#!/usr/bin/env python3
"""
Auto-discover new developer resources from GitHub and add them to the database.

Usage: python scripts/auto_discover.py [--dry-run] [--max-per-category 10]

Requires: GITHUB_TOKEN env var
"""

import json, os, sys, time, re, glob, math, locale
locale.setlocale(locale.LC_ALL, 'C')
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

REPO_ROOT = Path(__file__).resolve().parent.parent
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
HEADERS = {'User-Agent': 'DeveloperHub/1.0'}
if GITHUB_TOKEN:
    HEADERS['Authorization'] = f'Bearer {GITHUB_TOKEN}'

# Map GitHub topics to our categories
TOPIC_TO_CATEGORY = {
    'android': 'android', 'android-sdk': 'android', 'kotlin': 'android',
    'ios': 'mobile', 'swift': 'mobile', 'flutter': 'mobile', 'react-native': 'mobile',
    'react': 'frontend', 'vue': 'frontend', 'angular': 'frontend', 'svelte': 'frontend',
    'css': 'frontend', 'ui': 'frontend', 'frontend': 'frontend', 'webpack': 'frontend',
    'javascript': 'frontend', 'typescript': 'frontend',
    'backend': 'backend', 'api': 'backend', 'rest-api': 'backend', 'graphql': 'backend',
    'nodejs': 'backend', 'django': 'backend', 'flask': 'backend', 'fastapi': 'backend',
    'spring': 'backend', 'laravel': 'backend',
    'database': 'database', 'sql': 'database', 'nosql': 'database', 'postgresql': 'database',
    'mysql': 'database', 'mongodb': 'database', 'redis': 'database', 'sqlite': 'database',
    'cloud': 'cloud', 'aws': 'cloud', 'azure': 'cloud', 'gcp': 'cloud',
    'serverless': 'cloud', 'docker': 'containers', 'kubernetes': 'containers', 'container': 'containers',
    'devops': 'devops', 'ci': 'devops', 'cd': 'devops',
    'security': 'security', 'authentication': 'security', 'encryption': 'security',
    'linux': 'linux', 'bash': 'linux', 'unix': 'linux',
    'windows': 'windows', 'dotnet': 'windows', 'csharp': 'windows',
    'macos': 'macos', 'apple': 'macos',
    'python': 'languages', 'golang': 'languages', 'rust': 'languages', 'java': 'languages',
    'cpp': 'languages', 'ruby': 'languages', 'php': 'languages',
    'ai': 'ai', 'machine-learning': 'ai', 'deep-learning': 'ai', 'llm': 'ai', 'nlp': 'ai',
    'tensorflow': 'ai', 'pytorch': 'ai',
    'blockchain': 'blockchain', 'ethereum': 'blockchain', 'web3': 'blockchain', 'solidity': 'blockchain',
    'iot': 'iot', 'embedded': 'embedded', 'arduino': 'iot', 'raspberry-pi': 'iot',
    'game-development': 'game-development', 'game-engine': 'game-development', 'unity': 'game-development',
    'robotics': 'robotics', 'ros': 'robotics',
    'firmware': 'firmware', 'esp32': 'firmware', 'esp8266': 'firmware',
    'network': 'network', 'networking': 'network', 'proxy': 'network',
    'desktop': 'desktop', 'electron': 'desktop', 'qt': 'desktop',
    'operating-system': 'operating-systems', 'os': 'operating-systems',
    'mac': 'macos', 'osx': 'macos',
    'framework': 'frameworks', 'web-framework': 'frameworks',
    'library': 'libraries', 'tool': 'tools',
    'termux': 'termux', 'termux-repo': 'termux', 'termux-package': 'termux',
    'termux-tool': 'termux', 'termux-app': 'termux', 'termux-api': 'termux',
    'adb': 'android-tools', 'fastboot': 'android-tools',
    'android-debug': 'android-tools', 'android-tool': 'android-tools',
    'android-apk': 'android-tools', 'android-rom': 'android-tools',
    'android-recovery': 'android-tools', 'android-bootloader': 'android-tools',
    'android-devtools': 'android-tools', 'sideload': 'android-tools',
    'cli': 'cli-tools', 'command-line': 'cli-tools', 'shell': 'cli-tools',
    'terminal': 'cli-tools', 'tui': 'cli-tools', 'terminal-emulator': 'cli-tools',
    'cli-tool': 'cli-tools', 'commandline': 'cli-tools',
    'binary': 'binary', 'prebuilt': 'binary', 'portable': 'binary',
    'static-binary': 'binary', 'standalone': 'binary', 'pre-compiled': 'binary',
    'release-binary': 'binary', 'appimage': 'binary', 'portable-app': 'binary',
    'android-ndk': 'android', 'gradle': 'android', 'android-studio': 'android',

    'adb': 'android-tools', 'fastboot': 'android-tools',
    'cli': 'cli-tools', 'command-line': 'cli-tools', 'shell': 'cli-tools',
    'terminal': 'cli-tools',
    'binary': 'binary', 'prebuilt': 'binary', 'portable': 'binary',
}

