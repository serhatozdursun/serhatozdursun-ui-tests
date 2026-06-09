---
name: ui-test-healer
description: >-
  Triages failing Selenium UI tests using the Selenium MCP server to inspect the live site,
  adopts tests when the page changed, re-runs pytest until green, pushes a heal PR, and reports
  real bugs to the console (cloud agent) or as a PR comment in CI. Use when pytest fails,
  UI tests need healing, or the user asks to fix or adopt failing tests.
---

# UI Test Healer

Heal failing tests for this Selenium + pytest POM suite.

**Inspection must use Selenium MCP** (`selenium` server, `@angiejones/mcp-selenium`) — not cursor-ide-browser. See [selenium-mcp.md](selenium-mcp.md).

## Quick start

```bash
# Script: run pytest, write inspection manifest for MCP
python scripts/ui_test_healer.py run --base-url https://www.serhatozdursun.com

# Agent: read reports/healer/inspection_manifest.json → Selenium MCP inspect → adopt → verify
python scripts/ui_test_healer.py --push-pr
```

## Workflow

```
- [ ] 1. Run healer/pytest → failures + inspection_manifest.json
- [ ] 2. Selenium MCP: start_browser → navigate → inspect (see selenium-mcp.md)
- [ ] 3. Classify: page change vs real bug
- [ ] 4. Page change → adopt test_data / locators / tests / page objects
- [ ] 5. Re-run pytest (or full healer loop)
- [ ] 6. Green + file changes → push-pr
- [ ] 7. Real bugs → console (local) or PR comment (CI)
```

### Step 1 — Run tests and build manifest

```bash
python scripts/ui_test_healer.py run --base-url "${BASE_URL:-https://www.serhatozdursun.com}"
python scripts/ui_test_healer.py --junit reports/report.xml inspect
```

Outputs:
- `reports/report.xml`
- `reports/healer/inspection_manifest.json` — MCP checklist per failure
- `reports/screenshots/` on pytest failure

### Step 2 — Selenium MCP inspect (mandatory)

1. **Read MCP tool schemas** for server `selenium` before calling tools.
2. `start_browser` — chrome, headless
3. `navigate` — same `--base-url` as pytest
4. `accessibility://current` — page structure
5. Per failure, run checks in [selenium-mcp.md](selenium-mcp.md)
6. `take_screenshot` if ambiguous
7. `close_session` when finished

Example:

```json
{ "browser": "chrome", "options": { "headless": true } }
→ navigate url
→ get_element_text { "by": "id", "value": "name" }
→ get_element_attribute { "by": "css", "value": "#iconWrapper .iconLink", "attribute": "href" }
```

### Step 3 — Classify

| MCP evidence | Classification |
|--------------|----------------|
| Element exists, text/src/href changed | **PAGE_CHANGE** |
| Next.js `/_next/image` src | **PAGE_CHANGE** |
| Lazy content after scroll | **PAGE_CHANGE** |
| Locator id changed, element still there | **PAGE_CHANGE** |
| Required element/link missing or broken | **BUG** |
| Not visible / not enabled when should be | **BUG** |

### Step 4 — Adopt (page change only)

Edit order: `config/test_data.json` → `pages/locators.py` → `pages/home_page.py` → `tests/test_home.py`

Optional pattern auto-heal:

```bash
python scripts/ui_test_healer.py heal
```

### Step 5 — Verify

```bash
pytest --lf -q
# or
python scripts/ui_test_healer.py --push-pr
```

### Step 6 — Open heal PR

When tests pass after healing and git has changes:

```bash
python scripts/ui_test_healer.py push-pr --base-url https://www.serhatozdursun.com
```

CI enables this with `HEALER_PUSH_PR=true` and `--push-pr`.

### Step 7 — Report real bugs

```bash
python scripts/ui_test_healer.py report --junit reports/report.xml
```

- **Cloud agent** (`CLOUD_AGENT=true`): structured stdout only — **fail the run**, do not open a heal PR
- **Local**: structured stdout
- **CI pull_request**: `gh pr comment` on the triggering PR (skipped when `CLOUD_AGENT=true`)
- **Future**: Slack via `SLACK_WEBHOOK_URL` (not implemented yet)

## CI vs cloud agent

| Environment | Inspection | Adopt | Heal PR | Bug report |
|-------------|------------|-------|---------|------------|
| **Cloud healer agent** | Selenium MCP (required) | Manual + optional `heal` | `--push-pr` if green | Console only, exit 1 |
| **GitHub Actions** | pytest + pattern `heal` only | auto-heal patterns | `--push-pr` if green | PR comment |
| **Local + skill** | Selenium MCP (required) | Manual + optional `heal` | `--push-pr` | Console |

Cloud dashboard setup: see `AGENTS.md`.

In CI, run the agent with Selenium MCP locally when auto-heal is insufficient.

## Project conventions

- Default URL: `https://www.serhatozdursun.com`
- Local container: `http://localhost:3000/`
- MCP server name: `selenium` (see `.vscode/mcp.json`)
