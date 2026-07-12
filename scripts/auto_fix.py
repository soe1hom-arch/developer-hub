#!/usr/bin/env python3
"""
Auto-fix placeholder entries — finds real GitHub repos from official websites.

Usage: python scripts/auto_fix.py [--dry-run]

Requires: GITHUB_TOKEN env var for GitHub API (rate limit without it is low)
"""

import json, os, sys, time, re, glob
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
        if e.code == 403 and 'rate' in str(e.read()):
            print(f"  ⚠️  GitHub API rate limited")
        return None
    except Exception as e:
        return None

def search_github_repo(name, website):
    """Try to find the GitHub repo for a project."""
    # Strategy 1: Search by website URL
    if website:
        domain = re.sub(r'https?://(www\.)?', '', website).split('/')[0]
        # Strip TLD for search
        parts = domain.split('.')
        if len(parts) >= 2:
            org_name = parts[-2]  # e.g. 'assemblyai' from 'assemblyai.com'
            # Try common GitHub org patterns
            for candidate in [org_name, org_name.replace('-',''), org_name.lower()]:
                r = gh_api(f'/orgs/{candidate}')
                if r and 'login' in r:
                    return f"https://github.com/{r['login']}"
    
    # Strategy 2: Search GitHub by name
    safe_name = re.sub(r'[^a-zA-Z0-9 ]', '', name).strip()
    if safe_name:
        q = safe_name.replace(' ', '+')
        r = gh_api(f'/search/repositories?q={q}&sort=stars&per_page=5')
        if r and r.get('items'):
            for item in r['items']:
                if not item.get('fork'):
                    return item['html_url']
    
    return None

def get_repo_info(github_url):
    """Get repo info from GitHub API."""
    match = re.search(r'github\.com/([^/]+/[^/]+?)(?:/|$)', github_url)
    if not match:
        return None
    full_name = match.group(1)
    data = gh_api(f'/repos/{full_name}')
    if not data:
        return None
    # Get languages
    lang_data = gh_api(f'/repos/{full_name}/languages')
    languages = list(lang_data.keys())[:5] if lang_data else []
    # Get topics
    topics = data.get('topics', [])
    return {
        'stars': data.get('stargazers_count', 0),
        'forks': data.get('forks_count', 0),
        'open_issues': data.get('open_issues_count', 0),
        'watchers': data.get('subscribers_count', 0),
        'language': data.get('language'),
        'languages': languages,
        'topics': topics,
        'description': data.get('description', ''),
        'license': data.get('license', {}).get('spdx_id') if data.get('license') else None,
        'archived': data.get('archived', False),
    }

def needs_fix(entry):
    gh = entry.get('github_repository', '')
    return 'example.com' in gh or 'example/' in gh

def is_placeholder(entry):
    return needs_fix(entry)

def fix_entry(entry, dry_run=False):
    name = entry.get('name', '?')
    website = entry.get('official_website', '')
    print(f"\n  🔍 {name}")
    
    # Find real GitHub repo
    gh_url = search_github_repo(name, website)
    if not gh_url:
        print(f"     ❌ Could not find GitHub repo")
        return False
    
    print(f"     ✅ Found: {gh_url}")
    
    if dry_run:
        return True
    
    # Update GitHub URL
    entry['github_repository'] = gh_url
    
    # Get repo info
    info = get_repo_info(gh_url)
    if info:
        # Update programming_languages
        if info['languages']:
            entry['programming_languages'] = info['languages']
        elif info['language']:
            entry['programming_languages'] = [info['language']]
        
        # Update popularity based on stars
        stars = info['stars']
        if stars >= 10000:
            entry['popularity'] = 10
        elif stars >= 5000:
            entry['popularity'] = 9
        elif stars >= 1000:
            entry['popularity'] = 8
        elif stars >= 500:
            entry['popularity'] = 7
        elif stars >= 100:
            entry['popularity'] = 6
        else:
            entry['popularity'] = 5
        
        # Update repository stats
        entry['repository_statistics'] = {
            'stars': info['stars'],
            'forks': info['forks'],
            'open_issues': info['open_issues'],
            'watchers': info['watchers'],
        }
        
        # Update license if available
        if info['license']:
            entry['license'] = info['license']
        
        # Update archived status
        if info['archived']:
            entry['archived'] = True
        
        # Add topics as tags
        if info['topics']:
            existing_tags = set(t.lower() for t in entry.get('tags', []))
            for topic in info['topics']:
                if topic.lower() not in existing_tags:
                    entry.setdefault('tags', []).append(topic)
    
    # Update timestamps
    entry['last_checked'] = time.strftime('%Y-%m-%d')
    entry['last_updated'] = time.strftime('%Y-%m-%d')
    
    return True

def main():
    dry_run = '--dry-run' in sys.argv
    
    print("=== Developer Hub - Auto Fix Placeholder Entries ===\n")
    
    fixed = 0
    failed = 0
    files_processed = 0
    
    for f in sorted(glob.glob(str(REPO_ROOT / '*/*.json'))):
        fpath = Path(f)
        if fpath.parent.name not in CATEGORIES:
            continue
        
        with open(f) as fh:
            entry = json.load(fh)
        
        if not is_placeholder(entry):
            continue
        
        files_processed += 1
        success = fix_entry(entry, dry_run)
        
        if success and not dry_run:
            with open(f, 'w') as fh:
                json.dump(entry, fh, indent=2)
            fixed += 1
        elif success and dry_run:
            fixed += 1
        else:
            failed += 1
        
        # Rate limiting: wait between requests
        time.sleep(0.5)
    
    print(f"\n=== Done ===")
    print(f"Processed: {files_processed}")
    print(f"Fixed: {fixed}")
    print(f"Failed: {failed}")
    if dry_run:
        print(f"(dry run - no files were modified)")

if __name__ == '__main__':
    main()
