from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait

from pages.base_page import BasePage
from pages.locators import HOME_PAGE_LOCATORS

SCROLL_TO_EXPERIENCE_JS = (
    "window.scrollTo(0, arguments[0].getBoundingClientRect().top "
    "+ window.scrollY - 80);"
)


class HomePage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.header_locator = HOME_PAGE_LOCATORS["header"]
        self.title_locator = HOME_PAGE_LOCATORS["title"]
        self.icon_wrapper_locator = HOME_PAGE_LOCATORS["icon_wrapper"]
        self.profile_image_locator = HOME_PAGE_LOCATORS["profile_image"]
        self.icon_links_locator = HOME_PAGE_LOCATORS["icon_links"]
        self.left_column_link_container_locator = HOME_PAGE_LOCATORS[
            "left_column_link_container"
        ]
        self.email_label_locator = HOME_PAGE_LOCATORS["email_label"]
        self.email_locator = HOME_PAGE_LOCATORS["email"]
        self.phone_label_locator = HOME_PAGE_LOCATORS["phone_label"]
        self.phone_locator = HOME_PAGE_LOCATORS["phone"]
        self.summary_locator = HOME_PAGE_LOCATORS["summary"]
        self.experience_container_locator = HOME_PAGE_LOCATORS["experience_container"]
        self.send_message_text_locator = HOME_PAGE_LOCATORS["send_message_text"]
        self.languages_label_locator = HOME_PAGE_LOCATORS["languages_label"]
        self.qa_help_label_locator = HOME_PAGE_LOCATORS["qa_help_label"]
        self.practice_page_link_locator = HOME_PAGE_LOCATORS["practice_page_link"]
        self.ctal_tae_exam_link_locator = HOME_PAGE_LOCATORS["ctal_tae_exam_link"]
        self.ctal_tm_exam_link_locator = HOME_PAGE_LOCATORS["ctal_tm_exam_link"]
        self.certificates_container_locator = HOME_PAGE_LOCATORS["certificates_container"]
        self.skill_labels_locator = HOME_PAGE_LOCATORS["skill_labels"]

    def wait_for_page_load(self):
        self.wait_for_element(self.header_locator)

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
        return link.get_attribute("href")

    def get_icon_src(self, link: WebElement):
        """Return the src attribute of the image within an icon link."""
        img = link.find_element(By.TAG_NAME, "img")
        return img.get_attribute("src")

    def get_profile_image(self):
        """Return the profile image element."""
        return self.wait_for_element(self.profile_image_locator)

    def get_left_container(self):
        return self.wait_for_elements(self.left_column_link_container_locator)

    def get_left_column_image(self, link_container: WebElement):
        """Return the image element within a left column link container."""
        return link_container.find_element(By.TAG_NAME, "img")

    def get_left_column_link(self, link_container: WebElement):
        """Return the anchor element within a left column link container."""
        return link_container.find_element(By.TAG_NAME, "a")

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
        container = self.wait_for_element(self.experience_container_locator)
        self.scroll_into_view(container)
        WebDriverWait(self.driver, 10).until(
            lambda _: len(container.text.strip()) > len("PROFESSIONAL EXPERIENCE")
        )
        return container

    def get_experience_company_names(self):
        """Collect company names while scrolling.

        Experience entries lazy-load in the section.
        """
        container = self.get_experience_container()
        company_names = set()

        self.driver.execute_script(SCROLL_TO_EXPERIENCE_JS, container)

        stale_rounds = 0
        for _ in range(50):
            prev_count = len(company_names)
            container = self.driver.find_element(*self.experience_container_locator)
            for link in container.find_elements(By.CSS_SELECTOR, "a[href]"):
                name = link.text.strip()
                if name and "," in name:
                    company_names.add(name)

            self.driver.execute_script(
                "arguments[0].scrollTop = arguments[0].scrollTop + 400;", container
            )
            self.driver.execute_script("window.scrollBy(0, 400);")

            if len(company_names) == prev_count:
                stale_rounds += 1
                if stale_rounds >= 3:
                    break
            else:
                stale_rounds = 0

        return company_names

    def get_send_message_text(self):
        return self.get_text(self.send_message_text_locator)

    def get_languages_label(self):
        return self.get_text(self.languages_label_locator)

    def get_languages_value(self):
        label = self.wait_for_element(self.languages_label_locator)
        parent_text = label.find_element(By.XPATH, "..").text
        return parent_text.split(":", 1)[1].strip()

    def get_qa_help_label(self):
        label = self.wait_for_element(self.qa_help_label_locator)
        self.scroll_into_view(label)
        return label.text

    def get_qa_help_link(self, locator):
        link = self.wait_for_element(locator)
        self.scroll_into_view(link)
        return link

    def get_practice_page_link(self):
        return self.get_qa_help_link(self.practice_page_link_locator)

    def get_ctal_tae_exam_link(self):
        return self.get_qa_help_link(self.ctal_tae_exam_link_locator)

    def get_ctal_tm_exam_link(self):
        return self.get_qa_help_link(self.ctal_tm_exam_link_locator)

    def get_certificates_container(self):
        container = self.wait_for_element(self.certificates_container_locator)
        self.scroll_into_view(container)
        return container

    def get_skill_labels(self):
        labels = self.wait_for_elements(self.skill_labels_locator)
        if labels:
            self.scroll_into_view(labels[0])
        return labels
