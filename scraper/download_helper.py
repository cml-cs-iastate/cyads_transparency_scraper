import youtube_dl
from youtube_dl.extractor import YoutubeIE
import logging
from typing import Optional, Tuple

from pathlib import PurePosixPath, Path
from urllib.parse import unquote, urlparse
import re
import urllib

logger = logging.getLogger(__name__)


class DuplicateVideoError(Exception):
    """A video is already downloaded by youtube-dl"""

    def __init__(self, message, url: str = None, path: Path = None):
        self.message = message
        self.url: str = url
        self.path: Path = path

    def __str__(self):
        return f"{self.message}: url={self.url}, path={self.path}"


class MissingVideoError(Exception):
    """A video is no longer available to download because it is taken down"""

    def __init__(self, message, url: str = None):
        self.message = message
        self.url: str = url

    def __str__(self):
        return f"{self.message}: url={self.url}"


class PrivateVideoError(Exception):
    """A video is no longer available to download because it is private"""

    def __init__(self, message, url: str = None):
        self.message = message
        self.url: str = url

    def __str__(self):
        return f"{self.message}: url={self.url}"


class UserRemovedVideoError(Exception):
    """A video is no longer available to download because it was removed by the user"""

    def __init__(self, message, url: str = None):
        self.message = message
        self.url: str = url

    def __str__(self):
        return f"{self.message}: url={self.url}"


class AccountTerminationVideoError(Exception):
    """A video is no longer available to download because the associated account was terminated"""

    def __init__(self, message, url: str = None):
        self.message = message
        self.url: str = url

    def __str__(self):
        return f"{self.message}: url={self.url}"


