from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from enum import Enum


class CreativeMissingReason(Enum):
    AD_PREVIEW_UNAVAILABLE = "AD_PREVIEW_UNAVAILABLE"


class AdUrlMissing(Exception):
    pass


class UnknownMissingReason(Exception):
    pass


class Scraper:
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver

    def scrape_url(self, url) -> str:
        self.driver.get(url)
        try:
            ad_url = self.locate_ad_url()
            return ad_url
        except AdUrlMissing:
            raise self.missing_reason_known()

    def missing_reason_known(self) -> CreativeMissingReason:
        if "Ad preview unavailable" in self.driver.find_element_by_class_name("no-renderable-ad").text:
            return CreativeMissingReason.AD_PREVIEW_UNAVAILABLE
        else:
            raise UnknownMissingReason()

    def locate_ad_url(self) -> str:
        # wait for creative embed to load
        wait = WebDriverWait(self.driver, 10)
        viz = wait.until(ec.presence_of_element_located((By.CLASS_NAME, "visualization")))

        # Standard YouTube embed
        try:
            try:
                embed_container = viz.find_element_by_class_name("container")
                embed_iframe = embed_container.find_element_by_tag_name("iframe")
                ad_url = embed_iframe.get_attribute("src")
                return ad_url
            except NoSuchElementException as e:

                external_ad = viz.find_element_by_tag_name("video")
                ad_url = external_ad.get_attribute("src")
                return ad_url
        except NoSuchElementException as e:
            raise AdUrlMissing()
