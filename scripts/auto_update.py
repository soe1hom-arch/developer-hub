#!/usr/bin/env python3
"""
Auto-update existing entries — refresh GitHub stats via batched GraphQL queries.

Usage:
    python scripts/auto_update.py                     # Update stale entries (>7 days)
    python scripts/auto_update.py --full              # Force update all entries
    python scripts/auto_update.py --dry-run           # Preview only

Requires: GITHUB_TOKEN env var
"""

import json, os, sys, time, re, subprocess
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from scripts.categories import CATEGORIES

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
HEADERS = {'User-Agent': 'DeveloperHub/1.0'}
if GITHUB_TOKEN:
    HEADERS['Authorization'] = f'Bearer {GITHUB_TOKEN}'

BATCH_SIZE = 50  # GitHub GraphQL can query up to 50 nodes per call
RATE_LIMIT_SLEEP = 2  # seconds between batches


def gh_graphql(query):
    """Call GitHub GraphQL API."""
    url = 'https://api.github.com/graphql'
    if not GITHUB_TOKEN:
        return None
    req = Request(url, method='POST', headers={
        'Authorization': f'Bearer {GITHUB_TOKEN}',
        'Content-Type': 'application/json',
    })
    try:
        with urlopen(req, data=json.dumps({'query': query}).encode(), timeout=30) as r:
            return json.loads(r.read())
    except HTTPError as e:
        body = e.read().decode()
        if e.code == 403 and 'rate' in body.lower():
            print(f"  ⏳ Rate limited. Waiting 60s...")
            time.sleep(60)
            return gh_graphql(query)
        if e.code == 401:
            print(f"  ❌ Bad GitHub token")
            return None
        print(f"  ⚠️  GraphQL error: {e.code}")
        return None
    except Exception as e:
        return None


def build_batch_query(entries_batch):
    """Build a GraphQL query for a batch of repos."""
    fragments = []
    for i, (fpath, entry) in enumerate(entries_batch):
        gh_url = entry.get('github_repository', '')
        m = re.search(r'github\.com/([^/]+/[^/]+?)(?:/|$)', gh_url)
        if not m:
            continue
        owner, repo = m.group(1).split('/')
        alias = f'repo{i}'
        fragments.append(f'''
      {alias}: repository(owner: "{owner}", name: "{repo}") {{
        nameWithOwner
        stargazerCount
        forkCount
        isArchived
        primaryLanguage {{ name }}
        licenseInfo {{ spdxId }}
        description
        repositoryTopics(first: 10) {{ nodes {{ topic {{ name }} }} }}
        latestRelease {{ tagName }}
      }}
        ''')
    
    if not fragments:
        return None
    
    return f'query {{ {",".join(fragments)} }}'


def update_entry(entry, data):
    """Update entry fields with fresh GitHub data from GraphQL."""
    entry['last_checked'] = time.strftime('%Y-%m-%d')
    
    stars = data.get('stargazerCount', 0)
    if stars == 0:
        return False  # No valid data
    
    # Stars-based popularity
    entry['repository_statistics'] = {
        'stars': stars,
        'forks': data.get('forkCount', 0),
        'open_issues': 0,
        'watchers': 0,
    }
    
    if stars >= 10000: entry['popularity'] = 10
    elif stars >= 5000: entry['popularity'] = 9
    elif stars >= 1000: entry['popularity'] = 8
    elif stars >= 500: entry['popularity'] = 7
    elif stars >= 100: entry['popularity'] = 6
    
    # Language
    lang = data.get('primaryLanguage')
    if lang and lang.get('name'):
        langs = entry.get('programming_languages', [])
        if langs == ['Generic'] or not langs:
            entry['programming_languages'] = [lang['name']]
    
    # License
    lic = data.get('licenseInfo')
    if lic and lic.get('spdxId'):
        entry['license'] = lic['spdxId']
    
    # Archived
    if data.get('isArchived'):
        entry['archived'] = True
        entry['maintained'] = False
    
    # Topics → tags
    topics = data.get('repositoryTopics', {}).get('nodes', [])
    if topics:
        existing_tags = set(t.lower() for t in entry.get('tags', []))
        for node in topics:
            tname = node.get('topic', {}).get('name', '')
            if tname and tname.lower() not in existing_tags:
                entry.setdefault('tags', []).append(tname)
    
    # Description
    desc = data.get('description')
    if desc and (not entry.get('description') or len(entry.get('description', '')) < 10):
        entry['description'] = desc[:200]
    
    # Latest version
    release = data.get('latestRelease')
    if release and release.get('tagName'):
        entry['latest_version'] = release['tagName']
    
    entry['last_updated'] = time.strftime('%Y-%m-%d')
    return True


