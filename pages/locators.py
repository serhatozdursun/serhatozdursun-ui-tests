from selenium.webdriver.common.by import By

HOME_PAGE_LOCATORS = {
    "header": (By.ID, "name"),
    "title": (By.ID, "title"),
    "icon_wrapper": (By.ID, "iconWrapper"),
    "profile_image": (By.ID, "profile_image"),
    "icon_links": (By.CLASS_NAME, "iconLink"),
    "left_column_link_container": (By.CLASS_NAME, "leftColumnLinkContainer"),
    "email_label": (By.ID, "emailLabel"),
    "email": (By.ID, "email"),
    "phone_label": (By.ID, "phoneLabel"),
    "phone": (By.ID, "phone"),
    "summary": (By.ID, "summary"),
    "experience_container": (By.ID, "experience_container"),
    "send_message_text": (By.ID, "sendMessageText"),
    "languages_label": (By.ID, "languages"),
    "qa_help_label": (By.ID, "qaHelpLabel"),
    "practice_page_link": (By.ID, "practicePage"),
    "ctal_tae_exam_link": (By.ID, "CtalTaeExam"),
    "ctal_tm_exam_link": (By.ID, "CtalTmExam"),
    "certificates_container": (By.ID, "certificatesContainer"),
    "skill_labels": (By.CSS_SELECTOR, '[id^="skill-label-"]'),
}
