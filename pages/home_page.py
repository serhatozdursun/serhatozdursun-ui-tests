from selenium.webdriver.remote.webelement import WebElement

from pages.locators import HOME_PAGE_LOCATORS
from selenium.webdriver.common.by import By
from pages.base_page import BasePage


class HomePage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.header_locator = HOME_PAGE_LOCATORS['header']
        self.title_locator = HOME_PAGE_LOCATORS['title']
        self.icon_wrapper_locator = HOME_PAGE_LOCATORS['icon_wrapper']
        self.profile_image_locator = HOME_PAGE_LOCATORS['profile_image']
        self.icon_links_locator = HOME_PAGE_LOCATORS['icon_links']
        self.icon_image_locator = HOME_PAGE_LOCATORS['icon_image']
        self.left_column_link_container_locator = HOME_PAGE_LOCATORS['left_column_link_container']
        self.email_label_locator = HOME_PAGE_LOCATORS['email_label']
        self.email_locator = HOME_PAGE_LOCATORS['email']
        self.phone_label_locator = HOME_PAGE_LOCATORS['phone_label']
        self.phone_locator = HOME_PAGE_LOCATORS['phone']
        self.languages_locator = HOME_PAGE_LOCATORS['languages']
        self.summary_locator = HOME_PAGE_LOCATORS['summary']
        self.experience_container_locator = HOME_PAGE_LOCATORS['experience_container']
        self.sendMessageText = HOME_PAGE_LOCATORS['sendMessageText']

    def get_header_text(self):
        """Return the header text."""
        return self.get_text(self.header_locator)

    def get_header_tag(self):
        """Return the tag of the header."""
        return self.get_tag(self.header_locator)

    def get_sub_header_text(self):
        """Return the sub-header text."""
        return self.get_text(self.title_locator)

    def get_sub_header_tag(self):
        """Return the tag of the sub-header."""
        return self.get_tag(self.title_locator)

    def get_icon_wrapper(self):
        """Return the icon wrapper element."""
        return self.wait_for_element(self.icon_wrapper_locator)

    def get_icon_links(self):
        """Return all icon link elements within the icon wrapper."""
        return self.get_icon_wrapper().find_elements(*self.icon_links_locator)

    def get_icon_href(self, link: WebElement):
        """Return the href attribute of an icon link."""
        return link.get_attribute('href')

    def get_icon_src(self, link: WebElement):
        """Return the src attribute of the image within an icon link."""
        img = link.find_element(By.TAG_NAME, 'img')
        return img.get_attribute('src')

    def get_profile_image(self):
        """Return the profile image element."""
        return self.wait_for_element(self.profile_image_locator)

    def get_left_container(self):
        return self.wait_for_elements(self.left_column_link_container_locator)

    def get_left_column_links(self):
        """Return all link container elements in the left column."""
        return self.wait_for_elements(self.left_column_link_container_locator)

    def get_left_column_image(self, link_container: WebElement):
        """Return the image element within a left column link container."""
        return link_container.find_element(By.TAG_NAME, 'img')

    def get_left_column_link(self,  link_container: WebElement):
        """Return the anchor element within a left column link container."""
        return link_container.find_element(By.TAG_NAME, 'a')

    def get_email_label(self):
        """Return the email label text."""
        return self.get_text(self.email_label_locator)

    def get_email_text(self):
        """Return the email text."""
        return self.get_text(self.email_locator)

    def get_phone_label(self):
        """Return the phone label text."""
        return self.get_text(self.phone_label_locator)

    def get_phone_text(self):
        """Return the phone text."""
        return self.get_text(self.phone_locator)

    def get_summary(self):
        return self.wait_for_element(self.summary_locator)

    def get_experience_container(self):
        return self.wait_for_element(self.experience_container_locator)

    def get_send_message_text(self):
        return self.get_text(self.sendMessageText)