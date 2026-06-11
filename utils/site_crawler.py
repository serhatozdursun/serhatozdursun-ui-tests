"""Crawl same-domain routes and collect visible element ids per page."""

from __future__ import annotations

import re
from collections import deque
from urllib.parse import urldefrag, urljoin, urlparse

from selenium.webdriver.remote.webdriver import WebDriver

COLLECT_LINKS_JS = """
return [...document.querySelectorAll('a[href]')]
  .map(a => a.href)
  .filter(Boolean);
"""

COLLECT_IDS_JS = """
return [...document.querySelectorAll('[id]')]
  .map(el => ({
    id: el.id,
    tag: el.tagName,
    visible: el.offsetParent !== null || el.getClientRects().length > 0
  }))
  .filter(item => item.id && !item.id.startsWith('__'));
"""

SCROLL_PAGE_JS = """
window.scrollTo(0, document.body.scrollHeight);
return document.body.scrollHeight;
"""


def _host(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def canonical_page_url(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    origin = f"{parsed.scheme}://{parsed.netloc.lower()}"
    if path == "/":
        return origin
    return f"{origin}{path}"


def normalize_same_domain_link(href: str, base_url: str) -> str | None:
    """Return normalized absolute URL when href stays on the same host."""
    if not href or href.startswith(("mailto:", "tel:", "javascript:")):
        return None

    absolute = urljoin(base_url, href)
    clean, _ = urldefrag(absolute)
    parsed = urlparse(clean)

    if parsed.scheme not in ("http", "https"):
        return None
    if _host(clean) != _host(base_url):
        return None

    return canonical_page_url(clean)


def path_from_url(url: str) -> str:
    path = urlparse(url).path or "/"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    return path


def route_to_test_module(path: str) -> str:
    if path in ("", "/"):
        return "test_home"
    slug = path.strip("/").replace("-", "_").replace("/", "_")
    slug = re.sub(r"[^a-zA-Z0-9_]", "_", slug)
    return f"test_{slug}"


def collect_page_element_ids(driver: WebDriver) -> list[dict[str, str | bool]]:
    driver.execute_script(SCROLL_PAGE_JS)
    return driver.execute_script(COLLECT_IDS_JS) or []


def collect_same_domain_links(driver: WebDriver, base_url: str) -> set[str]:
    links: set[str] = set()
    for href in driver.execute_script(COLLECT_LINKS_JS) or []:
        normalized = normalize_same_domain_link(href, base_url)
        if normalized:
            links.add(normalized)
    return links


def crawl_site(
    driver: WebDriver,
    base_url: str,
    *,
    max_pages: int = 25,
) -> dict:
    """BFS crawl starting at base_url; only follow same-domain http(s) links."""
    start = canonical_page_url(
        normalize_same_domain_link(base_url, base_url) or base_url
    )

    visited: set[str] = set()
    queue: deque[str] = deque([start])
    pages: list[dict] = []

    while queue and len(visited) < max_pages:
        url = queue.popleft()
        if url in visited:
            continue

        driver.get(url)
        visited.add(url)

        element_ids = collect_page_element_ids(driver)
        outbound = collect_same_domain_links(driver, base_url)

        route = path_from_url(url)
        pages.append(
            {
                "url": url,
                "path": route,
                "test_module": route_to_test_module(route),
                "element_ids": element_ids,
                "same_domain_links": sorted(outbound),
            }
        )

        for link in sorted(outbound):
            if link not in visited:
                queue.append(link)

    tested_modules = set()
    routes_without_tests: list[dict] = []
    for page in pages:
        module = page["test_module"]
        if module in tested_modules:
            continue
        tested_modules.add(module)
        routes_without_tests.append(
            {
                "path": page["path"],
                "url": page["url"],
                "test_module": module,
                "suggested_test_file": f"tests/{module}.py",
            }
        )

    return {
        "base_url": base_url,
        "host": _host(base_url),
        "pages_crawled": len(pages),
        "pages": pages,
        "routes": [
            {"path": p["path"], "url": p["url"], "test_module": p["test_module"]}
            for p in pages
        ],
        "routes_without_tests": routes_without_tests,
    }
