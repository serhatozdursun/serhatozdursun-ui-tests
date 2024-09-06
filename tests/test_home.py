import pytest_check as check
from pages.home_page import HomePage
from urllib.parse import urlparse


class TestHomePage:
    def test_home_page_header(self, driver, test_data):
        home_page = HomePage(driver)
        check.equal(home_page.get_header_text(), test_data['home_page']['header_text'],
                    f"Expected header text: {test_data['home_page']['header_text']}, but got {home_page.get_header_text()}")
        check.equal(home_page.get_header_tag(), test_data['home_page']['header_tag'],
                    f"Expected header tag: {test_data['home_page']['header_tag']}, but got {home_page.get_header_tag()}")

    def test_home_page_sub_header(self, driver, test_data):
        home_page = HomePage(driver)
        check.equal(home_page.get_sub_header_text(), test_data['home_page']['sub_header_text'],
                    f"Expected sub-header text: {test_data['home_page']['sub_header_text']}, but got {home_page.get_sub_header_text()}")
        check.equal(home_page.get_sub_header_tag(), test_data['home_page']['sub_header_tag'],
                    f"Expected sub-header tag: {test_data['home_page']['sub_header_tag']}, but got {home_page.get_sub_header_tag()}")

    def test_home_page_icons(self, driver, test_data):
        home_page = HomePage(driver)
        icon_links = home_page.get_icon_links()

        for i, link in enumerate(icon_links):
            actual_href = home_page.get_icon_href(link)
            actual_src = home_page.get_icon_src(link)

            # Extract only the path of the src (ignoring domain)
            actual_src_path = urlparse(actual_src).path

            # Use soft assertions to check each href and src
            check.equal(actual_href, test_data['home_page']['icons'][i]['href'],
                        f"Expected href {test_data['home_page']['icons'][i]['href']}, but got {actual_href}")
            check.equal(actual_src_path, test_data['home_page']['icons'][i]['src'],
                        f"Expected src {test_data['home_page']['icons'][i]['src']}, but got {actual_src_path}")