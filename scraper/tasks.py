import os

from celery import shared_task, app
from django.db import transaction
from .download_helper import extract_base_identifier, video_download

from time import sleep
from .scraper import Scraper, CreativeMissingReason, UnknownMissingReason, ScrapeResult
from selenium import webdriver
from .old_models import CreativeInfo, VideoMeta, AdType, AdFile, CollectionType, Channel, Category, Tag
from selenium.common.exceptions import TimeoutException
import youtube_dl


@shared_task
def hello():
    print("Hello there!")
    return "done 1"


@shared_task
def test_double(num: int) -> int:
    sleep(1)
    result = num * 2
    print(result)
    return result


@shared_task(bind=True)
def test_progress(self, num: int, times: int):
    result = 1
    for i in range(times):
        result *= num
        self.update_state(state="PROGRESS", meta={'iteration': i, 'inter_result': result})
        with self.app.events.default_dispatcher() as dispatcher:
            dispatcher.send('test-progress-event', event="PROGRESS", iteration=i, inter_result=result)
            print("in dispatch")
        sleep(2)
    return result


@shared_task
def test_exception(number):
    raise Exception(f"exc number={number}")


@shared_task
def test_chrome_spawn():
    options = webdriver.ChromeOptions()
    options.add_argument("--remote-debugging-port=4444")
    chrome = webdriver.Chrome(options=options)
    chrome.get(
        "https://transparencyreport.google.com/political-ads/advertiser/AR458000056721604608/creative/CR500897228001378304")
    sleep(120)
    chrome.quit()


@shared_task
def scrape_new_urls():
    chrome = webdriver.Chrome()
    scraper = Scraper(driver=chrome)
    creative: CreativeInfo
    for creative in CreativeInfo.objects.filter(checked=False):
        print(f"scraping: {creative=}, {creative.ad_url=}")
        try:
            embed_ad_url_result: ScrapeResult = scraper.scrape_url(creative.ad_url)
            if not embed_ad_url_result.missing:
                assert embed_ad_url_result.actual_url
                creative.embed_url = embed_ad_url_result.actual_url
                creative.checked = True
                creative.missing = False
                creative.save()
            else:
                assert embed_ad_url_result.missing
                assert isinstance(embed_ad_url_result.missing_reason, CreativeMissingReason)
                reason = embed_ad_url_result.missing_reason
                print(f"MISSING: reason: {reason.name}, ad_url={creative.ad_url}")
                creative.missing_reason = reason.value
                creative.missing = True
                creative.checked = True
                creative.save()
        except UnknownMissingReason as e:
            # for dev: pass for speed!
            continue
            raise e

        print(f"{creative.ad_url=}, {creative.embed_url=}")


@shared_task
def download_creatives():
    for creativeinfo in CreativeInfo.objects.filter(missing=False):
        with transaction.atomic():
            url_for_ad_location = creativeinfo.embed_url
            base_identifier: str = extract_base_identifier(url_for_ad_location)

            # check if it already has been downloaded
            try:
                video_meta_already = VideoMeta.objects.get(base_identifer=base_identifier)
                # skip downloading and getting info
                creativeinfo.meta_id = video_meta_already
                creativeinfo.meta_extracted = True
                creativeinfo.save()
                continue
            except VideoMeta.DoesNotExist:
                download_dir: str = os.environ["AD_ARCHIVE_ROOT_DIR"]
                ad_filepath = video_download(url_for_ad_location, download_dir=download_dir)
                ad_file = AdFile(ad_filepath=ad_filepath, collection_type=collection_type)
                ad_file.save()

                result: dict = youtube_dl.YoutubeDL().extract_info(download=False)
                collection_type = CollectionType.GOOGLETREPORT.value

                extractor = result["extractor"]
                if extractor == "youtube":
                    ad_type = AdType.YOUTUBE.value
                else:
                    ad_type = AdType.EXTERNAL.value
                video_meta = VideoMeta(base_identifer=base_identifier,
                                       ad_type=ad_type,
                                       AdFile_ID=ad_file)

                if extractor == "youtube":
                    title = result["title"]
                    video_meta.title = title

                    channel_id = result["uploader_id"]
                    channel_name = result["uploader_name"]
                    channel, created = Channel.objects.get_or_create(channel_id=channel_id)
                    if not created:
                        channel.name = channel_name
                        channel.save()
                    video_meta.channel = channel

                    category_ytdl = result["categories"]
                    category, created = Category.objects.get_or_create(name=category_ytdl)
                    video_meta.category = category

                    tags = result["tags"]
                    for tag in tags:
                        db_tag, created = Tag.objects.get_or_create(tag=tag)
                        video_meta.tags.add(db_tag)

                    description = result["description"]
                    video_meta.description = description
                video_meta.save()

                creativeinfo.meta_id = video_meta
                creativeinfo.meta_extracted = True
                creativeinfo.save()

