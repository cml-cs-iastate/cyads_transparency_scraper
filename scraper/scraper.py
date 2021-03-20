from typing import Union

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from enum import Enum


class CreativeMissingReason(Enum):
    AD_PREVIEW_UNAVAILABLE = "AD_PREVIEW_UNAVAILABLE"
    AD_POLICY_VIOLATION = "AD_POLICY_VIOLATION"
    UNKNOWN_CREATIVE = "UNKNOWN_CREATIVE"


class AdUrlMissing(Exception):
    pass


class UnknownMissingReason(Exception):
    pass


class ScrapeResult:
    def __init__(self, actual_url: Union[str, None] = None, missing_reason: CreativeMissingReason = None):
        self.actual_url = actual_url
        self.missing = missing_reason is not None
        self.missing_reason = missing_reason

        if not actual_url and not self.missing:
            raise ValueError("actual_url must be non-empty if missing is false")


class Scraper:
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver

    def scrape_url(self, url) -> ScrapeResult:
        self.driver.get(url)
        try:
            ad_url = self._locate_ad_url()
            return ScrapeResult(actual_url=ad_url)
        except AdUrlMissing:
            return ScrapeResult(missing_reason=self._determine_missing_reason())

    def _determine_missing_reason(self) -> CreativeMissingReason:
        try:
            no_render_ad = self.driver.find_element_by_class_name("no-renderable-ad")
            if "Ad preview unavailable" in no_render_ad.text:
                return CreativeMissingReason.AD_PREVIEW_UNAVAILABLE
            elif "This ad violated Google's Advertising Policies" in no_render_ad.text:
                return CreativeMissingReason.AD_POLICY_VIOLATION
        except NoSuchElementException:
            report = self.driver.find_element_by_tag_name("report-section")
            if "There was a problem loading the content you requested" in report.text:
                return CreativeMissingReason.UNKNOWN_CREATIVE
        raise UnknownMissingReason()

    def _locate_ad_url(self) -> str:
        # wait for creative embed to load
        wait = WebDriverWait(self.driver, 10)
        try:
            visualization = wait.until(ec.presence_of_element_located((By.CLASS_NAME, "visualization")))
        except TimeoutException:
            raise AdUrlMissing()

        # Standard YouTube embed
        try:
            try:
                embed_container = visualization.find_element_by_class_name("container")
                embed_iframe = embed_container.find_element_by_tag_name("iframe")
                ad_url = embed_iframe.get_attribute("src")
                return ad_url
            except NoSuchElementException as e:
                # external ad
                external_ad = visualization.find_element_by_tag_name("video")
                ad_url = external_ad.get_attribute("src")
                return ad_url
        except NoSuchElementException as e:
            raise AdUrlMissing()
