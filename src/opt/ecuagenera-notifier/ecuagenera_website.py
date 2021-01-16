import datetime
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait


class EcuageneraWebsite:
    url = "https://www.ecuagenera.com"
    product_url_object_path = "https://www.ecuagenera.com/epages/ecuagenera.sf/en_US/?ObjectPath=/Shops/ecuagenera/Products/"
    product_url_object_id = "https://www.ecuagenera.com/epages/ecuagenera.sf/en_US/?ObjectID="

    def __init__(self, headless=False):
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")  # for sudo linux usage
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.set_window_size(1600, 768)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # time.sleep(5)
        self.driver.close()

    def open_website(self):
        self.driver.get(self.url)
        assert "Ecuagenera" in self.driver.title

    def open_item_page(self, item_id: str) -> bool:
        # try object path first
        self.driver.get(f"{self.product_url_object_path}{item_id}")
        if len(self.driver.find_elements_by_class_name('ProductDetails')) > 0:
            return True

        self.driver.get(f"{self.product_url_object_id}{item_id}")
        if len(self.driver.find_elements_by_class_name('ProductDetails')) > 0:
            return True

        print(
            f'item {item_id} is not available - Are you sure the ID is correct?')
        return False

    def is_item_available(self, item_id: str) -> bool:
        if not self.open_item_page(item_id):
            return False
        elements: list[WebElement] = self.driver.find_elements_by_class_name(
            "ProductOnStockIcon")
        return len(elements) > 0

    def get_item_name(self, item_id: str) -> str:
        if not self.open_item_page(item_id):
            return "invalid item ID"
        return self.driver.find_element_by_xpath("//*[@itemprop='name']").text
