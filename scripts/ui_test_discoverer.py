#!/usr/bin/env python3
"""Discover untested page areas, guide MCP inspection, verify tests, open/merge PR."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JUNIT_DEFAULT = ROOT / "reports" / "report.xml"
MANIFEST_JSON = ROOT / "reports" / "discoverer" / "discovery_manifest.json"
INVENTORY_JSON = ROOT / "reports" / "discoverer" / "test_inventory.json"
MCP_SERVER = "selenium"

DISCOVER_COMMIT_PATHS = (
    "tests/",
    "pages/",
    "config/",
    "conftest.py",
    "utils/",
)

KNOWN_PAGE_AREAS = [
    {
        "id": "header",
        "label": "Main header (name)",
        "locator_key": "header",
        "mcp": {"by": "id", "value": "name"},
        "test_hint": "test_home_page_header",
    },
    {
        "id": "sub_header",
        "label": "Sub-header / title block",
        "locator_key": "title",
        "mcp": {"by": "id", "value": "title"},
        "test_hint": "test_home_page_sub_header",
    },
    {
        "id": "icons",
        "label": "Social / profile icon links",
        "locator_key": "icon_wrapper",
        "mcp": {"by": "css", "value": "#iconWrapper .iconLink"},
        "test_hint": "test_home_page_icons",
    },
    {
        "id": "profile_image",
        "label": "Profile image",
        "locator_key": "profile_image",
        "mcp": {"by": "id", "value": "profile_image"},
        "test_hint": "test_home_profile_image",
    },
    {
        "id": "left_column_links",
        "label": "Left column link containers",
        "locator_key": "left_column_link_container",
        "mcp": {"by": "css", "value": ".leftColumnLinkContainer"},
        "test_hint": "test_left_column_link_container",
    },
    {
        "id": "email",
        "label": "Email label and value",
        "locator_key": "email",
        "mcp": {"by": "id", "value": "email"},
        "test_hint": "test_email",
    },
    {
        "id": "phone",
        "label": "Phone label and value",
        "locator_key": "phone",
        "mcp": {"by": "id", "value": "phone"},
        "test_hint": "test_phone",
    },
    {
        "id": "experience_title",
        "label": "Experience section title",
        "locator_key": "experience_container",
        "mcp": {"by": "id", "value": "experience_container"},
        "test_hint": "test_experience_section_title",
    },
    {
        "id": "experience_companies",
        "label": "Experience company entries (scroll)",
        "locator_key": "experience_container",
        "mcp": {"by": "id", "value": "experience_container"},
        "test_hint": "test_experience_companies",
    },
    {
        "id": "summary",
        "label": "Summary block",
        "locator_key": "summary",
        "mcp": {"by": "id", "value": "summary"},
        "test_hint": "test_summary",
    },
    {
        "id": "send_message",
        "label": "Send message CTA text",
        "locator_key": "send_message_text",
        "mcp": {"by": "id", "value": "sendMessageText"},
        "test_hint": "test_send_message",
    },
]


def run_pytest(
    base_url: str, browser: str, junit_path: Path, extra_args: list[str]
) -> int:
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
        *extra_args,
    ]
    print(f"[discoverer] running: {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=ROOT).returncode


def list_test_methods(tests_dir: Path = ROOT / "tests") -> list[dict[str, str]]:
    methods: list[dict[str, str]] = []
    for path in sorted(tests_dir.glob("test_*.py")):
        source = path.read_text()
        for match in re.finditer(r"def (test_\w+)\(", source):
            methods.append(
                {
                    "name": match.group(1),
                    "file": str(path.relative_to(ROOT)),
                    "module": path.stem,
                }
            )
    return methods


def list_locator_keys() -> list[str]:
    locators_file = ROOT / "pages" / "locators.py"
    if not locators_file.exists():
        return []
    keys = re.findall(r'"(\w+)":\s*\(', locators_file.read_text())
    return sorted(set(keys))


def covered_test_hints(methods: list[dict[str, str]]) -> set[str]:
    return {m["name"] for m in methods}


def find_gaps(methods: list[dict[str, str]]) -> list[dict]:
    covered = covered_test_hints(methods)
    gaps = []
    for area in KNOWN_PAGE_AREAS:
        if area["test_hint"] not in covered:
            gaps.append({**area, "status": "missing_test"})
    return gaps


def mcp_session_steps(base_url: str, browser: str) -> list[dict]:
    return [
        {
            "tool": "start_browser",
            "args": {"browser": browser, "options": {"headless": True}},
        },
        {"tool": "navigate", "args": {"url": base_url}},
        {"tool": "accessibility://current", "note": "Full page tree"},
        {
            "tool": "execute_script",
            "script": (
                "return [...document.querySelectorAll('[id]')].map(el => ({"
                "id: el.id, tag: el.tagName, visible: el.offsetParent !== null}))"
            ),
            "note": "Collect all elements with id attributes",
        },
        {
            "tool": "execute_script",
            "script": (
                "window.scrollTo(0, document.body.scrollHeight); "
                "return document.body.scrollHeight"
            ),
            "note": "Scroll to bottom for lazy-loaded sections",
        },
        {"tool": "accessibility://current", "note": "Re-read after scroll"},
        {"tool": "close_session"},
    ]


def build_discovery_manifest(base_url: str, browser: str) -> dict:
    methods = list_test_methods()
    locator_keys = list_locator_keys()
    gaps = find_gaps(methods)

    return {
        "mcp_server": MCP_SERVER,
        "mcp_package": "@angiejones/mcp-selenium",
        "base_url": base_url,
        "browser": browser,
        "skill_reference": ".cursor/skills/ui-test-discoverer/SKILL.md",
        "existing_tests": methods,
        "locator_keys": locator_keys,
        "known_areas": KNOWN_PAGE_AREAS,
        "gaps_from_inventory": gaps,
        "session": mcp_session_steps(base_url, browser),
        "agent_instructions": [
            (
                "Read Selenium MCP tool schemas for server 'selenium' "
                "before calling tools."
            ),
            (
                "Run session steps; note any visible id/role not covered "
                "by existing_tests."
            ),
            "Compare live page with pages/locators.py and config/test_data.json.",
            (
                "For each gap: add locator, page object method, "
                "test_data entry, and test."
            ),
            "Follow POM style in tests/test_home.py (pytest_check, test_data fixture).",
            "Run: python scripts/ui_test_discoverer.py verify --push-pr --merge-pr",
            "If nothing new to test, exit 0 without opening a PR.",
        ],
    }


def save_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))


def run_git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)


def is_discover_path(path: str) -> bool:
    normalized = path.strip().strip('"')
    return any(
        normalized.startswith(prefix) or normalized == prefix.rstrip("/")
        for prefix in DISCOVER_COMMIT_PATHS
    )


def changed_discover_files() -> list[str]:
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
        if is_discover_path(path):
            files.append(path)
    return sorted(set(files))


def default_base_branch() -> str:
    env_branch = os.getenv("GITHUB_BASE_REF") or os.getenv("DISCOVERER_BASE_BRANCH")
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


def format_discover_pr_body(base_url: str, files: list[str]) -> str:
    bullets = "\n".join(f"- `{path}`" for path in files) or "- New UI tests"
    return f"""## Discover UI tests