# Search queries per category to find new repos

# Repos to exclude (not real developer resources)
EXCLUDE_PATTERNS = [
    'awesome-', 'awesome-list', 'free-programming', 'free-books',
    '-books', '-tutorial', '-guide', '-course', '-learning',
    'Microsoft-Activation', 'Windows-Activation', 'MAS',
    'cs-video-courses', 'developer-roadmap', 'build-your-own-x',
    'project-based-learning', 'system-design', 'system-design',
    'interview-', 'cheatsheet', 'cheat-sheet',
    '-zh_CN', '-zh-CN', '-zh',
    'android-interview', 'kotlin-interview',
    'tldr-pages', 'tldr',  # man page summaries
    'freecodecamp', 'leetcode',
    'javascript-algorithms', 'python-interview',
    'the-book-of', 'rust-book',
    'notes', '-notes', 'notebook',
    # Non-dev tools: hacking, phishing, cracking
    'hacking', 'hacktool', 'hackingtool', 'hack',
    'phish', 'phishing', 'crack', 'cracking',
    'bomb', 'bomber', 'bombing', 'spam', 'spammer',
    'exploit', 'payload', 'malware',
    'whatsapp-hack', 'instagram-hack', 'facebook-hack',
    'termux-social', 'termux-hacking', 'termux-extra', 'termux-style',
    # Non-relevant termux
    'termux-boot', 'termux-tasker', 'termux-styling',
    # Non-relevant android
    'android-tv', 'android-auto', 'android-wear', 'android-things',
    # Non-tool binaries
    'game-assets', 'game-data', 'roms', 'iso', 'firmware-dump',

]

CATEGORY_QUERIES = {
    'ai': 'topic:ai stars:>500',
    'android': 'topic:android stars:>1000',
    'frontend': 'topic:frontend stars:>1000',
    'backend': 'topic:backend stars:>1000',
    'database': 'topic:database stars:>1000',
    'cloud': 'topic:cloud stars:>500',
    'devops': 'topic:devops stars:>500',
    'security': 'topic:security stars:>500',
    'tools': 'topic:developer-tools stars:>1000',
    'mobile': 'topic:mobile stars:>500',
    'game-development': 'topic:game-development stars:>500',
    'blockchain': 'topic:blockchain stars:>200',
    'machine-learning': 'topic:machine-learning stars:>1000',
    'containers': 'topic:containers stars:>500',
    'frameworks': 'topic:framework stars:>1000',
    'libraries': 'topic:library stars:>1000',
    'languages': 'topic:programming-language stars:>1000',
    'network': 'topic:networking stars:>500',
    'iot': 'topic:iot stars:>200',
    'linux': 'topic:linux stars:>500',
    'macos': 'topic:macos stars:>200',
    'windows': 'topic:windows stars:>200',
    # Mobile & Termux tools
    'termux': 'topic:termux stars:>50',
    'android-tools': 'topic:android-tools stars:>100',
    # Binary & CLI tools
    'cli-tools': 'topic:cli stars:>1000',
    'binary': 'topic:binary stars:>200',
}

