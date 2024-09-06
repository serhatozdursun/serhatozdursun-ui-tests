import pytest
from utils.driver_manager import DriverManager
from utils.config_loader import load_test_data


# Define a fixture for the WebDriver instance
@pytest.fixture(scope="function")
def driver(request):
    browser = request.config.getoption("--browser")
    driver_manager = DriverManager("https://www.serhatozdursun.com")
    driver = driver_manager.initialize_driver(browser=browser)
    yield driver
    driver_manager.teardown()


# Define a fixture to load test data
@pytest.fixture(scope="session")
def test_data():
    return load_test_data()  # Load the test data once per session


def pytest_addoption(parser):
    parser.addoption("--browser", action="store", default="chrome", help="Browser to run tests on (chrome or firefox)")
