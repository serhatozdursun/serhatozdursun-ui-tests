#!/usr/bin/env python3
"""Run UI tests, auto-heal known page-change patterns, report bugs, and open a PR."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JUNIT_DEFAULT = ROOT / "reports" / "report.xml"
BUGS_JSON = ROOT / "reports" / "healer" / "bugs.json"
MANIFEST_JSON = ROOT / "reports" / "healer" / "inspection_manifest.json"
MCP_SERVER = "selenium"
HEAL_COMMIT_PATHS = (
    "tests/",
    "pages/",
    "config/",
    "scripts/",
    "conftest.py",
    "utils/",
    "README.md",
)

SCROLL_TO_EXPERIENCE_JS = (
    "window.scrollTo(0, arguments[0].getBoundingClientRect().top "
    "+ window.scrollY - 80);"
)
OLD_EXPERIENCE_METHOD_DOCSTRING = (
    "Collect company names while scrolling; "
    "experience entries lazy-load in the section."
)


@dataclass
class TestFailure:
    classname: str
    name: str
    message: str
    classification: str = "UNKNOWN"

    @property
    def nodeid(self) -> str:
        module = self.classname.replace(".", "/") + ".py"
        if not module.startswith("tests/"):
            module = f"tests/{module}"
        return f"{module}::{self.name}"


def run_pytest(base_url: str, browser: str, junit_path: Path) -> int:
    junit_path.parent.mkdir(parents=True, exist_ok=True)
    (ROOT / "reports" / "screenshots").mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        f"--browser={browser}",
        f"--base_url={base_url}",
        "-m",
        "not in_progress",
        f"--junitxml={junit_path}",
    ]
    print(f"[healer] running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=ROOT)
    return result.returncode


def parse_junit(path: Path) -> list[TestFailure]:
    if not path.exists():
        return []

    root = ET.parse(path).getroot()
    failures: list[TestFailure] = []
    for case in root.iter("testcase"):
        failed = case.find("failure") or case.find("error")
        if failed is None:
            continue
        message = (failed.get("message") or failed.text or "").strip()
        failures.append(
            TestFailure(
                classname=case.get("classname", ""),
                name=case.get("name", ""),
                message=message,
            )
        )
    return failures


def classify_failure(failure: TestFailure) -> str:
    msg = failure.message

    if failure.name == "test_home_page_icons" and (
        "/_next/image" in msg or "icon src" in msg
    ):
        return "PAGE_CHANGE"

    if (
        failure.name == "test_experience_companies"
        and "Expected company not found" in msg
    ):
        return "PAGE_CHANGE"

    if "TimeoutException" in msg and "setup" in msg.lower():
        return "BUG"

    if "not visible" in msg.lower() or "not displayed" in msg.lower():
        return "BUG"

    if "not enabled" in msg.lower():
        return "BUG"

    if "AssertionError" in msg or "check" in msg.lower():
        return "PAGE_CHANGE"

    return "UNKNOWN"


def heal_known_patterns() -> list[str]:
    """Apply safe, repo-local fixes for recurring page-change patterns."""
    changes: list[str] = []
    test_file = ROOT / "tests" / "test_home.py"
    home_page_file = ROOT / "pages" / "home_page.py"
    test_src = test_file.read_text()

    old_icon_assert = (
        "            self.verify_text(actual_href, expected['href'], "
        "f'icon href ({actual_href})')\n"
        "            self.verify_text(actual_src_path, expected['src'], "
        "f'icon src ({actual_href})')"
    )
    new_icon_assert = (
        "            self.verify_text(actual_href, expected['href'], "
        "f'icon href ({actual_href})')\n"
        "            filename = expected['src'].lstrip('/')\n"
        "            check.is_true(\n"
        "                filename in decoded_src or "
        "actual_src_path == expected['src'],\n"
        "                f'icon src ({actual_href}): expected {filename} "
        "in {icon_src}'\n"
        "            )"
    )
    if old_icon_assert in test_src and "decoded_src" not in test_src:
        if "from urllib.parse import urlparse" in test_src:
            test_src = test_src.replace(
                "from urllib.parse import urlparse",
                "from urllib.parse import urlparse, unquote",
            )
        old_src_path_line = (
            "            actual_src_path = urlparse("
            "home_page.get_icon_src(link)).path\n"
        )
        test_src = test_src.replace(
            old_src_path_line,
            "            icon_src = home_page.get_icon_src(link)\n"
            "            actual_src_path = urlparse(icon_src).path\n"
            "            decoded_src = unquote(icon_src)\n",
        )
        test_src = test_src.replace(old_icon_assert, new_icon_assert)
        test_file.write_text(test_src)
        changes.append("tests/test_home.py: icon src accepts Next.js /_next/image URLs")

    home_src = home_page_file.read_text()
    old_experience_method = f"""    def get_experience_company_names(self):
        \"\"\"{OLD_EXPERIENCE_METHOD_DOCSTRING}\"\"\"
        container = self.get_experience_container()
        company_names = set()

        last_scroll_y = -1
        for _ in range(30):
            for link in container.find_elements(By.CSS_SELECTOR, "a[href]"):
                name = link.text.strip()
                if name:
                    company_names.add(name)

            self.driver.execute_script("window.scrollBy(0, 400);")
            scroll_y = self.driver.execute_script("return window.scrollY;")
            if scroll_y == last_scroll_y:
                break
            last_scroll_y = scroll_y

        return company_names"""

    new_experience_method = """    def get_experience_company_names(self):
        \"\"\"Collect company names while scrolling.

        Experience entries lazy-load in the section.
        \"\"\"
        container = self.get_experience_container()
        company_names = set()

        self.driver.execute_script(SCROLL_TO_EXPERIENCE_JS, container)

        last_scroll_y = -1
        for _ in range(40):
            for link in container.find_elements(By.CSS_SELECTOR, "a[href]"):
                name = link.text.strip()
                if name and "," in name:
                    company_names.add(name)

            self.driver.execute_script("window.scrollBy(0, 300);")
            scroll_y = self.driver.execute_script("return window.scrollY;")
            if scroll_y == last_scroll_y:
                break
            last_scroll_y = scroll_y

        return company_names"""

    if old_experience_method in home_src:
        home_page_file.write_text(
            home_src.replace(old_experience_method, new_experience_method)
        )
        changes.append(
            "pages/home_page.py: improved experience company scroll collection"
        )

    return changes


def classify_failures(failures: list[TestFailure]) -> list[TestFailure]:
    for failure in failures:
        failure.classification = classify_failure(failure)
    return failures


def mcp_session_steps(base_url: str, browser: str) -> list[dict]:
    return [
        {
            "tool": "start_browser",
            "server": MCP_SERVER,
            "arguments": {"browser": browser, "options": {"headless": True}},
        },
        {"tool": "navigate", "server": MCP_SERVER, "arguments": {"url": base_url}},
        {
            "resource": "accessibility://current",
            "server": MCP_SERVER,
            "note": "Compact page tree — use before targeted element checks",
        },
    ]


def mcp_checks_for_test(test_name: str) -> list[dict]:
    """Selenium MCP checks mapped to this project's home page tests."""
    common_close = {
        "tool": "close_session",
        "server": MCP_SERVER,
        "arguments": {},
    }
    checks_by_test = {
        "test_home_page_header": [
            {
                "tool": "get_element_text",
                "by": "id",
                "value": "name",
                "expected_ref": "home_page.header_text",
            },
            {
                "tool": "execute_script",
                "script": "return document.getElementById('name')?.tagName",
                "expected_ref": "home_page.header_tag",
            },
        ],
        "test_home_page_sub_header": [
            {
                "tool": "get_element_text",
                "by": "id",
                "value": "title",
                "expected_ref": "home_page.sub_header_text",
            },
            {
                "tool": "execute_script",
                "script": "return document.getElementById('title')?.tagName",
                "expected_ref": "home_page.sub_header_tag",
            },
        ],
        "test_home_page_icons": [
            {
                "tool": "execute_script",
                "script": (
                    "return [...document.querySelectorAll('#iconWrapper .iconLink')]"
                    ".map(a => ({href: a.href, "
                    "src: a.querySelector('img')?.src || ''}))"
                ),
                "expected_ref": "home_page.icons",
                "note": (
                    "Accept /_next/image if icons[].src filename appears in src URL"
                ),
            },
        ],
        "test_home_profile_image": [
            {
                "tool": "execute_script",
                "script": (
                    "const el = document.getElementById('profile_image');"
                    "return el && el.offsetParent !== null"
                ),
                "expect": "true",
            },
        ],
        "test_left_column_link_container": [
            {
                "tool": "execute_script",
                "script": (
                    "return [...document.querySelectorAll('.leftColumnLinkContainer')]"
                    ".map(c => ({imgVisible: !!c.querySelector('img')?.offsetParent,"
                    "linkEnabled: !c.querySelector('a')?.disabled}))"
                ),
            },
        ],
        "test_email": [
            {
                "tool": "get_element_text",
                "by": "id",
                "value": "emailLabel",
                "expected_ref": "home_page.email.label",
            },
            {
                "tool": "get_element_text",
                "by": "id",
                "value": "email",
                "expected_ref": "home_page.email.value",
            },
        ],
        "test_phone": [
            {
                "tool": "get_element_text",
                "by": "id",
                "value": "phoneLabel",
                "expected_ref": "home_page.phone.label",
            },
            {
                "tool": "get_element_text",
                "by": "id",
                "value": "phone",
                "expected_ref": "home_page.phone.value",
            },
        ],
        "test_experience_section_title": [
            {
                "tool": "get_element_text",
                "by": "id",
                "value": "experience_container",
                "expected_ref": "home_page.experience_section_title",
            },
        ],
        "test_experience_companies": [
            {
                "tool": "execute_script",
                "script": (
                    "const c = document.getElementById('experience_container');"
                    "c?.scrollIntoView();"
                    "const names = new Set();"
                    "for (let i = 0; i < 40; i++) {"
                    "  c?.querySelectorAll('a[href]').forEach(a => {"
                    "    const t = a.textContent?.trim(); "
                    "if (t && t.includes(',')) names.add(t);"
                    "  });"
                    "  window.scrollBy(0, 300);"
                    "}"
                    "return [...names];"
                ),
                "expected_ref": "home_page.experience_companies",
            },
        ],
        "test_summary": [
            {
                "tool": "execute_script",
                "script": (
                    "const el = document.getElementById('summary'); "
                    "return el && el.offsetParent !== null"
                ),
                "expect": "true",
            },
        ],
        "test_send_message": [
            {
                "tool": "get_element_text",
                "by": "id",
                "value": "sendMessageText",
                "expected_ref": "home_page.send_message_text",
            },
        ],
    }
    steps = checks_by_test.get(
        test_name,
        [
            {
                "note": (
                    f"No preset MCP map for {test_name}; "
                    "use accessibility://current and inspect manually"
                ),
            },
        ],
    )
    return [*steps, common_close]


