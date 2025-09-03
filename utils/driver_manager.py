from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
import os, shutil

class DriverManager:
    def __init__(self, base_url):
        self.driver = None
        self.base_url = base_url

    def initialize_driver(self, browser: str):
        if browser == "chrome":
            opts = webdriver.ChromeOptions()
            opts.add_argument("--headless=new")
            opts.add_argument("--disable-gpu")
            opts.add_argument("--no-sandbox")
            opts.add_argument("--window-size=1920,1080")

            # Always use webdriver_manager for Chrome (avoid stale PATH chromedriver)
            from webdriver_manager.chrome import ChromeDriverManager
            pinned = os.getenv("CHROMEDRIVER_VERSION", "").strip()  # optional pin
            service = ChromeService(ChromeDriverManager(version=pinned or None).install())
            self.driver = webdriver.Chrome(service=service, options=opts)

        elif browser == "firefox":
            opts = webdriver.FirefoxOptions()
            opts.add_argument("-headless")

            # Prefer system geckodriver (installed by setup-geckodriver in CI)
            gecko_path = shutil.which("geckodriver")
            if gecko_path:
                service = FirefoxService(executable_path=gecko_path)
            else:
                from webdriver_manager.firefox import GeckoDriverManager
                pinned = os.getenv("GECKODRIVER_VERSION", "").strip()
                service = FirefoxService(executable_path=GeckoDriverManager(version=pinned or None).install())

            self.driver = webdriver.Firefox(service=service, options=opts)
            self.driver.set_window_size(1920, 1080)

        else:
            raise ValueError(f"Browser '{browser}' is not supported.")

        self.driver.get(self.base_url)
        return self.driver

    def teardown(self):
        if self.driver:
            self.driver.quit()
