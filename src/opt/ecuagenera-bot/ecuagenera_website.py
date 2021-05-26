from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from ecua_utils.logger import Logger

logger = Logger.logger

class EcuageneraWebsite:
    url = "https://www.ecuagenera.com/epages/ecuagenera.sf/en_US/?ObjectPath=/Shops/ecuagenera&ViewAction=ViewMyAccount&LastViewAction=ViewMyAccount&HideNotice=1"
    product_url_object_path = "https://www.ecuagenera.com/epages/ecuagenera.sf/en_US/?ObjectPath=/Shops/ecuagenera/Products/"
    product_url_object_id = "https://www.ecuagenera.com/epages/ecuagenera.sf/en_US/?ObjectID="

    def __init__(self, username=None, password=None, headless=False):
        self.username = username
        self.password = password

        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")  # for sudo linux usage
        chrome_options.add_argument('--no-proxy-server')
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.set_window_size(1600, 768)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # time.sleep(5)
        self.driver.close()

    def open_website(self):
        self.driver.get(self.url)
        assert "Sign in" in self.driver.title

    def login(self):
        email_tf = self.driver.find_element_by_name('Login')
        email_tf.send_keys(self.username)
        pw_tf = self.driver.find_element_by_name('Password')
        pw_tf.send_keys(self.password)
        self.driver.find_element_by_name('Save').click()

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
        elements = self.driver.find_elements_by_class_name(
            "ProductOnStockIcon")
        return len(elements) > 0

    def add_to_basket(self, quantity=1):
        select = Select(self.driver.find_element_by_name('Quantity'))
        select.select_by_value(str(quantity))
        self.driver.find_element_by_name('AddToBasket').click()

    def get_item_name(self, item_id: str) -> str:
        if not self.open_item_page(item_id):
            return "invalid item ID"
        return self.driver.find_element_by_xpath("//*[@itemprop='name']").text

    def clear_basket(self):
        # click on basket
        if "Basket" not in self.driver.current_url:
            try:
                self.driver.find_element_by_class_name(
                    'basket-icon-link').click()
            except NoSuchElementException:
                print("Basket is already empty")
                return

        if "Your basket is empty" in self.driver.page_source:
            print("Basket is now empty")
            return
        else:
            self.driver.find_element_by_xpath(
                '//*[@id="BasketTable"]/tbody/tr[1]/td[6]/button').click()
            # clear until all are gone
            self.clear_basket()

    def checkout(self) -> bool:
        try:
            # click on basket
            self.driver.find_element_by_class_name('basket-icon-link').click()

            # click on check out
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(
                (By.XPATH, '//*[@id="CheckOutTop"]/button')))
            self.driver.find_element_by_xpath(
                '//*[@id="CheckOutTop"]/button').click()

            # click on Next (Address tab)
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(
                (By.XPATH, '//*[@id="BasketForm"]/div/button')))
            self.driver.find_element_by_xpath(
                '//*[@id="BasketForm"]/div/button').click()

            # click on Next (Delivery tab)
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(
                (By.XPATH, '//*[@id="BasketForm"]/div[2]/button')))
            self.driver.find_element_by_xpath(
                '//*[@id="BasketForm"]/div[2]/button').click()

            # click on Next (Payment Type tab)
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(
                (By.XPATH, '//*[@id="BasketForm"]/div[2]/button')))
            self.driver.find_element_by_xpath(
                '//*[@id="BasketForm"]/div[2]/button').click()

            # click on T&C button and final order (Check & Order tab)
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(
                (By.ID, 'AcceptTAC')))
            self.driver.find_element_by_id('AcceptTAC').click()
            self.driver.find_element_by_xpath(
                '//*[@id="BasketForm"]/div[4]/div[1]/button').click()

            print('Successfully checked out!')
            return True
        except Exception as e:
            print(e)
            return False
