# pages/locators.py
from selenium.webdriver.common.by import By

HOME_PAGE_LOCATORS = {
    'header': (By.ID, 'name'),
    'title': (By.ID, 'title'),
    'icon_wrapper': (By.ID, 'iconWrapper'),
    'profile_image': (By.ID, 'profile_image'),
    'icon_links': (By.CLASS_NAME, 'iconLink'),
    'icon_image': (By.CLASS_NAME, 'iconImage'),
    'left_column_link_container': (By.CLASS_NAME, 'leftColumnLinkContainer'),
    'email_label': (By.ID, 'emailLabel'),
    'email': (By.ID, 'email'),
    'phone_label': (By.ID, 'phoneLabel'),
    'phone': (By.ID, 'phone'),
    'languages': (By.ID, 'languages'),
    'summary': (By.ID, 'summary'),
    'experience_container': (By.ID, 'experience_container')

}