def gh_api(path):
    url = f"https://api.github.com{path}"
    req = Request(url, headers=HEADERS)
    try:
        with urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except HTTPError as e:
        if e.code in (403, 404):
            return None
        return None
    except:
        return None

def load_existing():
    """Load all existing entries into a set of IDs and GitHub URLs."""
    existing_ids = set()
    existing_gh = set()
    existing_names = set()
    
    for f in glob.glob(str(REPO_ROOT / '*/*.json')):
        if Path(f).parent.name not in CATEGORY_QUERIES and Path(f).parent.name not in ('api', 'api_server', 'scripts', 'docs', 'website', 'schemas', '.git'):
            continue
        try:
            with open(f) as fh:
                d = json.load(fh)
            eid = d.get('id', '')
            gh = d.get('github_repository', '')
            name = d.get('name', '').lower()
            if eid:
                existing_ids.add(eid)
            if gh and 'example' not in gh:
                existing_gh.add(gh.rstrip('/').lower())
            if name:
                existing_names.add(name)
        except:
            pass
    
    return existing_ids, existing_gh, existing_names

def categorize_repo(topics, language, description):
    """Determine which category a repo belongs to - with STRONG matching."""
    topic_set = set(t.lower() for t in topics)
    
    # Category-specific strong signals
    strong_signals = {
        'android': {'android', 'android-sdk', 'kotlin', 'jetpack'},
        'mobile': {'ios', 'swift', 'flutter', 'react-native', 'xamarin'},
        'frontend': {'reactjs', 'vue', 'angular', 'frontend', 'css', 'ui-components'},
        'backend': {'backend', 'rest-api', 'graphql', 'microservices'},
        'database': {'database', 'sql', 'nosql', 'orm', 'db'},
        'cloud': {'cloud', 'aws', 'azure', 'gcp', 'serverless', 'cloud-computing'},
        'containers': {'docker', 'kubernetes', 'container', 'k8s'},
        'devops': {'devops', 'ci', 'cd', 'cicd'},
        'security': {'security', 'cybersecurity', 'encryption', 'authentication'},
        'blockchain': {'blockchain', 'ethereum', 'web3', 'solidity', 'crypto'},
        'game-development': {'game-development', 'game-engine', 'gamedev', 'unity3d'},
        'iot': {'iot', 'internet-of-things', 'arduino', 'esp32'},
        'embedded': {'embedded', 'embedded-systems', 'firmware'},
        'firmware': {'firmware', 'esp8266', 'microcontroller'},
        'robotics': {'robotics', 'robot', 'ros'},
        'ai': {'ai', 'artificial-intelligence', 'machine-learning', 'deep-learning', 'llm', 'nlp'},
        'machine-learning': {'machine-learning', 'deep-learning', 'ml'},
        'network': {'network', 'networking', 'proxy', 'vpn'},
        'languages': {'programming-language', 'language'},
        'frameworks': {'framework', 'web-framework'},
        'libraries': {'library'},
        'tools': {'developer-tools', 'cli', 'command-line'},
        'linux': {'linux', 'unix'},
        'windows': {'windows', 'dotnet'},
        'macos': {'macos', 'mac'},
        'termux': {'termux', 'termux-package', 'termux-tool'},
        'android-tools': {'android-tools', 'adb', 'fastboot', 'android-utility'},
        'cli-tools': {'cli', 'command-line', 'terminal', 'shell'},
        'binary': {'binary', 'prebuilt', 'portable', 'standalone'},
    }
    
    # Check strong signals first
    matched_cats = set()
    for cat, signals in strong_signals.items():
        if topic_set & signals:
            matched_cats.add(cat)
    
    # If multiple matches, prefer non-ai specific ones
    if len(matched_cats) > 1:
        # Remove 'ai' if there are other good matches (many repos use AI but aren't AI tools)
        if 'ai' in matched_cats and len(matched_cats) > 1:
            matched_cats.discard('ai')
        # Remove 'machine-learning' similarly
        if 'machine-learning' in matched_cats and len(matched_cats) > 1:
            matched_cats.discard('machine-learning')
    
    if matched_cats:
        return list(matched_cats)[0]
    
    # Fallback: check language
    if language:
        lang_lower = language.lower()
        lang_map = {
            'kotlin': 'android', 'swift': 'mobile', 'javascript': 'frontend',
            'typescript': 'frontend', 'go': 'backend', 'java': 'backend',
            'ruby': 'backend', 'php': 'backend', 'dart': 'mobile',
            'solidity': 'blockchain', 'rust': 'tools',
            'c': 'languages', 'c++': 'languages', 'python': 'tools',
            'csharp': 'windows',
        }
        return lang_map.get(lang_lower, 'tools')
    
    return None

