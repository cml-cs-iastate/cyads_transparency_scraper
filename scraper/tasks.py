from celery import shared_task, app
from time import sleep
from .scraper import Scraper, CreativeMissingReason, UnknownMissingReason
from selenium import webdriver
from .models import CreativeInfo

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
    chrome.get("https://transparencyreport.google.com/political-ads/advertiser/AR458000056721604608/creative/CR500897228001378304")
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
            embed_ad_url = scraper.scrape_url(creative.ad_url)
            assert embed_ad_url
            creative.embed_url = embed_ad_url
            creative.checked = True
            creative.missing = False
            creative.save()
        except CreativeMissingReason as reason:
            print(f"MISSING: reason: {reason.name}, ad_url={creative.ad_url}")
            creative.missing_reason = reason.value
            creative.missing = True
            creative.checked = True
            creative.save()
        except UnknownMissingReason as e:
            raise e

        print(f"{creative.ad_url=}, {creative.embed_url=}")
