
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
=======
# Cursor Cloud Agents — serhatozdursun-ui-tests

Configure **two agents** in the [Cursor Cloud dashboard](https://cursor.com/dashboard) for this repository. Both require **Selenium MCP** (`selenium` server, `@angiejones/mcp-selenium`) — add it under Environment → MCP (same as `.vscode/mcp.json`).

## Environment setup (Update script)

Paste the contents of `scripts/cloud_env_setup.sh` into the dashboard **Environment → Update script**, or run:

```bash
bash scripts/cloud_env_setup.sh
```

**Secrets to configure in the dashboard**

| Secret | Used by | Purpose |
|--------|---------|---------|
| `GH_TOKEN` or `GITHUB_TOKEN` | Both | Push branches, open/merge PRs via `gh` |
| `CLOUD_AGENT` | Healer | Set to `true` — bug reports go to console only (no PR comment) |
| `DISCOVERER_PUSH_PR` | Discoverer | Set to `true` — open PR after successful verify |
| `DISCOVERER_MERGE_PR` | Discoverer | Set to `true` — squash-merge PR after tests pass |

Future: `SLACK_WEBHOOK_URL` for bug notifications (not wired yet).

**Default URLs**

| Target | URL |
|--------|-----|
| Production | `https://www.serhatozdursun.com` |
| Local resume app | `http://localhost:3000/` |

---

## Agent 1 — UI Test Healer

**Purpose:** Run the suite; if the page changed, heal tests; if it is a real bug, **fail and print a console report** (no heal PR).

**Skill:** `.cursor/skills/ui-test-healer/SKILL.md`

**Suggested schedule:** Daily or after production deploy (cron / manual).

**Environment variables**

```bash
CLOUD_AGENT=true
GH_TOKEN=<github-token-with-repo-scope>
```

**Agent prompt (copy into dashboard)**

```
You are the UI Test Healer for serhatozdursun-ui-tests.

1. Read and follow the ui-test-healer skill (.cursor/skills/ui-test-healer/SKILL.md).
2. Run: poetry run python scripts/ui_test_healer.py run --base-url https://www.serhatozdursun.com
3. If tests fail, read reports/healer/inspection_manifest.json.
4. Inspect the live site with Selenium MCP (server: selenium) before changing any test.
5. PAGE_CHANGE → update config/test_data.json, pages/locators.py, pages/home_page.py, tests/ as needed.
6. Re-run pytest until green.
7. If healed and files changed: poetry run python scripts/ui_test_healer.py push-pr --base-url https://www.serhatozdursun.com
8. BUG or UNKNOWN (element missing, broken behaviour) → poetry run python scripts/ui_test_healer.py report
   - Print the full console bug report
   - Exit with failure; do NOT open a heal PR
   - Do NOT adopt tests to hide a real regression

Never skip Selenium MCP inspection. Never merge on bug reports.
```

**Success:** Tests pass, or heal PR opened.  
**Failure:** Console bug report; exit code 1.

---

## Agent 2 — UI Test Discoverer

**Purpose:** Discover the live page, compare with existing tests, implement **missing** coverage, run pytest, open PR, and merge when green.

**Skill:** `.cursor/skills/ui-test-discoverer/SKILL.md`

**Suggested schedule:** Weekly or manual.

**Environment variables**

```bash
DISCOVERER_PUSH_PR=true
DISCOVERER_MERGE_PR=true
GH_TOKEN=<github-token-with-repo-and-contents-write>
CLOUD_AGENT=true
```

**Agent prompt (copy into dashboard)**

```
You are the UI Test Discoverer for serhatozdursun-ui-tests.

1. Read and follow the ui-test-discoverer skill (.cursor/skills/ui-test-discoverer/SKILL.md).
2. Run: poetry run python scripts/ui_test_discoverer.py inventory --base-url https://www.serhatozdursun.com
3. Read reports/discoverer/discovery_manifest.json and reports/discoverer/test_inventory.json.
4. Use Selenium MCP (server: selenium) to inspect the full page — including after scroll.
5. Compare live elements with existing tests in tests/, pages/locators.py, and config/test_data.json.
6. For each user-visible area without a test: add locator, page object helper, test_data entry, and pytest method.
   Follow patterns in tests/test_home.py (pytest_check, test_data fixture, POM).
7. Do not duplicate tests that already exist. Do not remove passing tests.
8. Run: poetry run python scripts/ui_test_discoverer.py verify --push-pr --merge-pr --base-url https://www.serhatozdursun.com
9. If nothing new to test, stop with success and do not open a PR.

Only merge when verify exits 0 and pytest is fully green.
```

**Success:** New tests merged via PR, or inventory shows full coverage.  
**Failure:** pytest red — fix or abandon; do not merge.

---

## MCP servers (dashboard)

| Server name | Package | Required |
|-------------|---------|----------|
| `selenium` | `@angiejones/mcp-selenium` | Yes — both agents |

## Local parity

```bash
# Healer
poetry run python scripts/ui_test_healer.py --base-url https://www.serhatozdursun.com

# Discoverer
poetry run python scripts/ui_test_discoverer.py inventory
# … agent implements tests …
poetry run python scripts/ui_test_discoverer.py verify --push-pr --merge-pr
```
