from django.shortcuts import render

# Create your views here.

from django.http import HttpResponse

from .bigquery import enrich_transparency_report

def index(request):
    return HttpResponse("Hello. You're at the scraper index.")


def update_transparency(request):
    task_enrich = enrich_transparency_report()
    task_enrich(blocking=False)
    return HttpResponse("beginning to update transparency report", status=201)


def endpoint_scrape_new_urls(request):
    return HttpResponse("beginning to scrape urls")


def test_double(request, num):
    return HttpResponse(f"{num} is awaiting doubling")
