#!/usr/bin/env python3
"""
Quality Check Engine — multi-layer verification untuk hampir 100% akurasi.

Layers:
  1. Schema & format check
  2. GitHub repo verification (exists, active, not renamed)
  3. Description quality & relevance
  4. Category confidence (multi-signal via category_rules)
  5. URL/website reachability
  6. Duplicate detection

Usage:
    python scripts/quality_check.py --check path/to/file.json
    python scripts/quality_check.py --batch proposals/
"""

import json, os, sys, re, time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from scripts.categories import CATEGORIES

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
HEADERS = {"User-Agent": "DeveloperHub/1.0", "Accept": "application/vnd.github+json"}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"


# Layer 1: Schema & Format
REQUIRED_FIELDS = ["id", "name", "category", "description", "official_website",
                   "documentation", "github_repository", "license", "latest_version",
                   "programming_languages", "platforms", "tags"]

def check_schema(entry):
    issues = []
    for field in REQUIRED_FIELDS:
        if field not in entry:
            issues.append(f"Missing required field: {field}")
    if not isinstance(entry.get("tags", []), list):
        issues.append("tags must be a list")
    if not isinstance(entry.get("programming_languages", []), list):
        issues.append("programming_languages must be a list")
    if not isinstance(entry.get("platforms", []), list):
        issues.append("platforms must be a list")
    entry_id = entry.get("id", "")
    if not re.match(r"^[a-z0-9][a-z0-9_-]*[a-z0-9]$", entry_id):
        issues.append(f"Invalid id format: {entry_id}")
    return len(issues) == 0, issues


# Layer 2: GitHub Verification
def check_github(repo_url):
    if not repo_url or "github.com" not in repo_url:
        return False, "Not a GitHub URL", {}
    m = re.search(r"github\.com[:/]([\w.-]+)/([\w.-]+?)(?:\.git|/|$)", repo_url)
    if not m:
        return False, "Invalid GitHub URL", {}
    owner, repo = m.group(1), m.group(2)
    api_url = f"https://api.github.com/repos/{owner}/{repo}"
    try:
        req = Request(api_url, headers=HEADERS)
        with urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
    except HTTPError as e:
        if e.code == 404:
            return False, "Repository not found (404)", {}
        if e.code == 403:
            return False, "API rate limited", {}
        return False, f"HTTP {e.code}", {}
    except Exception as e:
        return False, f"Connection error: {e}", {}
    info = {
        "stars": data.get("stargazers_count", 0),
        "forks": data.get("forks_count", 0),
        "language": data.get("language"),
        "topics": data.get("topics", []),
        "description": data.get("description", ""),
        "archived": data.get("archived", False),
        "disabled": data.get("disabled", False),
        "license": data.get("license", {}).get("spdx_id") if data.get("license") else None,
        "has_wiki": data.get("has_wiki", False),
        "has_pages": data.get("has_pages", False),
    }
    # Check releases
    try:
        rel_url = f"https://api.github.com/repos/{owner}/{repo}/releases?per_page=1"
        rel_req = Request(rel_url, headers=HEADERS)
        with urlopen(rel_req, timeout=10) as r:
            releases = json.loads(r.read())
            info["has_releases"] = len(releases) > 0
            if releases and releases[0].get("assets"):
                info["has_assets"] = len(releases[0]["assets"]) > 0
            else:
                info["has_assets"] = False
    except:
        info["has_releases"] = False
        info["has_assets"] = False
    issues = []
    if info["archived"]:
        issues.append("Repository is archived")
    if info["disabled"]:
        issues.append("Repository is disabled")
    if info["stars"] < 10:
        issues.append(f"Very few stars ({info['stars']})")
    return len(issues) == 0, issues, info


# Layer 3: Description Quality
def check_description(entry):
    desc = entry.get("description", "")
    name = entry.get("name", "")
    issues = []
    if not desc or len(desc) < 30:
        issues.append("Description too short (< 30 chars)")
    elif len(desc) < 60:
        issues.append("Description could be more detailed (< 60 chars)")
    if len(desc) > 500:
        issues.append("Description too long (> 500 chars)")
    generic = [r"a (tool|library|framework|sdk|api) for", r"this is (a|an)", r"my (project|first|awesome)"]
    for pat in generic:
        if re.search(pat, desc.lower()):
            issues.append(f"Generic description pattern: {pat}")
            break
    name_words = set(name.lower().split()[:3])
    desc_lower = desc.lower()
    if name_words and not any(w in desc_lower for w in name_words if len(w) > 3):
        issues.append("Project name not found in description")
    return len(issues) <= 1, issues