def build_inspection_manifest(
    failures: list[TestFailure], base_url: str, browser: str
) -> dict:
    classified = classify_failures(list(failures))
    return {
        "mcp_server": MCP_SERVER,
        "mcp_package": "@angiejones/mcp-selenium",
        "base_url": base_url,
        "browser": browser,
        "skill_reference": ".cursor/skills/ui-test-healer/selenium-mcp.md",
        "session": mcp_session_steps(base_url, browser),
        "failures": [
            {
                **asdict(failure),
                "nodeid": failure.nodeid,
                "mcp_checks": mcp_checks_for_test(failure.name),
            }
            for failure in classified
        ],
        "agent_instructions": [
            (
                "Read Selenium MCP tool schemas for server 'selenium' "
                "before calling tools."
            ),
            "Run session steps once, then mcp_checks per failure.",
            (
                "If page changed: adopt config/test_data.json, "
                "pages/locators.py, or tests."
            ),
            "If real bug: run `python scripts/ui_test_healer.py report`.",
            "Re-run pytest; use push-pr when green.",
        ],
    }


def save_inspection_manifest(manifest: dict, path: Path = MANIFEST_JSON) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2))


def print_mcp_instructions(manifest_path: Path = MANIFEST_JSON) -> None:
    print("[healer] Selenium MCP inspection required")
    print(f"[healer] manifest: {manifest_path}")
    print("[healer] server: selenium (@angiejones/mcp-selenium)")
    print("[healer] guide: .cursor/skills/ui-test-healer/selenium-mcp.md")
    print(
        "[healer] invoke ui-test-healer skill and inspect the site "
        "before adopting tests"
    )


