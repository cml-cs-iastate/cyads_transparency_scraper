from django.db import models


class CreativeInfo(models.Model):
    ad_id = models.CharField(max_length=32, null=False)
    advertiser_id = models.CharField(max_length=32, null=False)
    ad_url = models.CharField(null=True, max_length=128)
    embed_url = models.TextField(null=True)
    missing = models.BooleanField(null=True)
    checked = models.BooleanField(default=False, null=False)

    class Meta:
        unique_together = ('ad_id', 'advertiser_id',)
