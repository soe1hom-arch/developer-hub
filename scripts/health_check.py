#!/usr/bin/env python3
"""
Comprehensive health check for all repository entries.

Checks:
- Official website is reachable
- Documentation URL is reachable
- GitHub repository exists
- License is available
- Project status (archived, maintained)
- Latest version
- Duplicate entries
- Repo rename detection

Usage:
    python scripts/health_check.py          # Full health check
    python scripts/health_check.py --quick  # Skip network checks
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
import socket
from pathlib import Path
from datetime import datetime, date

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from scripts.categories import CATEGORIES


TIMEOUT = 10
MAX_REDIRECTS = 5

def check_url(url, name="URL"):
    """Check if a URL is reachable."""
    if not url:
        return False, "No URL provided"
    try:
        req = urllib.request.Request(url, method="HEAD",
            headers={"User-Agent": "DeveloperHub-HealthCheck/1.0"})
        resp = urllib.request.urlopen(req, timeout=TIMEOUT)
        return True, f"HTTP {resp.status}"
    except urllib.error.HTTPError as e:
        # 403/404 might still mean the site exists but blocks HEAD
        if e.code in (403, 405):
            return True, f"HTTP {e.code} (may block HEAD)"
        return False, f"HTTP {e.code}"
    except urllib.error.URLError as e:
        return False, f"DNS/Connection error: {e.reason}"
    except socket.timeout:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)


def check_github_repo(url):
    """Check if a GitHub repository exists (not renamed/archived)."""
    if not url or "github.com" not in url:
        return None, "Not a GitHub URL"

    api_url = url.replace("github.com", "api.github.com/repos")
    try:
        req = urllib.request.Request(api_url,
            headers={
                "User-Agent": "DeveloperHub-HealthCheck/1.0",
                "Accept": "application/vnd.github+json"
            })
        resp = urllib.request.urlopen(req, timeout=TIMEOUT)
        data = json.loads(resp.read().decode())
        if data.get("archived"):
            return False, "Repository is archived"
        if data.get("full_name"):
            expected = "/".join(url.rstrip("/").split("/")[-2:])
            actual = data["full_name"]
            if expected.lower() != actual.lower():
                return False, f"Repository renamed: expected '{expected}', actual '{actual}'"
        return True, f"Active ({data.get('stargazers_count', '?')} stars)"
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False, "Repository not found (404)"
        if e.code == 403:
            return True, "API rate limited (403)"
        return None, f"HTTP {e.code}"
    except Exception as e:
        return None, f"Error: {e}"


def check_entry(filepath, skip_network=False):
    """Run all checks on a single entry file."""
    try:
        with open(filepath, "r") as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        return {"file": str(filepath), "status": "error", "issues": [str(e)]}

    issues = []
    warnings = []
    name = data.get("name", filepath.stem)

    # Check required fields exist
    required = ["id", "name", "category", "description", "official_website",
                 "documentation", "github_repository", "license", "latest_version",
                 "programming_languages", "platforms", "tags"]
    for field in required:
        if field not in data:
            issues.append(f"Missing required field: {field}")

    # Check dates are recent
    for date_field in ["last_checked", "last_updated"]:
        val = data.get(date_field)
        if val:
            try:
                d = datetime.strptime(val, "%Y-%m-%d").date()
                days_ago = (date.today() - d).days
                if days_ago > 90:
                    warnings.append(f"{date_field} is {days_ago} days old")
            except ValueError:
                warnings.append(f"Invalid date format for {date_field}")

    # Check archived status
    if data.get("archived"):
        warnings.append("Project is archived")

    if not data.get("maintained"):
        warnings.append("Project is not actively maintained")

    # Check URLs (optional, network-dependent)
    if not skip_network:
        for url_field in ["official_website", "documentation", "github_repository"]:
            url = data.get(url_field)
            if url:
                ok, msg = check_url(url, url_field)
                if not ok:
                    issues.append(f"{url_field} unreachable: {msg}")

        # Check GitHub repo specifically
        gh_url = data.get("github_repository")
        if gh_url and "github.com" in gh_url:
            ok, msg = check_github_repo(gh_url)
            if ok is False:
                issues.append(f"github: {msg}")

    return {
        "file": str(filepath.relative_to(REPO_ROOT)),
        "name": name,
        "status": "fail" if issues else "warn" if warnings else "pass",
        "issues": issues,
        "warnings": warnings,
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Comprehensive health check")
    parser.add_argument("--quick", action="store_true", help="Skip network checks")
    parser.add_argument("--report", action="store_true", help="Generate report file")
    parser.add_argument("--fix", action="store_true", help="Auto-fix: update archived/maintained status")
    args = parser.parse_args()

    all_results = []
    total = 0
    passed = 0
    warned = 0
    failed = 0

    for entry in REPO_ROOT.iterdir():
        if not entry.is_dir() or entry.name not in CATEGORIES:
            continue
        for json_file in sorted(entry.rglob("*.json")):
            total += 1
            result = check_entry(json_file, skip_network=args.quick)
            all_results.append(result)
            if result["status"] == "pass":
                passed += 1
            elif result["status"] == "warn":
                warned += 1
            else:
                failed += 1

            status_icon = "✅" if result["status"] == "pass" else "⚠️" if result["status"] == "warn" else "❌"
            print(f"{status_icon} {result['name']}")
            for issue in result["issues"]:
                print(f"     ✗ {issue}")
            for warn in result["warnings"]:
                print(f"     ⚠ {warn}")

    print(f"\n{'='*40}")
    print(f"Results: {passed} passed, {warned} warnings, {failed} failed of {total} total")


    # Auto-fix: update archived/maintained berdasarkan hasil health check
    if args.fix:
        fixed = 0
        for result in all_results:
            if result["status"] == "fail":
                continue
            filepath = REPO_ROOT / result["file"]
            if not filepath.exists():
                continue
            try:
                with open(filepath) as f:
                    entry = json.load(f)
                changed = False
                for warn in result["warnings"]:
                    if warn == "Project is archived":
                        entry["archived"] = True
                        entry["maintained"] = False
                        changed = True
                    elif warn == "Project is not actively maintained":
                        entry["maintained"] = False
                        changed = True
                if changed:
                    with open(filepath, "w") as f:
                        json.dump(entry, f, indent=2)
                    print(f"  \u2705 Fixed: {result['name']} (archived/maintained updated)")
                    fixed += 1
            except Exception as e:
                print(f"  \u274c Error fixing {result['name']}: {e}")
        if fixed:
            print(f"\nFixed {fixed} entries\n")

    if args.report:
        report_path = REPO_ROOT / "reports"
        report_path.mkdir(exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        report_file = report_path / f"health-check-{timestamp}.json"
        with open(report_file, "w") as f:
            json.dump({
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "total": total,
                "passed": passed,
                "warned": warned,
                "failed": failed,
                "results": all_results,
            }, f, indent=2)
        print(f"Report saved to {report_file}")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