def video_download(url: str, download_dir: str) -> Path:
    """Download video from ad url"""

    class MyLogger:
        def __init__(self):
            self.ad_filepath: Optional[Path] = None

        def debug(self, msg):
            print(msg)
            new_download_match = re.search('Merging formats into \"(.*)\"$', msg)
            already_downloaded_match = re.search("\[download\] (.*) has already been downloaded and merged.*", msg)
            if new_download_match:
                final_path = new_download_match.group(1)

                # This log msg occurs after any status messages from youtube-dl
                # This field will not be updated again for a video download.
                self.ad_filepath = Path(final_path)
                return
            elif already_downloaded_match:
                filepath = already_downloaded_match.group(1)
                self.ad_filepath = Path(filepath)
                return

        def warning(self, msg):
            print(msg)

        def error(self, msg):
            print(msg)

        def info(self, msg):
            print(msg)

    def my_hook(d):
        pass

    mylogger = MyLogger()

    ydl_opts = {
        # Pick best audio and video format and combine them OR pick the file with the best combination
        # Need to capture filename of merged ffmpeg file
        # Best doesn't return the highest video, only the highest pair.
        # So 360p video may have the highest audio
        # 'format': 'best',
        # 'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo[ext=webm]+bestaudio[ext=webm]/best',
        'format': 'bestvideo+bestaudio/best',
        'nooverwrites': True,
        # 'continuedl': True,
        'progress_hooks': [my_hook],
        'logger': mylogger,
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        # Extract info about video to determine where to download the file to
        try:
            result = ydl.extract_info(url, download=False)
        except youtube_dl.utils.DownloadError as e:
            if "video is unavailable" in e.args[0]:
                raise MissingVideoError("Missing video", url=url) from e
            elif "video is private" in e.args[0]:
                raise PrivateVideoError("Private video", url=url) from e
            elif "removed by the user" in e.args[0]:
                raise UserRemovedVideoError("User removed video", url=url) from e
            elif "account associated with this video has been terminated" in e.args[0]:
                raise AccountTerminationVideoError("Missing video due to account termination", url=url) from e
            else:
                raise e
        extractor = result["extractor"]

        if extractor == "generic":
            filename = extract_base_identifier(url)
            ydl_opts["outtmpl"] = download_dir + f'/{filename}.%(ext)s'
        elif extractor == "youtube":
            ydl_opts["outtmpl"] = download_dir + f'/%(id)s.%(ext)s'
            print(extractor)

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    saved_ad_filepath = mylogger.ad_filepath
    if saved_ad_filepath == download_dir:
        raise ValueError(f"`No video path was saved? Was the video downloaded?`, for url={url}")
    else:
        return saved_ad_filepath


def _extract_parts(url: str) -> Tuple[str, ...]:
    parsed = urlparse(url)
    return PurePosixPath(unquote(parsed.path)).parts


def handle_cbsadsales_a_akamaihd(url: str) -> str:
    url_parts = _extract_parts(url)
    id_pt1 = url_parts[1]
    id_pt2 = url_parts[2]
    return f"{id_pt1}-{id_pt2}"


def handle_cdn_flashtalking(url: str):
    url_parts = _extract_parts(url)
    id_pt1 = url_parts[1]
    id_pt2 = url_parts[2]
    return f"{id_pt1}-{id_pt2}"


def handle_cdn_jivox(url: str):
    url_parts = _extract_parts(url)
    return '-'.join(url_parts[1:4])


def handle_ssl_cdn_turner(url: str) -> str:
    url_parts = _extract_parts(url)
    return '-'.join(url_parts[4:8])


def handle_cdn_video_abc(url: str) -> str:
    url_parts = _extract_parts(url)
    return url_parts[3]


def handle_cdn1_extremereach(url: str) -> str:
    url_parts = _extract_parts(url)
    return '-'.join(url_parts[2:6])


def handle_ad_wsodcdn(url: str) -> str:
    url_parts = _extract_parts(url)
    id_pt1 = url_parts[3]
    id_pt2 = url_parts[8]
    return f"{id_pt1}-{id_pt2}"


def handle_ads_pd_nbcuni(url: str) -> str:
    url_parts = _extract_parts(url)
    id_pt1 = url_parts[2]
    id_pt2 = url_parts[3]
    return f"{id_pt1}-{id_pt2}"


def handle_gcdn_2mdn(url: str) -> str:
    url_parts = _extract_parts(url)
    if url_parts[2] != "id" and url_parts[1] != "videoplayback":
        raise AssertionError(f"/videoplayback/id does not begin the url={url}")
    id_offset = url_parts.index("id")
    file_id = url_parts[id_offset + 1]
    file_ext = url_parts[-1]
    return f"{file_id}-{file_ext}"


def handle_innovid(url: str) -> str:
    url_parts = _extract_parts(url)
    id_pt1 = url_parts[-3]
    id_pt2 = url_parts[-2]
    id_pt3 = url_parts[-1]
    return f"{id_pt1}-{id_pt2}-{id_pt3}"


def handle_cdn01_basis(url: str) -> str:
    url_parts = _extract_parts(url)
    return '-'.join(url_parts[1:4])


def handle_i_r1_cdn(url: str) -> str:
    url_parts = _extract_parts(url)
    return '-'.join(url_parts[1:5])


def handle_nbcotsadops_akamaized(url: str) -> str:
    url_parts = _extract_parts(url)
    return url_parts[2]


def handle_olyhdliveextraads_amd_akamaized(url: str) -> str:
    url_parts = _extract_parts(url)
    return '-'.join(url_parts[1:5])


def handle_playtime_tubemogul(url: str) -> str:
    url_parts = _extract_parts(url)
    return url_parts[2]


def handle_redirector_gvt1(url: str) -> str:
    url_parts = _extract_parts(url)
    id_offset = url_parts.index("id")
    id_pt1 = url_parts[id_offset + 1]
    id_pt2 = url_parts[-1]
    return f"{id_pt1}-{id_pt2}"


def handle_s2_adform(url: str) -> str:
    url_parts = _extract_parts(url)
    id_pt1 = url_parts[-2]
    id_pt2 = url_parts[-1]
    return f"{id_pt1}-{id_pt2}"


def handle_secure_ds_serving_sys(url: str) -> str:
    url_parts = _extract_parts(url)
    site_num = url_parts[-3]
    assert "Site-" in site_num
    vid_type = url_parts[-2]
    assert "Type-" in vid_type
    filename = url_parts[-1]
    return f"{site_num}-{vid_type}-{filename}"


def handle_shunivision_a_akamaihd(url: str) -> str:
    url_parts = _extract_parts(url)
    return '-'.join(url_parts[1:])


def handle_v_adsrvr(url: str) -> str:
    url_parts = _extract_parts(url)
    return '-'.join(url_parts[1:])


def handle_washingtonpost(url: str) -> str:
    url_parts = _extract_parts(url)
    return unquote(url_parts[-1])


def handle_extended_youtube(url: str) -> str:
    return parse.parse_qs(urlparse(url).query)["v"][0]


handlers = {
    "ad.wsodcdn.com": handle_ad_wsodcdn,
    "ads-pd.nbcuni.com": handle_ads_pd_nbcuni,
    "amd-ssl.cdn.turner.com": handle_ssl_cdn_turner,
    "cbsadsales-a.akamaihd.net": handle_cbsadsales_a_akamaihd,
    "cdn.flashtalking.com": handle_cdn_flashtalking,
    "cdn.jivox.com": handle_cdn_jivox,
    "cdn1.extremereach.io": handle_cdn1_extremereach,
    "cdn.video.abc.com": handle_cdn_video_abc,
    "gcdn.2mdn.net": handle_gcdn_2mdn,
    "i.r1-cdn.net": handle_i_r1_cdn,
    "cdn01.basis.net": handle_cdn01_basis,
    "nbcotsadops.akamaized.net": handle_nbcotsadops_akamaized,
    "olyhdliveextraads-amd.akamaized.net": handle_olyhdliveextraads_amd_akamaized,
    "playtime.tubemogul.com": handle_playtime_tubemogul,
    "redirector.gvt1.com": handle_redirector_gvt1,
    "s-static.innovid.com": handle_innovid,
    "s2.adform.net": handle_s2_adform,
    "secure-ds.serving-sys.com": handle_secure_ds_serving_sys,
    "shunivision-a.akamaihd.net": handle_shunivision_a_akamaihd,
    "v.adsrvr.org": handle_v_adsrvr,
    "www.washingtonpost.com": handle_washingtonpost,
    "www.youtube.com": handle_extended_youtube,
}


def _unique_file_url(url: str, handlers: dict) -> str:
    netloc = urlparse(url).netloc
    filename = handlers[netloc](url)
    return f"{netloc}-{filename}"


def extract_base_identifier(url: str) -> str:
    netloc = urllib.parse.urlparse(url)["netloc"]
    if netloc == "www.youtube.com":
        return YoutubeIE.extract_id(url)
    else:
        return _unique_file_url(url, handlers)

