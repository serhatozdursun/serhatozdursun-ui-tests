from urllib.parse import unquote, urlparse

import pytest_check as check


class TestHomePage:
    def verify_text(self, actual, expected, element_name):
        check.equal(
            actual, expected, f"Expected {element_name}: {expected}, but got {actual}"
        )

    def test_home_page_header(self, home_page, test_data):
        header_text = home_page.get_header_text()
        header_tag = home_page.get_header_tag()
        expected_header_text = test_data["home_page"]["header_text"]
        expected_header_tag = test_data["home_page"]["header_tag"]

        self.verify_text(header_text, expected_header_text, "header text")
        self.verify_text(header_tag, expected_header_tag, "header tag")

    def test_home_page_sub_header(self, home_page, test_data):
        sub_header_text = home_page.get_sub_header_text()
        sub_header_tag = home_page.get_sub_header_tag()
        expected_sub_header_text = test_data["home_page"]["sub_header_text"]
        expected_sub_header_tag = test_data["home_page"]["sub_header_tag"]

        self.verify_text(sub_header_text, expected_sub_header_text, "sub-header text")
        self.verify_text(sub_header_tag, expected_sub_header_tag, "sub-header tag")

    def test_home_page_icons(self, home_page, test_data):
        """
        Verifies that each home page icon's href and src match the expected values.

        - Asserts total number of icons matches the expected data.
        - Validates href and src for each icon individually.
        """
        icon_links = home_page.get_icon_links()
        expected_icons = test_data["home_page"]["icons"]

        actual_count = len(icon_links)
        expected_count = len(expected_icons)

        # Step 1: Assert the number of icons matches
        assert actual_count == expected_count, (
            f"Mismatch in icon count: found {actual_count} icons on the page, "
            f"but {expected_count} were expected."
        )

        expected_by_href = {icon["href"]: icon for icon in expected_icons}
        actual_hrefs = {home_page.get_icon_href(link) for link in icon_links}
        expected_hrefs = set(expected_by_href)

        assert actual_hrefs == expected_hrefs, (
            f"Icon href mismatch: missing {expected_hrefs - actual_hrefs}, "
            f"unexpected {actual_hrefs - expected_hrefs}"
        )

        for link in icon_links:
            actual_href = home_page.get_icon_href(link)
            expected = expected_by_href[actual_href]
            icon_src = home_page.get_icon_src(link)
            actual_src_path = urlparse(icon_src).path
            decoded_src = unquote(icon_src)
            filename = expected["src"].lstrip("/")

            self.verify_text(
                actual_href, expected["href"], f"icon href ({actual_href})"
            )
            check.is_true(
                filename in decoded_src or actual_src_path == expected["src"],
                f"icon src ({actual_href}): expected {filename} in {icon_src}",
            )

    def test_home_profile_image(self, home_page):
        profile_image = home_page.get_profile_image()
        check.is_true(
            profile_image.is_displayed(),
            "Profile image is not visible on the home page",
        )

    def test_left_column_link_container(self, home_page):
        left_column_links = home_page.get_left_container()

        for link in left_column_links:
            img = home_page.get_left_column_image(link)
            a = home_page.get_left_column_link(link)

            assert img.is_displayed(), "Image is not displayed in left column container"
            assert a.is_enabled(), "Link is not enabled in left column container"

    def test_email(self, home_page, test_data):
        email_label_text = test_data["home_page"]["email"]["label"]
        email_value_text = test_data["home_page"]["email"]["value"]

        email_label = home_page.get_email_label()
        email_value = home_page.get_email_text()

        self.verify_text(email_label, email_label_text, "email label")
        self.verify_text(email_value, email_value_text, "email value")

    def test_phone(self, home_page, test_data):
        phone_label_text = test_data["home_page"]["phone"]["label"]
        phone_value_text = test_data["home_page"]["phone"]["value"]

        phone_label = home_page.get_phone_label()
        phone_value = home_page.get_phone_text()

        self.verify_text(phone_label, phone_label_text, "phone label")
        self.verify_text(phone_value, phone_value_text, "phone value")

    def test_experience_section_title(self, home_page, test_data):
        expected_title = test_data["home_page"]["experience_section_title"]
        experience_container_text = home_page.get_experience_container().text
        check.is_true(
            expected_title in experience_container_text.upper(),
            "Professional experience section title is not visible",
        )

    def test_experience_companies(self, home_page, test_data):
        company_names = home_page.get_experience_company_names()
        for company in test_data["home_page"]["experience_companies"]:
            assert company in company_names, f"Expected company not found: {company}"

    def test_summary(self, home_page):
        summary = home_page.get_summary()
        check.is_true(
            summary.is_displayed(),
            "Summary is not displayed in left column container",
        )

    def test_send_message(self, home_page, test_data):
        expected_text = test_data["home_page"]["send_message_text"]
        send_message_text = home_page.get_send_message_text()
        self.verify_text(send_message_text, expected_text, "send message text")

    def test_languages(self, home_page, test_data):
        expected = test_data["home_page"]["languages"]
        self.verify_text(
            home_page.get_languages_label(), expected["label"], "languages label"
        )
        self.verify_text(
            home_page.get_languages_value(), expected["value"], "languages value"
        )

    def test_qa_help_section(self, home_page, test_data):
        qa_help = test_data["home_page"]["qa_help"]
        self.verify_text(
            home_page.get_qa_help_label(), qa_help["label"], "QA help label"
        )

        link_getters = {
            "https://www.serhatozdursun.com/practice": home_page.get_practice_page_link,
            "https://www.serhatozdursun.com/ctal-tae-exam": home_page.get_ctal_tae_exam_link,
            "https://www.serhatozdursun.com/ctal-tm-exam": home_page.get_ctal_tm_exam_link,
        }
        for expected_link in qa_help["links"]:
            link = link_getters[expected_link["href"]]()
            self.verify_text(link.text, expected_link["text"], "QA help link text")
            self.verify_text(link.get_attribute("href"), expected_link["href"], "QA help link href")
            check.is_true(link.is_displayed(), f"QA help link not visible: {expected_link['text']}")

    def test_certificates_section(self, home_page, test_data):
        container = home_page.get_certificates_container()
        check.is_true(
            container.is_displayed(),
            "Certificates section is not visible on the home page",
        )
        container_text = container.text
        for entry in test_data["home_page"]["certificates"]["entries"]:
            check.is_true(
                entry in container_text,
                f"Expected certificate entry not found: {entry}",
            )

    def test_skills_labels(self, home_page, test_data):
        skills = test_data["home_page"]["skills"]
        labels = home_page.get_skill_labels()
        check.equal(
            len(labels),
            skills["count"],
            f"Expected {skills['count']} skill labels, found {len(labels)}",
        )
        label_texts = [label.text.strip() for label in labels]
        for expected_label in skills["sample_labels"]:
            check.is_true(
                expected_label in label_texts,
                f"Expected skill label not found: {expected_label}",
            )
