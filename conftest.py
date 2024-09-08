import pytest
import logging
from utils.driver_manager import DriverManager
from utils.config_loader import load_test_data

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Define a fixture for the WebDriver instance
@pytest.fixture(scope="function")
def driver(request):
    # Retrieve the browser option from command line, fall back to pytest.ini
    browser = request.config.getoption("--browser") or request.config.getini('browser')

    # Retrieve the base URL from command line, fall back to pytest.ini
    base_url = request.config.getoption("--base_url") or request.config.getini('base_url')
    base_url = f'https://{base_url}'

    # Log the base_url and browser for debugging purposes
    logger.debug(f"Base URL used for WebDriver initialization: {base_url}")
    logger.debug(f"Browser used for WebDriver initialization: {browser}")

    driver_manager = DriverManager(base_url)
    driver = driver_manager.initialize_driver(browser=browser)
    yield driver
    driver_manager.teardown()


# Define a fixture to load test data
@pytest.fixture(scope="session")
def test_data():
    return load_test_data()  # Load the test data once per session


# Add custom command-line options for pytest
def pytest_addoption(parser):
    parser.addoption("--browser", action="store", help="Browser to run tests on (chrome or firefox)")
    parser.addoption("--base_url", action="store", help="Base URL for the application under test")
    parser.addini("browser", default="chrome", help="Default browser for tests")
    parser.addini("base_url", default="https://www.serhatozdursun.com", help="Base URL for the application under test")


def pytest_configure(config):
    try:
        # Ensure base_url is set correctly from ini file if not provided via command line
        if not config.getoption("--base_url"):
            config.option.base_url = config.getini('base_url')
    except AttributeError as e:
        # Handle potential AttributeError if config.option.base_url does not exist
        logger.error(f"AttributeError: {e}")
        config.option.base_url = config.getini('base_url')
    except Exception as e:
        # Handle any other unexpected exceptions
        logger.error(f"Unexpected error: {e}")
        config.option.base_url = config.getini('base_url')
