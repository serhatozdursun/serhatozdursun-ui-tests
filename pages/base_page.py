from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class BasePage:
    def __init__(self, driver):
        self.driver = driver

    def wait_for_element(self, locator, timeout=10):
        return WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located(locator))

    def wait_for_elements(self, locator, timeout=10):
        return WebDriverWait(self.driver, timeout).until(EC.visibility_of_all_elements_located(locator))

    def wait_for_elements_to_be_clickable(self, locator, timeout=10):
        return WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable(locator))

    def click(self, locator):
        self.wait_for_elements_to_be_clickable(locator).click()

    def enter_text(self, locator, text):
        self.wait_for_element(locator).send_keys(text)

    def get_text(self, locator):
        return self.wait_for_element(locator).text

    def get_tag(self, locator):
        return self.wait_for_element(locator).tag_name