def bugs_from_failures(failures: list[TestFailure]) -> list[TestFailure]:
    return [f for f in failures if f.classification in {"BUG", "UNKNOWN"}]


def format_console_report(bugs: list[TestFailure]) -> str:
    if not bugs:
        return "[healer] No real bugs detected."

    lines = ["[healer] UI TEST BUG REPORT", "=" * 40]
    for bug in bugs:
        lines.append(f"TEST: {bug.nodeid}")
        lines.append(f"CLASSIFICATION: {bug.classification}")
        lines.append(f"MESSAGE: {bug.message[:500]}")
        lines.append("-" * 40)
    return "\n".join(lines)


def format_pr_comment(bugs: list[TestFailure]) -> str:
    rows = "\n".join(
        f"| `{bug.name}` | **{bug.classification}** | "
        f"{bug.message[:200].replace('|', '/')} |"
        for bug in bugs
    )
    return f"""## UI test failure report

Automated triage found failures that look like **real regressions** \
(not stale test expectations).

| Test | Classification | Message |
|------|----------------|---------|
{rows}

**Action required**: please investigate before merge.

_Screenshots and JUnit reports are available in the workflow artifacts._
"""


def format_heal_pr_body(applied_changes: list[str], base_url: str) -> str:
    bullets = (
        "\n".join(f"- {change}" for change in applied_changes)
        or "- Updated tests to match current page behaviour"
    )
    return f"""## Auto-healed UI tests

The UI suite failed against page changes. This PR adopts tests and page \
objects so the suite passes again.

**Target URL:** `{base_url}`

**Applied changes:**
{bullets}

**Verification:** `pytest` passed after heal.

---
_Auto-generated by `scripts/ui_test_healer.py`_
"""


