from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
import os
import shutil

class DriverManager:
    def __init__(self, base_url):
        self.driver = None
        self.base_url = base_url

    def initialize_driver(self, browser: str):
        if browser == "chrome":
            opts = webdriver.ChromeOptions()
            # Headless + stable CI flags
            opts.add_argument("--headless=new")
            opts.add_argument("--disable-gpu")
            opts.add_argument("--no-sandbox")
            opts.add_argument("--window-size=1920,1080")

            # Use chromedriver from PATH if available; else fall back to webdriver_manager
            chromedriver_path = shutil.which("chromedriver")
            if chromedriver_path:
                service = ChromeService(executable_path=chromedriver_path)
            else:
                # fallback only hits network if needed
                from webdriver_manager.chrome import ChromeDriverManager
                pinned = os.getenv("CHROMEDRIVER_VERSION", "").strip()  # e.g. "128.0.6613.137"
                service = ChromeService(ChromeDriverManager(version=pinned or None).install())

            self.driver = webdriver.Chrome(service=service, options=opts)

        elif browser == "firefox":
            opts = webdriver.FirefoxOptions()
            opts.add_argument("-headless")
            # "--kiosk" has no effect in headless; omit to avoid confusion

            # Prefer system geckodriver (installed by setup-geckodriver in CI)
            geckodriver_path = shutil.which("geckodriver")
            if geckodriver_path:
                service = FirefoxService(executable_path=geckodriver_path)
            else:
                from webdriver_manager.firefox import GeckoDriverManager
                pinned = os.getenv("GECKODRIVER_VERSION", "").strip()  # e.g. "0.35.0"
                service = FirefoxService(executable_path=GeckoDriverManager(version=pinned or None).install())

            self.driver = webdriver.Firefox(service=service, options=opts)
            # Ensure consistent viewport in headless
            self.driver.set_window_size(1920, 1080)

        else:
            raise ValueError(f"Browser '{browser}' is not supported.")

        self.driver.get(self.base_url)
        return self.driver

    def teardown(self):
        if self.driver:
            self.driver.quit()
