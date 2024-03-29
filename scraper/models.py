from django.db import models
from enum import Enum


class CollectionType(Enum):
    CYADS = "CyAds"
    GOOGLETREPORT = "GoogleTReport"


class AdType(Enum):
    YOUTUBE = "youtube"
    EXTERNAL = "external"


# Copied from CyAdsProcess models. Avoids restructuring CyAdsProcessor to get rid of pubsub placement in urls file.
class AdFile(models.Model):
    id = models.AutoField(db_column="AdFile_ID", primary_key=True)
    ad_filepath = models.TextField(null=False, unique=True)

    def __repr__(self):
        return (f'{self.__class__.__name__}('
                f' {self.id!r}, {self.ad_filepath!r},'
                )


class CreativeInfo(models.Model):
    ad_id = models.CharField(max_length=32, null=False)
    advertiser_id = models.CharField(max_length=32, null=False)
    transparency_url = models.CharField(null=False, max_length=128)
    first_served_timestamp: models.DateTimeField(null=False)
    direct_ad_url = models.TextField(null=True)
    scraped = models.BooleanField(null=False, default=False)
    was_available = models.BooleanField(null=True)
    regions = models.CharField(null=False, max_length=128)
    unable_to_scrape_reason=models.CharField(null=True, max_length=64)
    processed = models.BooleanField(default=False, null=False)
    AdFile_ID = models.ForeignKey(AdFile, db_column='AdFile_ID_id', null=True, on_delete=models.PROTECT)

    class Meta:
        unique_together = ('ad_id', 'advertiser_id',)