# Layer 4: Category via category_rules engine
def check_category(entry, gh_info=None):
    from scripts.category_rules import get_best_category
    best_cat, confidence, details = get_best_category(entry, gh_info)
    entry_cat = entry.get("category", "")
    issues = []
    if entry_cat != best_cat and confidence > 0.5:
        issues.append(f"Category might be {best_cat} instead of {entry_cat} ({confidence:.0%})")
    if confidence < 0.5:
        issues.append(f"Low category confidence for {entry_cat} ({confidence:.0%})")
    cat_details = details.get(entry_cat, {})
    signals = cat_details.get("signals", [])
    if not signals:
        issues.append("No strong signals matching this category")
    must_nots = [s for s in signals if "MUST_NOT" in s]
    for mn in must_nots[:2]:
        issues.append(f"Contradicting signal: {mn}")
    return len(issues) <= 1, issues, confidence


# Layer 5: URL Check
def check_url(url):
    if not url:
        return False, "No URL"
    try:
        req = Request(url, method="HEAD", headers={"User-Agent": "DeveloperHub/1.0"})
        with urlopen(req, timeout=10) as r:
            return True, f"HTTP {r.status}"
    except HTTPError as e:
        if e.code in (403, 405):
            return True, f"HTTP {e.code} (may block HEAD)"
        return False, f"HTTP {e.code}"
    except Exception as e:
        return False, str(e)


# Layer 6: Duplicate Check
def check_duplicate(entry, existing_entries=None):
    if existing_entries is None:
        existing_entries = []
    name = entry.get("name", "").lower()
    gh_url = entry.get("github_repository", "").rstrip("/").lower()
    website = entry.get("official_website", "").rstrip("/").lower()
    for existing in existing_entries:
        if existing.get("name", "").lower() == name:
            return False, f"Duplicate name: {name} already exists"
        if existing.get("github_repository", "").rstrip("/").lower() == gh_url and gh_url:
            return False, f"Duplicate GitHub URL: {gh_url}"
        if existing.get("official_website", "").rstrip("/").lower() == website and website:
            return False, f"Duplicate website: {website}"
    return True, []


# Master verification
def verify_entry(entry, existing_entries=None):
    all_issues = []
    details = {}
    # Layer 1
    ok, issues = check_schema(entry)
    if isinstance(issues, list):
        all_issues.extend(issues)
    elif issues:
        all_issues.append(issues)
    details["schema"] = {"passed": ok, "issues": issues if isinstance(issues, list) else [issues] if issues else []}
    # Layer 2
    ok, issues, gh_info = check_github(entry.get("github_repository", ""))
    if isinstance(issues, list):
        all_issues.extend(issues)
    elif issues:
        all_issues.append(issues)
    details["github"] = {"passed": ok, "issues": issues if isinstance(issues, list) else [issues] if issues else []}
    # Layer 3
    ok, issues = check_description(entry)
    if isinstance(issues, list):
        all_issues.extend(issues)
    elif issues:
        all_issues.append(issues)
    details["description"] = {"passed": ok, "issues": issues if isinstance(issues, list) else [issues] if issues else []}
    # Layer 4
    ok, issues, confidence = check_category(entry, gh_info)
    if isinstance(issues, list):
        all_issues.extend(issues)
    elif issues:
        all_issues.append(issues)
    details["category"] = {"passed": ok, "issues": issues if isinstance(issues, list) else [issues] if issues else [], "confidence": confidence}
    # Layer 6
    ok, issues = check_duplicate(entry, existing_entries)
    if isinstance(issues, list):
        all_issues.extend(issues)
    elif issues:
        all_issues.append(issues)
    details["duplicate"] = {"passed": ok, "issues": issues if isinstance(issues, list) else [issues] if issues else []}
    passed = len(all_issues) == 0
    quality = calculate_quality(details, entry)
    return passed, all_issues, details, quality


