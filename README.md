# serhatozdursun-ui-tests

This project is a sample Selenium Page Object Model (POM) framework using Python. It tests [serhatozdursun.com](https://www.serhatozdursun.com).

The project uses Selenium WebDriver for browser automation and pytest for writing and running tests. Browser drivers are managed automatically via [webdriver-manager](https://github.com/SergeyPirogov/webdriver_manager).

## System Requirements

- **Python**: 3.10 or higher (CI uses 3.12)
- **Poetry**: 2.x
- **Web Browser**: Google Chrome or Mozilla Firefox

## Project Structure

```text
serhatozdursun-ui-tests
├── config
│   └── test_data.json         # Expected page content (header text, icons, etc.)
├── conftest.py                # Pytest fixtures (driver, home_page, test_data)
├── pages                      # Page Object Model classes
│   ├── base_page.py           # Shared wait/interaction helpers
│   ├── home_page.py           # Home page object
│   └── locators.py            # Element locators
├── pyproject.toml             # Python dependencies (Poetry)
├── poetry.lock                # Locked dependency versions
├── pytest.ini                 # Pytest defaults (browser, base URL)
├── tests
│   └── test_home.py           # Home page tests
└── utils
    ├── config_loader.py       # Loads test data JSON
    └── driver_manager.py      # WebDriver setup and teardown
```

## Installation

```bash
poetry install
```

## Running Tests

Run all tests against production (default):

```bash
poetry run pytest
```

Test the local website build (e.g. resume app on port 3000):

```bash
poetry run pytest --base_url http://localhost:3000/
# or
poetry run pytest --base-url http://localhost:3000/
```

Use Firefox instead of Chrome:

```bash
poetry run pytest --browser firefox
```

Run with a visible browser window:

```bash
poetry run pytest --headed
```

Generate an HTML report:

```bash
poetry run pytest --html=reports/html/report.html
```

On failure, screenshots are saved automatically to `reports/screenshots/`.

## Linting and formatting

Install dev dependencies (included in a default `poetry install`):

```bash
poetry install
```

Run checks locally:

```bash
poetry run ruff check .
poetry run ruff format --check .
poetry run black --check .
```

Apply formatters:

```bash
poetry run ruff format .
poetry run black .
```

## Configuration

| Option | Default | Description |
|--------|---------|-------------|
| `--browser` | `chrome` | Browser to use (`chrome` or `firefox`) |
| `--base_url` / `--base-url` | `https://www.serhatozdursun.com` | Application URL under test |
| `--headed` | off | Show the browser window during the run |

Defaults can also be set in `pytest.ini`.

## CI/CD Strategy

| Workflow | Trigger | Target | Purpose |
|----------|---------|--------|---------|
| `lint.yml` | Pull request + push to `main`, manual | — | Ruff lint/format and Black style checks |
| `codeql.yml` | Pull request to `main` | — | CodeQL static security analysis |
| `ui_local_pytest.yml` | Pull request to `main` | `http://localhost:3000/` | Builds [serhatozdursun/resume](https://github.com/serhatozdursun/resume) and tests the latest website code in a container-like CI run |
| `ui_production_pytest.yml` | Daily schedule (06:00 UTC) + manual | `https://www.serhatozdursun.com` | Periodic smoke check of the live site |

UI test workflows run Chrome and Firefox in parallel and upload HTML/XML reports plus failure screenshots. They install only main Poetry dependencies (`--only main`); the lint workflow installs dev dependencies for Ruff and Black.

The resume repository also triggers UI tests on its own pull requests by cloning this test repo and pointing `--base_url` at `http://localhost:3000/`.

## Cursor Cloud agents

Two agents are defined for the [Cursor Cloud dashboard](https://cursor.com/dashboard). Full prompts, secrets, and environment setup are in **`AGENTS.md`**.

| Agent | Skill | Outcome |
|-------|-------|---------|
| **UI Test Healer** | `ui-test-healer` | Heal stale tests after page changes; **fail with console bug report** on real regressions |
| **UI Test Discoverer** | `ui-test-discoverer` | Find untested page areas, add tests, open PR, merge when green |

Environment update script: `bash scripts/cloud_env_setup.sh`

## Healing failed tests

Use the **ui-test-healer** skill with **Selenium MCP** (`selenium` server in `.vscode/mcp.json`).

```bash
# Run → auto-heal → Selenium MCP inspect (agent) → re-run → open PR
poetry run python scripts/ui_test_healer.py --push-pr

# Build MCP inspection checklist from failures
poetry run python scripts/ui_test_healer.py --junit reports/report.xml inspect
```

Flow:
1. Script runs pytest and writes `reports/healer/inspection_manifest.json`
2. Agent inspects the site via **Selenium MCP** (`start_browser` → `navigate` → `get_element_text` / `accessibility://current`)
3. **Page change** → adopt `test_data.json` / locators / tests → re-run → heal PR
4. **Real bug** → console locally; PR comment in CI

See `.cursor/skills/ui-test-healer/selenium-mcp.md` for MCP tool mapping.

## Discovering new tests

```bash
poetry run python scripts/ui_test_discoverer.py inventory
# Agent inspects site via Selenium MCP and implements missing tests
poetry run python scripts/ui_test_discoverer.py verify --push-pr --merge-pr
```

See `.cursor/skills/ui-test-discoverer/SKILL.md` and `AGENTS.md`.