Automated discovery found page areas without coverage. \
This PR adds tests and page objects.

**Target URL:** `{base_url}`

**Changed files:**
{bullets}

**Verification:** `pytest` passed after discovery.

---
_Auto-generated by `scripts/ui_test_discoverer.py`_
"""


def create_discover_pull_request(base_url: str) -> str | None:
    files = changed_discover_files()
    if not files:
        print("[discoverer] no discover-related file changes; skipping PR")
        return None

    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    if not token:
        print(
            "[discoverer] GH_TOKEN/GITHUB_TOKEN missing; cannot push branch or open PR"
        )
        return None

    if run_git("rev-parse", "--is-inside-work-tree").returncode != 0:
        print("[discoverer] not a git repository; skipping PR")
        return None

    ensure_git_identity()
    base_branch = default_base_branch()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    branch = f"discover/ui-tests-{timestamp}"

    checkout = run_git("checkout", "-b", branch)
    if checkout.returncode != 0:
        print(f"[discoverer] git checkout failed: {checkout.stderr.strip()}")
        return None

    add = run_git("add", *files)
    if add.returncode != 0:
        print(f"[discoverer] git add failed: {add.stderr.strip()}")
        return None

    commit_message = (
        "test(ui): add discovered UI test coverage\n\n"
        f"Target URL: {base_url}\n"
        "Auto-generated by scripts/ui_test_discoverer.py."
    )
    commit = run_git("commit", "-m", commit_message)
    if commit.returncode != 0:
        print(f"[discoverer] git commit failed: {commit.stderr.strip()}")
        return None

    push = run_git("push", "-u", "origin", branch)
    if push.returncode != 0:
        print(f"[discoverer] git push failed: {push.stderr.strip()}")
        return None

    title = f"test(ui): add discovered coverage ({timestamp})"
    body = format_discover_pr_body(base_url, files)
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
        print(f"[discoverer] gh pr create failed: {create.stderr.strip()}")
        return None

    pr_url = create.stdout.strip()
    print(f"[discoverer] opened PR: {pr_url}")
    return pr_url


def merge_pull_request(pr_url: str) -> bool:
    merge = subprocess.run(
        ["gh", "pr", "merge", pr_url, "--squash", "--delete-branch"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if merge.returncode != 0:
        print(f"[discoverer] gh pr merge failed: {merge.stderr.strip()}")
        return False
    print(f"[discoverer] merged PR: {pr_url}")
    return True


def should_push_pr(args: argparse.Namespace) -> bool:
    if args.no_push_pr:
        return False
    if args.push_pr:
        return True
    return os.getenv("DISCOVERER_PUSH_PR", "").lower() == "true"


def should_merge_pr(args: argparse.Namespace) -> bool:
    if args.no_merge_pr:
        return False
    if args.merge_pr:
        return True
    return os.getenv("DISCOVERER_MERGE_PR", "").lower() == "true"


def cmd_inventory(args: argparse.Namespace) -> int:
    methods = list_test_methods()
    gaps = find_gaps(methods)
    inventory = {
        "tests": methods,
        "locator_keys": list_locator_keys(),
        "gaps": gaps,
    }
    save_json(INVENTORY_JSON, inventory)

    manifest = build_discovery_manifest(args.base_url, args.browser)
    save_json(MANIFEST_JSON, manifest)

    print("[discoverer] inventory written:")
    print(f"  - {INVENTORY_JSON}")
    print(f"  - {MANIFEST_JSON}")
    print(f"[discoverer] {len(methods)} existing test(s), {len(gaps)} known gap(s)")
    if gaps:
        for gap in gaps:
            print(f"  - missing: {gap['test_hint']} ({gap['label']})")
    print(
        "[discoverer] use Selenium MCP per discovery_manifest.json, "
        "then implement tests"
    )
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    extra = [args.pytest_target] if args.pytest_target else []
    exit_code = run_pytest(args.base_url, args.browser, Path(args.junit), extra)
    if exit_code != 0:
        print("[discoverer] pytest failed; fix tests before opening PR")
        return exit_code

    if not changed_discover_files():
        print("[discoverer] tests passed; no file changes to commit")
        return 0

    if not should_push_pr(args):
        print("[discoverer] tests passed; push-pr not requested")
        return 0

    pr_url = create_discover_pull_request(args.base_url)
    if not pr_url:
        return 1

    if should_merge_pr(args) and not merge_pull_request(pr_url):
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="UI test discoverer")
    parser.add_argument(
        "--base-url",
        "--base_url",
        dest="base_url",
        default="https://www.serhatozdursun.com",
    )
    parser.add_argument("--browser", default="chrome")
    parser.add_argument("--junit", default=str(JUNIT_DEFAULT))
    parser.add_argument(
        "--pytest-target",
        default="",
        help="Optional pytest node id or path (default: full suite)",
    )
    parser.add_argument("--push-pr", action="store_true")
    parser.add_argument("--no-push-pr", action="store_true")
    parser.add_argument("--merge-pr", action="store_true")
    parser.add_argument("--no-merge-pr", action="store_true")

    sub = parser.add_subparsers(dest="command")
    sub.add_parser("inventory", help="Write test inventory and discovery manifest")
    sub.add_parser("verify", help="Run pytest and optionally open/merge PR")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "inventory":
        return cmd_inventory(args)
    if args.command == "verify":
        return cmd_verify(args)

    return cmd_inventory(args)


if __name__ == "__main__":
    raise SystemExit(main())
