# Selenium MCP inspection guide

This project configures Selenium MCP in `.vscode/mcp.json`:

```json
{
  "mcpServers": {
    "selenium": {
      "command": "npx",
      "args": ["-y", "@angiejones/mcp-selenium@latest"]
    }
  }
}
```

Server: **`selenium`** — [@angiejones/mcp-selenium](https://github.com/angiejones/mcp-selenium)

## Required MCP workflow (agent)

Always inspect the live site with Selenium MCP **before** adopting tests or reporting bugs.

```
1. start_browser (chrome, headless)
2. navigate (base_url from pytest/healer)
3. Fetch accessibility://current  (page structure)
4. Run targeted checks per failure (below)
5. close_session
6. Adopt tests OR report bug
7. pytest verify
8. push-pr if green
```

## Core tools

| Tool | Use |
|------|-----|
| `start_browser` | `{ "browser": "chrome", "options": { "headless": true } }` |
| `navigate` | `{ "url": "https://www.serhatozdursun.com" }` |
| `get_element_text` | `{ "by": "id", "value": "name" }` |
| `get_element_attribute` | `{ "by": "id", "value": "email", "attribute": "href" }` |
| `execute_script` | Scroll lazy sections: `window.scrollBy(0, 400)` |
| `take_screenshot` | Evidence on ambiguous failures |
| `accessibility://current` | Resource — compact page tree |
| `close_session` | Always close when done |

Locator strategies: `id`, `css`, `xpath`, `name`, `tag`, `class`.

## Project locator map

| Area | MCP check |
|------|-----------|
| Header | `get_element_text` id=`name`; tag via `execute_script`: `document.getElementById('name').tagName` |
| Sub-header | id=`title` |
| Icons | css=`#iconWrapper .iconLink` — `get_element_attribute` `href`; child img `src` |
| Profile image | id=`profile_image` — visible via `execute_script` offsetParent |
| Email / phone | id=`emailLabel`, `email`, `phoneLabel`, `phone` |
| Experience | id=`experience_container` — scroll with `execute_script`, collect company link text |
| Send message | id=`sendMessageText` |
| Summary | id=`summary` |

## Failure → MCP checklist

### `test_home_page_icons`
- Count links: css `#iconWrapper .iconLink`
- For each href in `config/test_data.json` → `icons[].href`, verify `get_element_attribute` href
- For src: accept `/_next/image` if filename from `icons[].src` appears in decoded src URL

### `test_experience_companies`
- `execute_script` scroll through page
- Collect link texts inside `#experience_container` containing `,`
- Compare with `experience_companies` in test_data; update JSON if page changed

### Locator timeout / element missing
- `accessibility://current` — is element present under different name/role?
- **Present with new id** → PAGE_CHANGE → update `pages/locators.py`
- **Absent entirely** → BUG → report

### Text mismatch
- `get_element_text` on locator
- Element exists, text changed → PAGE_CHANGE → `config/test_data.json`
- Element empty or wrong link → BUG

## Classification after MCP

| MCP finding | Result |
|-------------|--------|
| Content changed, behaviour OK | Adopt test_data / assertion → re-run pytest |
| Locator id/class changed | Adopt `locators.py` |
| Lazy-load needs scroll | Adopt `home_page.py` |
| Dead link, missing section, not visible | **BUG** — console locally, PR comment in CI |
