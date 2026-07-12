#!/usr/bin/env python3
"""
Auto-update existing entries — refresh GitHub stats, check versions, rebuild index.

Usage: python scripts/auto_update.py [--full]

Requires: GITHUB_TOKEN env var
"""

import json, os, sys, time, re, glob, subprocess
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

REPO_ROOT = Path(__file__).resolve().parent.parent
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
HEADERS = {'User-Agent': 'DeveloperHub/1.0'}
if GITHUB_TOKEN:
    HEADERS['Authorization'] = f'Bearer {GITHUB_TOKEN}'

CATEGORIES = {
    "ai", "android", "api", "backend", "frontend", "database", "cloud",
    "security", "languages", "frameworks", "libraries", "tools",
    "operating-systems", "linux", "windows", "macos", "network",
    "devops", "containers", "firmware", "embedded", "iot",
    "game-development", "mobile", "desktop", "web", "blockchain",
    "machine-learning", "robotics"
}

def gh_api(path):
    url = f"https://api.github.com{path}"
    req = Request(url, headers=HEADERS)
    try:
        with urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except HTTPError as e:
        if e.code == 403:
            return None
        if e.code == 404:
            return None
        return None
    except:
        return None

def update_entry(entry, info, gh_url):
    """Update entry fields with fresh GitHub data."""
    entry['last_checked'] = time.strftime('%Y-%m-%d')
    
    # Update repository stats
    stats = {
        'stars': info.get('stargazers_count', 0),
        'forks': info.get('forks_count', 0),
        'open_issues': info.get('open_issues_count', 0),
        'watchers': info.get('subscribers_count', 0),
    }
    
    # Only update if we got valid data
    if stats['stars'] > 0:
        # Update popularity based on stars
        stars = stats['stars']
        if stars >= 10000: entry['popularity'] = 10
        elif stars >= 5000: entry['popularity'] = 9
        elif stars >= 1000: entry['popularity'] = 8
        elif stars >= 500: entry['popularity'] = 7
        elif stars >= 100: entry['popularity'] = 6
        
        # Update programming_languages from GitHub language
        lang = info.get('language')
        if lang:
            langs = entry.get('programming_languages', [])
            if langs == ['Generic'] or not langs:
                entry['programming_languages'] = [lang]
        
        # Update license
        lic = info.get('license')
        if lic and lic.get('spdx_id'):
            entry['license'] = lic['spdx_id']
        
        # Update archived status
        if info.get('archived'):
            entry['archived'] = True
        
        # Topics -> tags
        topics = info.get('topics', [])
        if topics:
            existing_tags = set(t.lower() for t in entry.get('tags', []))
            for topic in topics:
                if topic.lower() not in existing_tags:
                    entry.setdefault('tags', []).append(topic)
        
        # Update description if entry has placeholder
        desc = info.get('description')
        if desc and (not entry.get('description') or len(entry.get('description','')) < 10):
            entry['description'] = desc[:200]
        
        # Save stats
        entry['repository_statistics'] = stats
        entry['last_updated'] = time.strftime('%Y-%m-%d')
        
        # Check if repo has pre-built binaries (releases with assets)
        try:
            rel_url = f'/repos/{match.group(1)}/releases/latest'
            rel_data = gh_api(rel_url)
            if rel_data and rel_data.get('assets'):
                entry['has_binaries'] = True
        except:
            pass
        
        return True
    return False

def main():
    full = '--full' in sys.argv
    
    print("=== Developer Hub - Auto Update Existing Entries ===\n")
    
    updated = 0
    skipped = 0
    errors = 0
    
    for f in sorted(glob.glob(str(REPO_ROOT / '*/*.json'))):
        fpath = Path(f)
        if fpath.parent.name not in CATEGORIES:
            continue
        
        with open(f) as fh:
            entry = json.load(fh)
        
        gh_url = entry.get('github_repository', '')
        name = entry.get('name', '?')
        
        # Skip placeholder entries
        if 'example.com' in gh_url or 'example/' in gh_url:
            skipped += 1
            continue
        
        # Skip if recently checked (within 7 days) and not full mode
        last_check = entry.get('last_checked', '')
        if not full and last_check:
            try:
                check_date = time.mktime(time.strptime(last_check, '%Y-%m-%d'))
                days_since = (time.time() - check_date) / 86400
                if days_since < 7:
                    skipped += 1
                    continue
            except:
                pass
        
        # Get GitHub repo info
        match = re.search(r'github\.com/([^/]+/[^/]+?)(?:/|$)', gh_url)
        if not match:
            skipped += 1
            continue
        
        repo_path = match.group(1)
        info = gh_api(f'/repos/{repo_path}')
        
        if not info:
            print(f"  ❌ {name} — could not fetch")
            errors += 1
            continue
        
        success = update_entry(entry, info, gh_url)
        if success:
            with open(f, 'w') as fh:
                json.dump(entry, fh, indent=2)
            print(f"  ✅ {name} — stars: {entry['repository_statistics']['stars']}")
            updated += 1
        else:
            print(f"  ⚠️  {name} — no update needed")
            skipped += 1
        
        time.sleep(0.3)  # Rate limiting
    
    # Always rebuild index after updates
    print(f"\n🔄 Rebuilding search index...")
    subprocess.run([sys.executable, str(REPO_ROOT / 'scripts' / 'build_index.py')], cwd=str(REPO_ROOT))
    
    print(f"\n=== Done ===")
    print(f"Updated: {updated}")
    print(f"Skipped: {skipped}")
    print(f"Errors: {errors}")

if __name__ == '__main__':
    main()
