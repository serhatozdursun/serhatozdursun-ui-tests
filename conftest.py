import logging
from datetime import datetime
from pathlib import Path

import pytest

from pages.home_page import HomePage
from utils.config_loader import load_test_data
from utils.driver_manager import DriverManager

logger = logging.getLogger(__name__)
SCREENSHOTS_DIR = Path("reports/screenshots")


@pytest.fixture(scope="function")
def driver(request):
    browser = request.config.getoption("--browser") or request.config.getini("browser")
    base_url = request.config.getoption("--base_url") or request.config.getini(
        "base_url"
    )
    headed = request.config.getoption("--headed")

    logger.debug(f"Base URL used for WebDriver initialization: {base_url}")
    logger.debug(f"Browser used for WebDriver initialization: {browser}")

    driver_manager = DriverManager(base_url)
    web_driver = driver_manager.initialize_driver(browser=browser, headless=not headed)
    yield web_driver
    driver_manager.teardown()


@pytest.fixture
def home_page(driver):
    return HomePage(driver)


@pytest.fixture(scope="session")
def test_data():
    return load_test_data()


def pytest_addoption(parser):
    parser.addoption(
        "--browser", action="store", help="Browser to run tests on (chrome or firefox)"
    )
    parser.addoption(
        "--base_url",
        action="store",
        default=None,
        help="Base URL for the application under test",
    )
    parser.addoption(
        "--base-url",
        dest="base_url",
        action="store",
        default=None,
        help="Alias for --base_url",
    )
    parser.addoption(
        "--headed",
        action="store_true",
        default=False,
        help="Run browser in headed mode",
    )
    parser.addini("browser", default="chrome", help="Default browser for tests")
    parser.addini(
        "base_url",
        default="https://www.serhatozdursun.com",
        help="Base URL for the application under test",
    )


def pytest_configure(config):
    try:
        if not config.getoption("--base_url"):
            config.option.base_url = config.getini("base_url")
    except AttributeError as e:
        logger.error(f"AttributeError: {e}")
        config.option.base_url = config.getini("base_url")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        config.option.base_url = config.getini("base_url")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when != "call" or not report.failed:
        return

    driver = item.funcargs.get("driver")
    if driver is None:
        return

    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"{item.name}_{timestamp}.png"
    screenshot_path = SCREENSHOTS_DIR / filename

    try:
        if driver.save_screenshot(str(screenshot_path)):
            report.sections.append(("Screenshot", str(screenshot_path)))
            logger.info(f"Saved failure screenshot: {screenshot_path}")
    except Exception as e:
        logger.warning(f"Could not save screenshot for {item.name}: {e}")
