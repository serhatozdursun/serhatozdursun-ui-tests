from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from pages.base_page import BasePage
from pages.locators import HOME_PAGE_LOCATORS

SCROLL_TO_EXPERIENCE_JS = (
    "window.scrollTo(0, arguments[0].getBoundingClientRect().top "
    "+ window.scrollY - 80);"
)

EXPAND_SIDEBAR_XPATH = (
    "//button[contains(., 'Expand profile sidebar') "
    "or contains(@aria-label, 'Expand profile sidebar')]"
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
        self.certificates_container_locator = HOME_PAGE_LOCATORS[
            "certificates_container"
        ]
        self.skill_labels_locator = HOME_PAGE_LOCATORS["skill_labels"]

    def wait_for_page_load(self):
        self.wait_for_element(self.header_locator)

    def _left_sidebar_content_visible(self) -> bool:
        try:
            qa_help = self.driver.find_element(*self.qa_help_label_locator)
            if qa_help.is_displayed():
                return True
        except NoSuchElementException:
            pass
        try:
            certificates = self.driver.find_element(
                *self.certificates_container_locator
            )
            return certificates.is_displayed()
        except NoSuchElementException:
            return False

    def ensure_left_sidebar_expanded(self):
        """Expand the profile sidebar only when QA help / certificates are hidden."""
        if self._left_sidebar_content_visible():
            return

        for button in self.driver.find_elements(By.XPATH, EXPAND_SIDEBAR_XPATH):
            if button.is_displayed() and button.is_enabled():
                button.click()
                WebDriverWait(self.driver, 5).until(
                    lambda _: self._left_sidebar_content_visible()
                )
                break

        try:
            left_column = self.driver.find_element(By.ID, "mobile-left-column-content")
            self.driver.execute_script(
                "arguments[0].scrollTop = arguments[0].scrollHeight;", left_column
            )
        except NoSuchElementException:
            pass

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
        for _ in range(80):
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
                if stale_rounds >= 6:
                    break
            else:
                stale_rounds = 0

        container = self.driver.find_element(*self.experience_container_locator)
        self.driver.execute_script(
            "arguments[0].scrollTop = arguments[0].scrollHeight;", container
        )
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        for link in container.find_elements(By.CSS_SELECTOR, "a[href]"):
            name = link.text.strip()
            if name and "," in name:
                company_names.add(name)

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
        self.ensure_left_sidebar_expanded()
        label = self.wait_for_element(self.qa_help_label_locator)
        self.scroll_into_view(label)
        return label.text

    def get_qa_help_link(self, locator):
        self.ensure_left_sidebar_expanded()
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
        self.ensure_left_sidebar_expanded()
        container = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located(self.certificates_container_locator)
        )
        self.scroll_into_view(container)
        return container

    def _element_text(self, element) -> str:
        text = element.text.strip()
        if text:
            return text
        return self.driver.execute_script(
            "return arguments[0].innerText || '';", element
        ).strip()

    def get_certificates_text(self):
        container = self.get_certificates_container()
        return self._element_text(container)

    def get_skill_labels(self):
        self.ensure_left_sidebar_expanded()
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_all_elements_located(self.skill_labels_locator)
        )
        labels = self.driver.find_elements(*self.skill_labels_locator)
        if labels:
            self.scroll_into_view(labels[0])
            try:
                left_column = self.driver.find_element(
                    By.ID, "mobile-left-column-content"
                )
                self.driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollHeight;", left_column
                )
            except NoSuchElementException:
                pass

        def _labels_have_text(_driver) -> bool:
            return any(
                self._element_text(el)
                for el in _driver.find_elements(*self.skill_labels_locator)
            )

        WebDriverWait(self.driver, 15).until(_labels_have_text)
        return self.driver.find_elements(*self.skill_labels_locator)

    def get_skill_label_texts(self) -> list[str]:
        return [self._element_text(label) for label in self.get_skill_labels()]
