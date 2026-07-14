#!/usr/bin/env python3
"""
Duplicate Detection — check for duplicate entries by name and GitHub URL.

Usage: python scripts/duplicate_check.py [--fix]
"""

import json, sys, re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from scripts.categories import CATEGORIES


def extract_repo_path(url):
    """Extract owner/repo from a GitHub URL. Returns None if org-only URL."""
    if not url or 'github.com' not in url:
        return None
    m = re.search(r'github\.com[:/]([\w.-]+)/([\w.-]+?)(?:\.git|/|$)', url)
    if m:
        owner, repo = m.group(1), m.group(2)
        if repo and not repo.startswith('.') and owner != repo:
            return f'{owner.lower()}/{repo.lower()}'
    return None


def check_duplicates(fix=False):
    """Check for duplicate entries."""
    seen_names = {}
    seen_gh = {}
    duplicates = []

    for cat in CATEGORIES:
        d = REPO_ROOT / cat
        if not d.exists():
            continue
        for f in sorted(d.glob('*.json')):
            try:
                data = json.loads(f.read_text())
                name = data.get('name', '').lower()
                gh_url = data.get('github_repository', '').rstrip('/')

                if name:
                    if name in seen_names:
                        duplicates.append((seen_names[name], str(f), f'Name: {name}'))
                    else:
                        seen_names[name] = str(f)

                repo_path = extract_repo_path(gh_url)
                if repo_path:
                    if repo_path in seen_gh:
                        duplicates.append((seen_gh[repo_path], str(f), f'GitHub: {gh_url}'))
                    else:
                        seen_gh[repo_path] = str(f)
            except Exception as e:
                print(f'Warning: {f}: {e}', file=sys.stderr)

    if duplicates:
        print(f'Found {len(duplicates)} duplicate(s):')
        for orig, dup, reason in duplicates:
            print(f'\n  {reason}')
            print(f'    Original: {orig}')
            print(f'    Duplicate: {dup}')
        return False
    else:
        print(f'No duplicates found.')
        print(f'  Checked {len(seen_names)} entries by name')
        print(f'  Checked {len(seen_gh)} entries by GitHub repo path')
        return True


if __name__ == '__main__':
    fix = '--fix' in sys.argv
    success = check_duplicates(fix)
    sys.exit(0 if success else 1)
