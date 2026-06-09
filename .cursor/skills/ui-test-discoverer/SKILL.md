---
name: ui-test-discoverer
description: >-
  Discovers the live site with Selenium MCP, compares page areas against existing
  pytest coverage, implements missing tests using the POM pattern, runs pytest,
  and opens plus merges a PR when green. Use when expanding UI test coverage or
  when the user asks to discover untested page areas.
---

# UI Test Discoverer

Expand Selenium + pytest coverage for serhatozdursun.com by discovering what is on the page but not yet tested.

**Inspection must use Selenium MCP** (`selenium` server) — not cursor-ide-browser. Reuse locator hints from [ui-test-healer/selenium-mcp.md](../ui-test-healer/selenium-mcp.md).

## Quick start

```bash
poetry run python scripts/ui_test_discoverer.py inventory --base-url https://www.serhatozdursun.com
# Agent: Selenium MCP discover → implement tests
poetry run python scripts/ui_test_discoverer.py verify --push-pr --merge-pr --base-url https://www.serhatozdursun.com
```

## Workflow

```
- [ ] 1. inventory → discovery_manifest.json + test_inventory.json
- [ ] 2. Selenium MCP: full page + scroll + list ids
- [ ] 3. Diff live page vs existing tests / locators / test_data
- [ ] 4. Implement only missing coverage (POM order)
- [ ] 5. verify → pytest
- [ ] 6. Green + file changes → push-pr → merge-pr
- [ ] 7. No gaps → exit success, no PR
```

### Step 1 — Inventory

```bash
poetry run python scripts/ui_test_discoverer.py inventory --base-url "${BASE_URL:-https://www.serhatozdursun.com}"
```

Outputs:
- `reports/discoverer/test_inventory.json` — existing `test_*` methods
- `reports/discoverer/discovery_manifest.json` — MCP checklist and agent instructions

### Step 2 — Selenium MCP discover

1. Read MCP tool schemas for server `selenium`.
2. `start_browser` (chrome, headless) → `navigate` (base URL).
3. `accessibility://current` — page structure.
4. `execute_script` — list elements with `id` and visibility.
5. Scroll full page (`window.scrollTo(0, document.body.scrollHeight)`), re-read accessibility tree.
6. Note **new** sections: ids, links, headings, CTAs not mapped in `pages/locators.py` or `tests/`.
7. `close_session` when done.

### Step 3 — Compare

| Source | What to check |
|--------|----------------|
| `tests/test_*.py` | Existing `test_*` methods |
| `pages/locators.py` | Registered locators |
| `config/test_data.json` | Expected strings and lists |
| Live MCP | Elements visible to users but absent from above |

**Add a test only when** the area is user-visible and behaviour is assertable (text, href, visibility, enabled state).

**Do not** duplicate tests for areas already covered (see manifest `known_areas`).

### Step 4 — Implement (POM order)

1. `config/test_data.json` — expected values for new assertions
2. `pages/locators.py` — new locator keys
3. `pages/home_page.py` — accessor methods (reuse `BasePage` helpers)
4. `tests/test_home.py` (or new `tests/test_*.py` for new pages/routes)

Conventions:
- Use `pytest_check` (`check.equal`, `check.is_true`) like existing tests
- Use `home_page` and `test_data` fixtures from `conftest.py`
- Mark WIP tests `@pytest.mark.in_progress` until stable

### Step 5 — Verify

```bash
poetry run pytest -q --base_url https://www.serhatozdursun.com
# or
poetry run python scripts/ui_test_discoverer.py verify --push-pr --merge-pr
```

### Step 6 — PR and merge

When verify passes and git has changes under `tests/`, `pages/`, or `config/`:

```bash
poetry run python scripts/ui_test_discoverer.py verify --push-pr --merge-pr
```

Requires `GH_TOKEN` and `gh` CLI. Set `DISCOVERER_MERGE_PR=true` in cloud environment for auto-merge.

### Step 7 — Nothing to add

If MCP shows no new assertable areas beyond current inventory, **stop successfully** without opening a PR.

## Cloud agent

See `AGENTS.md` for dashboard prompt, secrets, and `DISCOVERER_PUSH_PR` / `DISCOVERER_MERGE_PR` flags.
