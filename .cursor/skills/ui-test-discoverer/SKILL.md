---
name: ui-test-discoverer
description: >-
  Discovers the live site with Selenium MCP, compares page areas against existing
  pytest coverage, implements missing tests using the POM pattern, runs pytest,
  and opens plus merges a PR when green. Use when expanding UI test coverage or
  when the user asks to discover untested page areas.
---

# UI Test Discoverer

Expand Selenium + pytest coverage for serhatozdursun.com by crawling **same-domain routes** (home + sub-pages) and discovering what is not yet tested.

**Inspection must use Selenium MCP** (`selenium` server) — not cursor-ide-browser. Reuse locator hints from [ui-test-healer/selenium-mcp.md](../ui-test-healer/selenium-mcp.md).

## Quick start

```bash
poetry run python scripts/ui_test_discoverer.py --base-url https://www.serhatozdursun.com inventory
# Agent: Selenium MCP discover every route in site_map.json → implement tests
poetry run python scripts/ui_test_discoverer.py --base-url https://www.serhatozdursun.com --push-pr --merge-pr verify
```

## Workflow

```
- [ ] 1. inventory → site_map.json + discovery_manifest.json + test_inventory.json
- [ ] 2. Crawl same-domain hrefs (BFS); skip external links (LinkedIn, GitHub, etc.)
- [ ] 3. Selenium MCP: each route in site_map — scroll + list ids
- [ ] 4. Diff every route vs existing tests / locators / test_data
- [ ] 5. Implement missing coverage per route (POM order)
- [ ] 6. verify → pytest
- [ ] 7. Green + file changes → push-pr → merge-pr
- [ ] 8. No gaps → exit success, no PR
```

### Step 1 — Inventory

```bash
poetry run python scripts/ui_test_discoverer.py inventory --base-url "${BASE_URL:-https://www.serhatozdursun.com}"
```

Outputs:
- `reports/discoverer/site_map.json` — crawled same-domain routes, element ids per page, `route_gaps`
- `reports/discoverer/test_inventory.json` — existing `test_*` methods + route gaps
- `reports/discoverer/discovery_manifest.json` — MCP checklist per route and agent instructions

The inventory step uses headless Selenium to BFS-crawl **only** links on the same host as `base_url` (e.g. `/practice`, `/mentorship`). External hrefs are ignored.

### Step 2 — Selenium MCP discover (every route)

1. Read MCP tool schemas for server `selenium`.
2. Read `site_map.json` → `routes` and `route_gaps`.
3. For **each** route URL (home first, then sub-pages):
   - `start_browser` (chrome, headless) → `navigate` (route URL)
   - `accessibility://current` — page structure
   - `execute_script` — scroll + list elements with `id` and visibility
   - Note ids, headings, CTAs not mapped in locators/tests for that route
4. `close_session` when done.

Sub-pages get `tests/test_<slug>.py` and `pages/<slug>_page.py` (e.g. `/practice` → `test_practice.py`).

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

## Cloud agent & Cursor Automation

See `AGENTS.md` for:
- Dashboard prompt, secrets, `DISCOVERER_PUSH_PR` / `DISCOVERER_MERGE_PR`
- **Cursor Automation** trigger: PR merged on `serhatozdursun/resume` with label `discover`
- GitHub Actions bridge: `docs/resume-repo-discover-trigger.yml` + `.github/workflows/ui_discoverer.yml`
