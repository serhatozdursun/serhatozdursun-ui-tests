# AGENTS.md

## Cursor Cloud specific instructions

### What this repository is

This repo is a **Python Selenium + pytest UI test suite** for [serhatozdursun.com](https://www.serhatozdursun.com). It is **not** the portfolio site itself — the site lives in the separate [serhatozdursun/resume](https://github.com/serhatozdursun/resume) repository.

Tests use a Page Object Model under `pages/`, expected values in `config/test_data.json`, and headless Chrome/Firefox via `utils/driver_manager.py`.

### Services

| Service | Required? | Notes |
|--------|-----------|-------|
| Python 3.7+ (CI uses 3.12) | Yes | `pip install -r requirements.txt` |
| Google Chrome | Yes (default) | Pre-installed on Cloud VMs; tests run headless |
| Application under test | Yes | Either production URL or local resume app on port 3000 |
| Firefox + geckodriver | Optional | `pytest --browser firefox` |

There is no docker-compose, Makefile, or local app server in this repo.

### Base URL gotcha

`pytest.ini` defaults to `http://localhost:3000/`. To run against production without a local resume server:

```bash
pytest --base_url https://www.serhatozdursun.com
```

CI workflows do not pass `--base_url` and do not start the resume app, so they rely on whatever `pytest.ini` resolves to at runtime.

### Running tests

Use `python -m pytest` if `pytest` is not on `PATH` (pip user installs go to `~/.local/bin`).

```bash
# Default (Chrome + base_url from pytest.ini)
python -m pytest

# Match CI reporting
mkdir -p reports/html
python -m pytest -m "not in_progress" \
  --html=reports/html/report.html \
  --junitxml=reports/report.xml

# Production smoke run
python -m pytest --base_url https://www.serhatozdursun.com --browser chrome -v
```

### Lint / build

No lint or formatter is configured in this repo (no ruff, flake8, pylint, or pre-commit). CI runs CodeQL on Python only. Validation is done by running pytest.

### Local resume app (optional)

To test against `localhost:3000`, clone and run the resume project separately on port 3000, then run `pytest` without overriding `--base_url`.
