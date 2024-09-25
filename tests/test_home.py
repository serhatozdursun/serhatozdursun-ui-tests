import pytest
import pytest_check as check
from pages.home_page import HomePage
from urllib.parse import urlparse


@pytest.fixture
def home_page(driver):
    '''Fixture to initialize HomePage object.'''
    return HomePage(driver)


class TestHomePage:

    def verify_text(self, actual, expected, element_name):
        check.equal(
            actual,
            expected,
            f'Expected {element_name}: {expected}, but got {actual}'
        )

    def test_home_page_header(self, home_page, test_data):
        header_text = home_page.get_header_text()
        header_tag = home_page.get_header_tag()
        expected_header_text = test_data['home_page']['header_text']
        expected_header_tag = test_data['home_page']['header_tag']

        self.verify_text(header_text, expected_header_text, 'header text')
        self.verify_text(header_tag, expected_header_tag, 'header tag')

    def test_home_page_sub_header(self, home_page, test_data):
        sub_header_text = home_page.get_sub_header_text()
        sub_header_tag = home_page.get_sub_header_tag()
        expected_sub_header_text = test_data['home_page']['sub_header_text']
        expected_sub_header_tag = test_data['home_page']['sub_header_tag']

        self.verify_text(sub_header_text, expected_sub_header_text, 'sub-header text')
        self.verify_text(sub_header_tag, expected_sub_header_tag, 'sub-header tag')

    def test_home_page_icons(self, home_page, test_data):
        icon_links = home_page.get_icon_links()

        for i, link in enumerate(icon_links):
            actual_href = home_page.get_icon_href(link)
            icon_src = home_page.get_icon_src(link)
            actual_src_path = urlparse(icon_src).path

            expected_href = test_data['home_page']['icons'][i]['href']
            expected_src = test_data['home_page']['icons'][i]['src']

            self.verify_text(actual_href, expected_href, 'icon href')
            self.verify_text(actual_src_path, expected_src, 'icon src')

    def test_home_profile_image(self, home_page):
        profile_image = home_page.get_profile_image()
        assert profile_image.is_displayed(), 'Profile image is not visible on the home page'

    def test_left_column_link_container(self, home_page):
        left_column_links = home_page.get_left_container()

        for link in left_column_links:
            img = home_page.get_left_column_image(link)
            a = home_page.get_left_column_link(link)

            assert img.is_displayed(), 'Image is not displayed in left column container'
            assert a.is_enabled(), 'Link is not enabled in left column container'

    def test_email(self, home_page, test_data):
        email_label_text = test_data['home_page']['email']['label']
        email_value_text = test_data['home_page']['email']['value']

        email_label = home_page.get_email_label()
        email_value = home_page.get_email_text()

        self.verify_text(email_label, email_label_text, 'email label')
        self.verify_text(email_value, email_value_text, 'email value')

    def test_summary(self, home_page):
        summary = home_page.get_summary()
        assert summary.is_displayed(), 'Summary is not displayed in left column container'

    def test_send_message(self, home_page):
        send_message_text = home_page.get_send_message_text()
        assert send_message_text == 'Send a message', 'Send message title was not expected'