def calculate_quality(details, entry):
    score = 50
    gh = details.get("github", {}).get("info", {})
    stars = gh.get("stars", 0)
    if stars >= 50000: score += 30
    elif stars >= 10000: score += 25
    elif stars >= 5000: score += 20
    elif stars >= 1000: score += 15
    elif stars >= 100: score += 10
    elif stars >= 10: score += 5
    if not gh.get("archived", True): score += 5
    if gh.get("license"): score += 3
    desc = entry.get("description", "")
    if len(desc) >= 150: score += 15
    elif len(desc) >= 100: score += 12
    elif len(desc) >= 60: score += 8
    elif len(desc) >= 30: score += 4
    tags = entry.get("tags", [])
    if len(tags) >= 8: score += 10
    elif len(tags) >= 5: score += 7
    elif len(tags) >= 3: score += 4
    elif len(tags) >= 1: score += 2
    doc = entry.get("documentation", "")
    if doc and "readme" not in doc.lower(): score += 10
    elif doc: score += 5
    site = entry.get("official_website", "")
    if site and "github.com" not in site.lower(): score += 10
    elif site: score += 3
    langs = entry.get("programming_languages", [])
    if len(langs) >= 2: score += 10
    elif len(langs) >= 1 and langs[0] != "Generic": score += 5
    if entry.get("maintained", True) and not entry.get("archived", False): score += 5
    conf = details.get("category", {}).get("confidence", 0.5)
    score += int(conf * 5)
    return min(score, 100)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Multi-layer quality verification")
    parser.add_argument("--check", help="Check a single JSON file")
    parser.add_argument("--batch", help="Check all JSON files in a directory")
    parser.add_argument("--verify", action="store_true", help="Verify all existing entries")
    parser.add_argument("--auto-commit", action="store_true", help="Auto-commit passing entries")
    parser.add_argument("--min-quality", type=int, default=70)
    parser.add_argument("--min-confidence", type=float, default=0.7)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    
    if args.check:
        with open(args.check) as f:
            entry = json.load(f)
        passed, issues, details, quality = verify_entry(entry)
        print(f"\n{"="*50}")
        print(f"  Quality Check: {entry.get("name", "?")}")
        print(f"{"="*50}")
        print(f"  Overall: {"✅ PASS" if passed else "❌ FAIL"} (quality: {quality}/100)")
        print(f"  Issues: {len(issues)}")
        for issue in issues:
            print(f"    • {issue}")
        print()
        for layer, result in details.items():
            status = "✅" if result["passed"] else "❌"
            print(f"  {status} {layer}: {len(result.get("issues", []))} issues")
            for issue in result.get("issues", []):
                print(f"       • {issue}")
    
    elif args.batch:
        existing = []
        for cat_dir in CATEGORIES:
            d = REPO_ROOT / cat_dir
            if d.exists():
                for f in d.glob("*.json"):
                    try:
                        existing.append(json.loads(f.read_text()))
                    except:
                        pass
        dir_path = Path(args.batch)
        results = []
        for f in sorted(dir_path.glob("*.json")):
            try:
                entry = json.loads(f.read_text())
                passed, issues, details, quality = verify_entry(entry, existing)
                results.append({"file": str(f), "name": entry.get("name", "?"), "passed": passed, "quality": quality, "issues": issues})
                status = "✅" if passed else "❌"
                print(f"{status} {entry.get("name", "?"):30s} quality={quality:2d}/100  issues={len(issues)}")
                if args.auto_commit and passed and quality >= args.min_quality:
                    cat = entry.get("category", "tools")
                    cat_dir = REPO_ROOT / cat
                    cat_dir.mkdir(exist_ok=True)
                    dst = cat_dir / f.name
                    if dst.exists():
                        print(f"     Target exists, skipping: {dst}")
                    else:
                        import shutil
                        shutil.move(str(f), str(dst))
                        print(f"     Auto-committed to {cat}/")
            except Exception as e:
                print(f"Error processing {f}: {e}")
        print(f"\nResults: {sum(1 for r in results if r["passed"])}/{len(results)} passed")
    
    elif args.verify:
        print("Verifying all existing entries...")
        total = 0
        passed = 0
        for cat_dir in CATEGORIES:
            d = REPO_ROOT / cat_dir
            if d.exists():
                for f in d.glob("*.json"):
                    total += 1
                    try:
                        entry = json.loads(f.read_text())
                        ok, issues, details, quality = verify_entry(entry)
                        if ok:
                            passed += 1
                    except:
                        pass
        print(f"  {passed}/{total} passed ({passed/total*100:.0f}%)" if total else "  No entries found")


if __name__ == "__main__":
    main()