def discover_new_entries(max_per_category=10, dry_run=False):
    existing_ids, existing_gh, existing_names = load_existing()
    print(f"Existing entries: {len(existing_ids)} IDs, {len(existing_gh)} GitHub URLs\n")
    
    discovered = []
    errors = 0
    
    for category, query in sorted(CATEGORY_QUERIES.items()):
        print(f"\n--- {category.upper()} ---")
        
        # Search GitHub
        search_query = f"{query} sort:stars-desc"
        import urllib.parse
        params = urllib.parse.urlencode({"q": search_query, "per_page": max_per_category + 10})
        data = gh_api(f'/search/repositories?{params}')
        if not data or not data.get('items'):
            print(f"  No results or API error")
            continue
        
        found = 0
        for item in data['items']:
            if found >= max_per_category:
                break
            
            # Skip forks
            if item.get('fork'):
                continue
            
            full_name = item['full_name']
            gh_url = item['html_url'].rstrip('/').lower()
            name = item['name']  # Original GitHub name
            
            # Skip excluded patterns
            skip = False
            for pat in EXCLUDE_PATTERNS:
                if pat.lower() in name.lower() or pat.lower() in full_name.lower():
                    skip = True
                    break
            if skip:
                continue
            
            # Skip if already in database
            if gh_url in existing_gh or item['name'] in existing_names:
                continue
            
            # Skip if name is too generic
            if name.lower() in ('project', 'app', 'demo', 'test', 'my-project', 'sample'):
                continue
            
            topics = item.get('topics', [])
            language = item.get('language')
            description = item.get('description', '') or ''
            
            # Determine category
            # Check if repo is a developer tool (has code, not just docs/books)
            if not language and not topics:
                continue
            if topics and all(t in ('awesome-list', 'book', 'documentation') for t in topics[:3]):
                continue
            
            # Skip docs/tutorial repos
            desc_lower = (description or '').lower()
            desc_skip_keywords = ['book', 'tutorial', 'learn', 'guide', 'course', 
                                  'notes', 'interview', 'cheat sheet', 'awesome list',
                                  'curated list', 'awesome ', 'resources for']
            if any(kw in desc_lower for kw in desc_skip_keywords):
                continue
            
            # Skip repos without actual code (stars but no language = mostly docs)
            if not language and item.get('size', 0) < 1000:
                continue
            
            detected_cat = categorize_repo(topics, language, description)
            # If found by specific category search, trust the search category
            # unless there's a very strong conflicting signal
            if detected_cat and detected_cat != category:
                # Related categories: allow lenient matching
                related = {
                    'linux': {'termux', 'cli-tools', 'network'},
                    'android': {'termux', 'mobile', 'android-tools'},
                    'mobile': {'android', 'android-tools'},
                    'tools': {'cli-tools', 'binary'},
                    'network': {'security'},
                    'security': {'network'},
                    'frontend': {'mobile'},
                    'database': {'cloud'},
                    'termux': {'android', 'cli-tools', 'linux'},
                    'cli-tools': {'termux', 'tools', 'linux'},
                    'binary': {'tools', 'cli-tools', 'linux'},
                    'android-tools': {'termux', 'android', 'mobile'},
                }
                if category not in related.get(detected_cat, set()):
                    print(f"  ⚠️  {full_name} detected as '{detected_cat}' not '{category}', skipping here")
                    continue
            # If no category detected, use the search category
            if not detected_cat:
                detected_cat = category
            
            # Generate ID
            entry_id = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
            if not entry_id or entry_id in existing_ids:
                entry_id = f"{entry_id}-{category}" if entry_id else f"{category}-{int(time.time())}"
            
            # Get additional repo details
            repo_data = gh_api(f'/repos/{full_name}')
            if not repo_data:
                continue
            
            license_spdx = None
            if repo_data.get('license'):
                license_spdx = repo_data['license'].get('spdx_id') or repo_data['license'].get('key')
            
            entry = {
                "id": entry_id,
                "name": item['name'],
                "category": category,
                "description": (description or f"A {category} project on GitHub").strip()[:200],
                "official_website": repo_data.get('homepage') or f"https://github.com/{full_name}",
                "documentation": f"https://github.com/{full_name}#readme",
                "github_repository": f"https://github.com/{full_name}",
                "license": license_spdx or "MIT",
                "latest_version": repo_data.get('default_branch', 'main'),
                "programming_languages": [language] if language else ["Generic"],
                # Smart platform assignment based on category
                if category == 'termux':
                    plats = ["Termux", "Android", "Linux"]
                elif category == 'android-tools':
                    plats = ["Android", "Linux", "Windows", "macOS"]
                elif category == 'binary':
                    has_win = 'windows' in (description or '').lower() or any('win' in (t or '') for t in (topics or []))
                    has_mac = 'macos' in (description or '').lower() or 'macos' in (topics or [])
                    plats = ["Linux"]
                    if has_win: plats.append("Windows")
                    if has_mac: plats.append("macOS")
                elif category == 'cli-tools':
                    plats = ["Linux", "macOS", "Windows", "Termux"]
                else:
                    plats = ["Web", "Linux", "macOS", "Windows", "Android", "Termux"][:min(6, max(1, item.get('stargazers_count', 0) // 5000 + 1))]
                "platforms": plats,
                "tags": (topics or [])[:8],
                "has_binaries": False,  # Will be checked on update
                "alternatives": [],
                "popularity": min(10, max(1, int(item.get('stargazers_count', 0) / 1000) + 5)),
                "maintained": not repo_data.get('archived', False),
                "archived": repo_data.get('archived', False),
                "open_source": True,
                "repository_statistics": {
                    "stars": item.get('stargazers_count', 0),
                    "forks": item.get('forks_count', 0),
                    "open_issues": item.get('open_issues_count', 0),
                    "watchers": item.get('subscribers_count', 0),
                },
                "last_checked": time.strftime('%Y-%m-%d'),
                "last_updated": time.strftime('%Y-%m-%d'),
                "has_binaries": False,
            }
            
            if not dry_run:
                # Save to file
                cat_dir = REPO_ROOT / category
                cat_dir.mkdir(exist_ok=True)
                filepath = cat_dir / f"{entry_id}.json"
                with open(filepath, 'w') as f:
                    json.dump(entry, f, indent=2)
            
            stars = item.get('stargazers_count', 0)
            print(f"  ✅ +{entry['name']} ({category}) ⭐{stars}")
            discovered.append(entry)
            existing_ids.add(entry_id)
            existing_gh.add(gh_url)
            existing_names.add(name.lower())
            found += 1
            time.sleep(0.3)
        
        if found == 0:
            print(f"  No new entries found")
    
    print(f"\n=== Summary ===")
    print(f"Discovered: {len(discovered)} new entries")
    if dry_run:
        print(f"(dry run - no files were created)")
    else:
        print(f"Files saved to category folders")
    
    return discovered

if __name__ == '__main__':
    dry_run = '--dry-run' in sys.argv
    max_per_cat = 10
    for a in sys.argv:
        if a.startswith('--max-per-category='):
            max_per_cat = int(a.split('=')[1])
    
    discover_new_entries(max_per_cat, dry_run)
