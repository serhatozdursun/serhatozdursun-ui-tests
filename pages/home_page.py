from selenium.webdriver.common.by import By
from pages.base_page import BasePage

class HomePage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.header_locator = (By.ID, 'name')
        self.title_locator = (By.ID, 'title')
        self.icon_wrapper_locator = (By.ID, 'iconWrapper')
        self.icon_links_locator = (By.TAG_NAME, 'a')

    def get_header_text(self):
        return self.get_text(self.header_locator)

    def get_header_tag(self):
        return self.get_tag(self.header_locator)

    def get_sub_header_text(self):
        return self.get_text(self.title_locator)

    def get_sub_header_tag(self):
        return self.get_tag(self.title_locator)

    def get_icon_wrapper(self):
        return self.wait_for_element(self.icon_wrapper_locator)

    def get_icon_links(self):
        """Returns all the anchor elements within the iconWrapper div."""
        wrapper = self.get_icon_wrapper()
        # Unpack self.icon_links_locator
        return wrapper.find_elements(*self.icon_links_locator)

    def get_icon_href(self, link):
        """Returns the href attribute of the anchor tag."""
        return link.get_attribute('href')

    def get_icon_src(self, link):
        """Returns the src attribute of the image tag within the anchor."""
        img = link.find_element(By.TAG_NAME, 'img')
        return img.get_attribute('src')