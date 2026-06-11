import contextlib
import os
import shutil

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service as FirefoxService

PAGE_LOAD_TIMEOUT_SECONDS = 30


class DriverManager:
    def __init__(self, base_url):
        self.driver = None
        self.base_url = base_url

    def initialize_driver(self, browser: str, headless: bool = True):
        if browser == "chrome":
            from webdriver_manager.chrome import ChromeDriverManager

            opts = webdriver.ChromeOptions()
            opts.page_load_strategy = "eager"
            if headless:
                opts.add_argument("--headless=new")
            opts.add_argument("--disable-gpu")
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-dev-shm-usage")
            opts.add_argument("--window-size=1920,1080")

            service = ChromeService(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=opts)

        elif browser == "firefox":
            opts = webdriver.FirefoxOptions()
            opts.page_load_strategy = "eager"
            if headless:
                opts.add_argument("-headless")
            opts.set_preference("general.platform.override", "MacIntel")
            opts.set_preference("layout.css.devPixelsPerPx", "1.0")

            gecko_path = shutil.which("geckodriver")
            if gecko_path:
                service = FirefoxService(gecko_path)
            else:
                from webdriver_manager.firefox import GeckoDriverManager

                pinned = os.getenv("GECKODRIVER_VERSION", "").strip()
                service = FirefoxService(
                    GeckoDriverManager(version=pinned or None).install()
                )

            self.driver = webdriver.Firefox(service=service, options=opts)
            self.driver.set_window_size(1920, 1080)

        else:
            raise ValueError(f"Browser '{browser}' is not supported.")

        self.driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT_SECONDS)
        self._load_base_url()
        return self.driver

    def _page_usable(self) -> bool:
        with contextlib.suppress(Exception):
            return bool(self.driver.find_elements(By.ID, "name"))
        return False

    def _recoverable_navigation_error(self, exc: Exception) -> bool:
        if isinstance(exc, TimeoutException):
            return True
        if isinstance(exc, WebDriverException):
            message = str(exc).lower()
            return "timeout" in message or "nettimeout" in message
        return False

    def _load_base_url(self, retries: int = 2) -> None:
        last_error: Exception | None = None
        for _ in range(retries + 1):
            try:
                self.driver.get(self.base_url)
                return
            except Exception as exc:
                if not self._recoverable_navigation_error(exc):
                    raise
                last_error = exc
                # Lazy-scroll pages may never fire "load"; stop and use eager DOM.
                with contextlib.suppress(Exception):
                    self.driver.execute_script("window.stop();")
                if self._page_usable():
                    return
        if last_error is not None:
            raise last_error

    def teardown(self):
        if self.driver:
            self.driver.quit()
