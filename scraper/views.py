from django.shortcuts import render

# Create your views here.

from django.http import HttpResponse
from .tasks import test_double as celery_test_double
from .tasks import test_progress as celery_test_progress
from .tasks import test_exception
from .tasks import test_chrome_spawn, scrape_new_urls

from google.cloud import bigquery
from .old_models import CreativeInfo


def index(request):
    return HttpResponse("Hello, world. You're at the scraper index.")


def endpoint_scrape_new_urls(request):
    scrape_new_urls.delay()
    return HttpResponse("beginning to scrape urls")


def pull_bigquery_latest_creatives(request):
    client = bigquery.Client()
    sample_query = """SELECT ad_id, ad_url, advertiser_id FROM `cyads-203819.google_political_ads_with_actual_url`.creative_stats WHERE regions = "US" AND ad_type="Video" AND date_range_end > DATE("2000-02-04");"""
    query_job = client.query(sample_query)
    results = query_job.result()
    for index, row in enumerate(results):
        ad_id = row["ad_id"]
        ad_url = row["ad_url"]
        advertiser_id = row["advertiser_id"]
        creative_info, created = CreativeInfo.objects.get_or_create(ad_id=ad_id, advertiser_id=advertiser_id, ad_url=ad_url)
        creative_info: CreativeInfo
        creative_info.save()
        print(f'num={index}, {ad_id=}, {ad_url=}')
    print("DONE:", index)
    return HttpResponse("testing in progress")



def test_double(request, num):
    celery_test_double.delay(num=num)
    celery_test_progress.delay(num=num, times=10)
    return HttpResponse(f"{num} is awaiting doubling")


def test_celery_exception(request):
    test_exception.delay(123)
    return HttpResponse("Exception raised test")

def trigger_error(request):
    division_by_zero = 1 / 0


def test_chrome_spawn_url(request):
    test_chrome_spawn.delay()
    return HttpResponse("Spawned chrome instance on port 4444")
