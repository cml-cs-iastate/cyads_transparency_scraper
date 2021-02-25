from django.db import models
from enum import Enum


class CollectionType(Enum):
    CYADS = "CyAds"
    GOOGLETREPORT = "GoogleTReport"


class AdType(Enum):
    YOUTUBE = "YouTube"
    EXTERNAL = "external"


# Copied from CyAdsProcess models. Avoids restructuring CyAdsProcessor to get rid of pubsub placement in urls file.
class AdFile(models.Model):
    id = models.AutoField(db_column="AdFile_ID", primary_key=True)
    ad_filepath = models.TextField(null=True)
    collection_type = models.CharField(max_length=64, choices=[(tag, tag.value) for tag in CollectionType])

    def __repr__(self):
        return (f'{self.__class__.__name__}('
                f' {self.id!r}, {self.ad_filepath!r},'
                f' {self.collection_type!r})')


class Category(models.Model):
    CATEGORY_NAME_TO_ID = {'Film & Animation': 1,
                           'Autos & Vehicles': 2,
                           'Music': 10,
                           'Pets & Animals': 15,
                           'Sports': 17,
                           'ShortMovies': 18,
                           'Travel & Events': 19,
                           'Gaming': 20,
                           'Videoblogging': 21,
                           'People & Blogs': 22,
                           'Comedy': 34,
                           'Entertainment': 24,
                           'News & Politics': 25,
                           'Howto & Style': 26,
                           'Education': 27,
                           'Science & Technology': 28,
                           'Nonprofits & Activism': 29,
                           'Movies': 30,
                           'Anime/Animation': 31,
                           'Action/Adventure': 32,
                           'Classics': 33,
                           'Documentary': 35,
                           'Drama': 36,
                           'Family': 37,
                           'Foreign': 38,
                           'Horror': 39,
                           'Sci-Fi/Fantasy': 40,
                           'Thriller': 41,
                           'Shorts': 42,
                           'Shows': 43,
                           'Trailers': 44}

    # cat_id = models.IntegerField()
    name = models.CharField(max_length=100)


class Channel(models.Model):
    channel_id = models.CharField(max_length=255, null=False, unique=True)
    name = models.CharField(max_length=255, default='')
    description = models.CharField(max_length=255, default='', null=False)


class Tag(models.Model):
    tag = models.CharField(max_length=128, null=False, unique=True)


class VideoMeta(models.Model):
    # A combination of (hostname, unique parts of url)
    base_identifier = models.CharField(max_length=255, null=False, unique=True)
    # PK for looking up where the video file is stored on our server
    AdFile_ID = models.ForeignKey(AdFile, null=False, on_delete=models.PROTECT)

    ad_type = models.CharField(max_length=64, choices=[(tag, tag.value) for tag in AdType], null=False)

    # Youtube specific
    title = models.TextField(null=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, null=True)
    channel = models.ForeignKey(Channel, on_delete=models.PROTECT, null=True)
    description = models.TextField(null=True)
    tags = models.ManyToManyField(Tag, through='YTTag')


class YTTag(models.Model):
    class Meta:
        unique_together = ('yt_id', 'tag')

    yt_id = models.ForeignKey(VideoMeta, null=False, on_delete=models.PROTECT)
    tag = models.ForeignKey(Tag, null=False, on_delete=models.PROTECT)


class CreativeInfo(models.Model):
    ad_id = models.CharField(max_length=32, null=False)
    advertiser_id = models.CharField(max_length=32, null=False)
    ad_url = models.CharField(null=True, max_length=128)
    embed_url = models.TextField(null=True)
    missing = models.BooleanField(null=True)
    missing_reason = models.CharField(null=True, max_length=64)
    checked = models.BooleanField(default=False, null=False)
    meta_extracted = models.BooleanField(default=False, null=False)
    meta_id = models.ForeignKey(VideoMeta, null=True, on_delete=models.PROTECT)

    class Meta:
        unique_together = ('ad_id', 'advertiser_id',)