def main():
    dry_run = '--dry-run' in sys.argv
    full = '--full' in sys.argv
    
    if not GITHUB_TOKEN:
        print("❌ GITHUB_TOKEN not set. Cannot update.")
        sys.exit(1)
    
    print(f"=== Auto-Update (GraphQL batches of {BATCH_SIZE}) ===\n")
    
    # Collect all entries
    all_entries = []
    for f in sorted(Path(REPO_ROOT).glob('*/*.json')):
        fpath = Path(f)
        if fpath.parent.name not in CATEGORIES:
            continue
        try:
            with open(f) as fh:
                entry = json.load(fh)
            gh_url = entry.get('github_repository', '')
            if 'example.com' in gh_url or 'example/' in gh_url:
                continue
            
            # Skip if checked within 7 days (unless --full)
            if not full:
                lc = entry.get('last_checked', '')
                if lc:
                    try:
                        days = (time.time() - time.mktime(time.strptime(lc, '%Y-%m-%d'))) / 86400
                        if days < 7:
                            continue
                    except:
                        pass
            
            if re.search(r'github\.com/([^/]+/[^/]+?)(?:/|$)', gh_url):
                all_entries.append((f, entry))
        except:
            continue
    
    total = len(all_entries)
    print(f"Entries to update: {total}\n")
    
    if dry_run:
        print("(dry run — no changes made)")
        return
    
    updated = 0
    errors = 0
    
    # Process in batches of BATCH_SIZE
    for batch_start in range(0, total, BATCH_SIZE):
        batch = all_entries[batch_start:batch_start + BATCH_SIZE]
        query = build_batch_query(batch)
        if not query:
            continue
        
        print(f"  Batch {batch_start//BATCH_SIZE + 1}/{(total-1)//BATCH_SIZE + 1} ({len(batch)} repos)...")
        result = gh_graphql(query)
        
        if not result or 'data' not in result:
            print(f"    ⚠️  Batch failed, skipping")
            errors += len(batch)
            time.sleep(RATE_LIMIT_SLEEP)
            continue
        
        data = result['data']
        for i, (fpath, entry) in enumerate(batch):
            key = f'repo{i}'
            repo_data = data.get(key)
            if not repo_data:
                continue
            
            name = entry.get('name', '?')
            success = update_entry(entry, repo_data)
            
            if success:
                with open(fpath, 'w') as fh:
                    json.dump(entry, fh, indent=2)
                stars = entry.get('repository_statistics', {}).get('stars', 0)
                print(f"    ✅ {name} ⭐{stars}")
                updated += 1
            else:
                print(f"    ⚠️  {name} — no data")
                errors += 1
        
        time.sleep(RATE_LIMIT_SLEEP)
    
    # Rebuild index
    print(f"\n🔄 Rebuilding search index...")
    subprocess.run([sys.executable, str(REPO_ROOT / 'scripts' / 'build_index.py')], cwd=str(REPO_ROOT))
    
    print(f"\n=== Done ===")
    print(f"Updated: {updated}")
    print(f"Skipped: {total - updated - errors}")
    print(f"Errors: {errors}")
    print(f"Batches: {(total-1)//BATCH_SIZE + 1} (instead of {total} individual calls)")


if __name__ == '__main__':
    main()
