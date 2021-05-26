import json
import time

import requests
from lxml import etree
from lxml.etree import ParserError
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from ecua_utils.logger import Logger

logger = Logger.logger


class EcuageneraCurl:
    product_url_object_path = "https://www.ecuagenera.com/epages/ecuagenera.sf/en_US/?ObjectPath=/Shops/ecuagenera/Products/"
    product_url_object_id = "https://www.ecuagenera.com/epages/ecuagenera.sf/en_US/?ObjectID="
    flaresolverr_url = "http://localhost:8191/v1"
    last_response = None

    def __init__(self, username=None, password=None, headless=False):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def open_item_page(self, item_id: str) -> bool:
        payload = {
            "cmd": "request.get",
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleW...",
            "maxTimeout": 60000,
            # "headers": {
            #     "X-Test": "Testing 123..."
            # }
        }
        headers = {'content-type': 'application/json',
                   'Accept-Charset': 'UTF-8'}

        # try object path first
        payload["url"] = f"{self.product_url_object_path}{item_id}"
        r = requests.post(self.flaresolverr_url,
                          data=json.dumps(payload), headers=headers)
        if r.status_code == 200 and not "The page requested is not available." in r.text:
            self.last_response = r
            return True

        payload["url"] = f"{self.product_url_object_id}{item_id}"
        r = requests.post(self.flaresolverr_url,
                          data=json.dumps(payload), headers=headers)
        if r.status_code == 200 and not "The page requested is not available." in r.text:
            self.last_response = r
            return True

        logger.warning(
            f'item {item_id} is not available - Are you sure the ID is correct?')
        return False

    def is_item_available(self, item_id: str) -> bool:
        if not self.open_item_page(item_id):
            return False
        return "Out of stock" not in self.last_response.text

    def get_item_name(self, item_id: str) -> str:
        if not self.open_item_page(item_id):
            return "invalid item ID"
        try:
            parser = etree.HTMLParser()
            response_json = json.loads(self.last_response.content)
            html_dom = etree.HTML(
                response_json['solution']["response"], parser)
            name = html_dom.xpath("//*[@itemprop='name']/text()")
        except ParserError as e:
            logger.error(e)
        return name[0]
