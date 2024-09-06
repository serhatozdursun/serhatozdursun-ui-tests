# serhatozdursun-ui-tests

This project is created as a sample of the Selenium Page Object Model (POM) framework using Python. It is used to test the website [serhatozdursun.com](https://www.serhatozdursun.com), which will be updated once the repository [serhatozdursun/resume](https://github.com/serhatozdursun/resume) is merged with new code.

The project uses Selenium WebDriver for browser automation and pytest for writing and running tests. It follows the POM structure, making the tests modular, reusable, and easier to maintain.

## System Requirements

- **Python**: 3.7 or higher
- **Pip**: Latest version
- **Web Browser**: Google Chrome (or any other supported browser; make sure the WebDriver for the browser is compatible with the browser version)

## Project Structure

```markdown
serhatozdursun-ui-tests
├── config
│   └── test_data.json         # Contains test data (header text, icons, etc.)
├── conftest.py                # Pytest configurations (e.g., fixtures)
├── pages                      # Page classes following the POM structure
│   ├── __init__.py
│   ├── base_page.py           # Base page with common methods for other pages
│   └── home_page.py           # Home page object class
├── pytest.ini                 # Pytest configuration file
├── requirements.txt           # Dependencies needed for the project
├── tests                      # Test files
│   ├── __init__.py
│   └── test_home.py           # Tests for the Home page
└── utils                      # Utility modules for config and driver management
    ├── __init__.py
    ├── config_loader.py       # Loads config and test data
    └── driver_manager.py      # Manages WebDriver setup
```
## Requirements
The project dependencies can be found in the requirements.txt file. You can install them using pip:
```bash
pip install -r requirements.txt
```

## Running Tests

To run the tests, simply execute:

```bash
pytest
```
If you prefer to use Firefox, you can specify it as follows:

```bash
pytest --browser firefox
```
```bash
pytest --browser chrome
```
If no browser parameter is provided, Chrome is used as the default browser.