def run_git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)


def is_heal_path(path: str) -> bool:
    normalized = path.strip().strip('"')
    return any(
        normalized.startswith(prefix) or normalized == prefix.rstrip("/")
        for prefix in HEAL_COMMIT_PATHS
    )


def changed_heal_files() -> list[str]:
    result = run_git("status", "--porcelain")
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git status failed")

    files: list[str] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip()
        if path.startswith("reports/"):
            continue
        if is_heal_path(path):
            files.append(path)
    return sorted(set(files))


def default_base_branch() -> str:
    env_branch = os.getenv("GITHUB_BASE_REF") or os.getenv("HEALER_BASE_BRANCH")
    if env_branch:
        return env_branch

    remote = run_git("symbolic-ref", "--short", "refs/remotes/origin/HEAD")
    if remote.returncode == 0 and remote.stdout.strip():
        return remote.stdout.strip().replace("origin/", "")

    return "main"


def ensure_git_identity() -> None:
    if os.getenv("GITHUB_ACTIONS") != "true" and os.getenv("CLOUD_AGENT") != "true":
        return
    run_git("config", "user.name", "github-actions[bot]")
    run_git(
        "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"
    )


def create_heal_pull_request(applied_changes: list[str], base_url: str) -> str | None:
    files = changed_heal_files()
    if not files:
        print("[healer] no heal-related file changes; skipping PR")
        return None

    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    if not token:
        print("[healer] GH_TOKEN/GITHUB_TOKEN missing; cannot push branch or open PR")
        return None

    if run_git("rev-parse", "--is-inside-work-tree").returncode != 0:
        print("[healer] not a git repository; skipping PR")
        return None

    ensure_git_identity()
    base_branch = default_base_branch()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    branch = f"heal/ui-tests-{timestamp}"

    checkout = run_git("checkout", "-b", branch)
    if checkout.returncode != 0:
        print(f"[healer] git checkout failed: {checkout.stderr.strip()}")
        return None

    add = run_git("add", *files)
    if add.returncode != 0:
        print(f"[healer] git add failed: {add.stderr.strip()}")
        return None

    commit_message = (
        "heal(ui): adopt UI tests for page changes\n\n"
        f"Target URL: {base_url}\n"
        "Auto-healed by scripts/ui_test_healer.py after pytest failures."
    )
    commit = run_git("commit", "-m", commit_message)
    if commit.returncode != 0:
        print(f"[healer] git commit failed: {commit.stderr.strip()}")
        return None

    push = run_git("push", "-u", "origin", branch)
    if push.returncode != 0:
        print(f"[healer] git push failed: {push.stderr.strip()}")
        return None

    title = f"heal(ui): adopt UI tests for page changes ({timestamp})"
    body = format_heal_pr_body(applied_changes, base_url)
    create = subprocess.run(
        [
            "gh",
            "pr",
            "create",
            "--base",
            base_branch,
            "--head",
            branch,
            "--title",
            title,
            "--body",
            body,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if create.returncode != 0:
        print(f"[healer] gh pr create failed: {create.stderr.strip()}")
        return None

    pr_url = create.stdout.strip()
    print(f"[healer] opened PR: {pr_url}")
    return pr_url


def post_pr_comment(body: str) -> bool:
    if os.getenv("CLOUD_AGENT", "").lower() == "true":
        print("[healer] CLOUD_AGENT=true; bug report is console-only")
        return False
    if os.getenv("GITHUB_ACTIONS") != "true":
        return False
    if os.getenv("GITHUB_EVENT_NAME") != "pull_request":
        print("[healer] not a pull_request event; skipping PR comment")
        return False

    pr_number = os.getenv("GITHUB_EVENT_PULL_REQUEST_NUMBER")
    if not pr_number:
        print("[healer] GITHUB_EVENT_PULL_REQUEST_NUMBER missing; skipping PR comment")
        return False

    repo = os.getenv("GITHUB_REPOSITORY")
    if not repo:
        print("[healer] GITHUB_REPOSITORY missing; skipping PR comment")
        return False

    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    if not token:
        print("[healer] GH_TOKEN/GITHUB_TOKEN missing; skipping PR comment")
        return False

    cmd = ["gh", "pr", "comment", pr_number, "--repo", repo, "--body", body]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[healer] gh pr comment failed: {result.stderr.strip()}")
        return False

    print(f"[healer] posted PR comment on {repo}#{pr_number}")
    return True


def save_bugs(bugs: list[TestFailure], path: Path = BUGS_JSON) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([asdict(b) for b in bugs], indent=2))


def should_push_pr(args: argparse.Namespace) -> bool:
    if args.no_push_pr:
        return False
    if args.push_pr:
        return True
    if os.getenv("GITHUB_ACTIONS") == "true":
        return os.getenv("HEALER_PUSH_PR", "true").lower() == "true"
    return False


def cmd_run(args: argparse.Namespace) -> int:
    return run_pytest(args.base_url, args.browser, Path(args.junit))


def cmd_heal(_: argparse.Namespace) -> int:
    changes = heal_known_patterns()
    if changes:
        print("[healer] auto-heal applied:")
        for change in changes:
            print(f"  - {change}")
    else:
        print("[healer] no auto-heal patterns matched")
    return 0


def cmd_inspect(args: argparse.Namespace) -> int:
    failures = parse_junit(Path(args.junit))
    if not failures:
        print("[healer] no failures in junit report; no MCP inspection needed")
        return 0

    manifest = build_inspection_manifest(failures, args.base_url, args.browser)
    save_inspection_manifest(manifest)
    print_mcp_instructions()
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    failures = parse_junit(Path(args.junit))
    if not failures:
        print("[healer] no failures in junit report")
        return 0

    classified = classify_failures(failures)
    bugs = bugs_from_failures(classified)
    save_bugs(bugs)

    page_changes = [f for f in classified if f.classification == "PAGE_CHANGE"]
    if page_changes:
        print(
            f"[healer] {len(page_changes)} failure(s) classified as "
            "PAGE_CHANGE (adopt tests)"
        )

    report = format_console_report(bugs)
    print(report)

    if bugs:
        post_pr_comment(format_pr_comment(bugs))
        return 1
    return 0


def cmd_push_pr(args: argparse.Namespace) -> int:
    pr_url = create_heal_pull_request([], args.base_url)
    return 0 if pr_url else 1


def cmd_full_loop(args: argparse.Namespace) -> int:
    junit = Path(args.junit)
    had_initial_failures = False
    applied_changes: list[str] = []

    exit_code = cmd_run(args)
    failures = parse_junit(junit)

    if failures:
        had_initial_failures = True
        print(f"[healer] {len(failures)} failure(s) detected")
        save_inspection_manifest(
            build_inspection_manifest(failures, args.base_url, args.browser)
        )
        if args.auto_heal:
            applied_changes = heal_known_patterns()
            if applied_changes:
                print("[healer] auto-heal applied:")
                for change in applied_changes:
                    print(f"  - {change}")
            exit_code = cmd_run(args)
            failures = parse_junit(junit)
            if failures:
                save_inspection_manifest(
                    build_inspection_manifest(failures, args.base_url, args.browser)
                )

    if failures:
        classify_failures(failures)
        page_changes = [f for f in failures if f.classification == "PAGE_CHANGE"]
        bugs = bugs_from_failures(failures)

        print_mcp_instructions()

        if page_changes:
            print(
                f"[healer] {len(page_changes)} failure(s) need Selenium MCP inspection "
                "before adopting tests"
            )

        if bugs:
            return cmd_report(args)
        return 1

    print("[healer] all tests passed")

    if had_initial_failures and should_push_pr(args):
        create_heal_pull_request(applied_changes, args.base_url)

    return exit_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="UI test healer for serhatozdursun-ui-tests"
    )
    parser.add_argument(
        "--base-url",
        "--base_url",
        dest="base_url",
        default="https://www.serhatozdursun.com",
    )
    parser.add_argument("--browser", default="chrome")
    parser.add_argument("--junit", default=str(JUNIT_DEFAULT))
    parser.add_argument("--no-auto-heal", action="store_true")
    parser.add_argument(
        "--push-pr",
        action="store_true",
        help="Push branch and open PR after successful heal",
    )
    parser.add_argument(
        "--no-push-pr", action="store_true", help="Never push branch or open PR"
    )

    sub = parser.add_subparsers(dest="command")

    sub.add_parser("run", help="Run pytest and write JUnit report")
    sub.add_parser(
        "inspect", help="Build Selenium MCP inspection manifest from JUnit failures"
    )
    sub.add_parser("heal", help="Apply known auto-heal patches")
    sub.add_parser("report", help="Classify failures and report bugs")
    sub.add_parser("push-pr", help="Commit current heal changes and open a PR")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    args.auto_heal = not args.no_auto_heal

    if args.command == "run":
        return cmd_run(args)
    if args.command == "inspect":
        return cmd_inspect(args)
    if args.command == "heal":
        return cmd_heal(args)
    if args.command == "report":
        return cmd_report(args)
    if args.command == "push-pr":
        return cmd_push_pr(args)

    return cmd_full_loop(args)


if __name__ == "__main__":
    raise SystemExit(main())
