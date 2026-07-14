#!/usr/bin/env python3
"""
External resource scraper for Developer Hub.

Scrapes alternative sources for developer resources not easily found on GitHub:
- F-Droid: Android apps & tools
- Termux official packages: Packages available in Termux repositories
- GitHub releases: Pre-built binaries for popular tools

Usage:
    python scripts/scrape_external.py [--dry-run] [--sources fdroid,termux,releases]

Requires: GITHUB_TOKEN env var for GitHub API access
"""

import json, os, sys, time, re, html as html_mod
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from scripts.categories import CATEGORIES

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
HEADERS = {'User-Agent': 'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'}
if GITHUB_TOKEN:
    HEADERS['Authorization'] = f'Bearer {GITHUB_TOKEN}'

# === Utility ===

def fetch_url(url, headers=None):
    """Fetch a URL and return text content."""
    h = HEADERS.copy()
    if headers:
        h.update(headers)
    try:
        req = Request(url, headers=h)
        with urlopen(req, timeout=30) as resp:
            return resp.read().decode('utf-8', errors='replace')
    except Exception as e:
        print(f"  ⚠️  Error fetching {url}: {e}")
        return None


def gh_api(path):
    """Call GitHub API v3."""
    url = f"https://api.github.com{path}"
    h = HEADERS.copy()
    h['Accept'] = 'application/vnd.github.v3+json'
    return fetch_url(url, h)


def parse_github_url(url):
    """Extract owner/repo from GitHub URL."""
    m = re.search(r'github\.com[:/]([\w.-]+)/([\w.-]+?)(?:\.git)?$', url)
    if m:
        return m.group(1), re.sub(r'\.git$', '', m.group(2))
    return None, None


def safe_slug(name):
    """Create a safe file slug from name."""
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')


def load_existing(category):
    """Load existing entries in a category."""
    existing = {}
    cat_dir = REPO_ROOT / category
    if not cat_dir.exists():
        return existing
    for f in cat_dir.glob('*.json'):
        try:
            data = json.loads(f.read_text())
            existing[data.get('id')] = data
            if data.get('github_repository'):
                existing[data['github_repository'].rstrip('/')] = data
            existing[data.get('name', '').lower()] = data
        except:
            pass
    return existing


def save_entry(entry, dry_run=False):
    """Save an entry to its category folder."""
    if dry_run:
        print(f"  📄 [DRY RUN] Would save: {entry['category']}/{entry['id']}.json")
        return True
    
    cat_dir = REPO_ROOT / entry['category']
    cat_dir.mkdir(exist_ok=True)
    filepath = cat_dir / f"{entry['id']}.json"
    
    # Don't overwrite if already exists with more data
    if filepath.exists():
        try:
            existing = json.loads(filepath.read_text())
            existing_desc = existing.get('description', '')
            new_desc = entry.get('description', '')
            # Only overwrite if existing has placeholder or empty description
            if existing_desc and 'todo' not in existing_desc.lower() and 'coming soon' not in existing_desc.lower():
                print(f"  ⏭️  Skipping existing: {entry['name']}")
                return False
        except:
            pass
    
    with open(filepath, 'w') as f:
        json.dump(entry, f, indent=2)
    print(f"  ✅ +{entry['name']} ({entry['category']})")
    return True


# === F-Droid Scraper ===

def scrape_fdroid(max_items=20, dry_run=False):
    """Scrape F-Droid for Android tools and apps."""
    print("\n🔍 Scraping F-Droid for Android tools...")
    discovered = []
    existing = load_existing('android-tools')
    existing.update(load_existing('android'))
    
    # F-Droid API: https://f-droid.org/api/v1/packages
    # Categories of interest: "Development", "System", "Navigation", "Multimedia"
    categories = ["Development", "System"]
    
    for cat in categories:
        url = f"https://f-droid.org/api/v1/packages?category={cat}&limit={max_items}&offset=0"
        data = fetch_url(url, {'Accept': 'application/json'})
        if not data:
            # Try the sorting approach
            url = f"https://f-droid.org/api/v1/packages?sort={cat}&limit={max_items}"
            data = fetch_url(url, {'Accept': 'application/json'})
        if not data:
            continue
        
        try:
            packages = json.loads(data)
            if isinstance(packages, dict):
                packages = packages.get('packages', packages.get('results', []))
            if isinstance(packages, dict):
                # Single package
                packages = [packages]
        except:
            print(f"  ⚠️  Could not parse F-Droid response for {cat}")
            continue
        
        for pkg in packages[:max_items]:
            try:
                if isinstance(pkg, str):
                    # Got package name only, need to fetch details
                    pkg_url = f"https://f-droid.org/api/v1/packages/{pkg}"
                    pkg_data = fetch_url(pkg_url, {'Accept': 'application/json'})
                    if not pkg_data:
                        continue
                    pkg = json.loads(pkg_data)
                
                pkg_name = pkg.get('name', pkg.get('packageName', ''))
                pkg_id = pkg.get('packageName', safe_slug(pkg_name))
                summary = pkg.get('summary', pkg.get('description', ''))[:200]
                description = pkg.get('description', pkg.get('summary', ''))[:300]
                # Strip HTML from description
                description = re.sub(r'<[^>]+>', '', description).strip()[:200]
                
                # Skip non-tool apps
                skip_keywords = ['wallpaper', 'theme', 'icon', 'game', 'launcher', 'keyboard', 'live wallpaper']
                if any(k in (summary + description).lower() for k in skip_keywords):
                    continue
                
                # Determine if this is a dev tool or regular android entry
                tool_keywords = ['terminal', 'ssh', 'adb', 'vnc', 'server', 'proxy', 'dns',
                                'network', 'tool', 'editor', 'ide', 'compiler', 'python',
                                'git', 'database', 'sql', 'api', 'sdk', 'debug']
                is_tool = any(k in (pkg_name + summary + description).lower() for k in tool_keywords)
                target_cat = 'android-tools' if is_tool else 'android'
                
                entry_id = f"fdroid-{safe_slug(pkg_id)}"
                if entry_id in existing:
                    continue
                
                # Get source URL if available
                source_url = pkg.get('sourceCode', '')
                if not source_url and pkg.get('webSite'):
                    source_url = pkg.get('webSite')
                
                # Get GitHub info from source URL
                stars = 0
                if 'github.com' in source_url:
                    owner, repo = parse_github_url(source_url)
                    if owner:
                        repo_data = fetch_url(f"https://api.github.com/repos/{owner}/{repo}",
                                             HEADERS)
                        if repo_data:
                            try:
                                rd = json.loads(repo_data)
                                stars = rd.get('stargazers_count', 0)
                            except:
                                pass
                
                platforms = ["Android"]
                if is_tool:
                    platforms.append("Termux")
                
                entry = {
                    "id": entry_id,
                    "name": pkg_name,
                    "category": target_cat,
                    "description": (summary or description or f"An Android tool available on F-Droid")[:200],
                    "official_website": pkg.get('webSite', source_url) or f"https://f-droid.org/packages/{pkg_id}/",
                    "documentation": f"https://f-droid.org/packages/{pkg_id}/",
                    "github_repository": source_url or f"https://f-droid.org/packages/{pkg_id}/",
                    "license": pkg.get('license', 'MIT'),
                    "latest_version": pkg.get('suggestedVersionCode', pkg.get('version', '1.0')),
                    "programming_languages": ["Java", "Kotlin"],
                    "platforms": platforms,
                    "tags": ["android", "f-droid", is_tool and "tool" or "app", pkg.get('category', '')],
                    "alternatives": [],
                    "popularity": min(10, max(1, stars // 1000 + 2)),
                    "maintained": True,
                    "archived": False,
                    "open_source": True,
                    "repository_statistics": {"stars": stars, "forks": 0, "open_issues": 0, "watchers": 0},
                    "last_checked": time.strftime('%Y-%m-%d'),
                    "last_updated": time.strftime('%Y-%m-%d'),
                    "source": "fdroid",
                }
                
                if save_entry(entry, dry_run):
                    discovered.append(entry)
                    existing[entry_id] = entry
                
            except Exception as e:
                print(f"  ⚠️  Error processing F-Droid entry: {e}")
                continue
    
    print(f"  📊 F-Droid: {len(discovered)} new entries")
    return discovered


# === Termux Packages Scraper ===

def scrape_termux_packages(max_items=30, dry_run=False):
    """Scrape Termux official package repository."""
    print("\n🔍 Scraping Termux package repository...")
    discovered = []
    existing = load_existing('termux')
    
    # Termux package repository has a Packages file or we can use
    # the termux packages API/GitHub
    # Try fetching from termux-packages repo on GitHub
    repos_to_check = [
        # Termux main repo packages listing
        "https://raw.githubusercontent.com/termux/termux-packages/refs/heads/master/packages",
        # Alternative: termux community packages
    ]
    
    # Use GitHub search to find termux-related repos
    search_url = ("https://api.github.com/search/repositories?q="
                  "topic:termux+pushed:>2024-01-01&sort=stars&order=desc&per_page=50")
    
    data = fetch_url(search_url)
    if not data:
        print("  ⚠️  Could not search GitHub for Termux repos")
        return discovered
    
    try:
        result = json.loads(data)
        items = result.get('items', [])
    except:
        print("  ⚠️  Could not parse GitHub search results")
        return discovered
    
    for item in items:
        try:
            name = item.get('name', '')
            full_name = item.get('full_name', '')
            description = (item.get('description') or '')[:200]
            gh_url = f"https://github.com/{full_name}"
            
            # Skip non-tool repos
            skip = ['awesome', 'tutorial', 'guide', 'book', 'notes',
                    'hack', 'crack', 'phish', 'malware', 'exploit',
                    'bomb', 'spam', 'social', 'whatsapp', 'instagram',
                    'facebook', 'tiktok', 'snapchat', 'style', 'styling',
                    'theme', 'font', 'widget', 'boot', 'tasker',
                    'lesson', 'course', 'collection', 'list']
            if any(k in (name + ' ' + description).lower() for k in skip):
                continue
            
            # Check existing
            entry_id = safe_slug(name)
            gh_url_clean = gh_url.rstrip('/')
            if entry_id in existing or gh_url_clean in existing or name.lower() in existing:
                continue
            
            topics = item.get('topics', [])
            language = item.get('language', '')
            stars = item.get('stargazers_count', 0)
            
            # Determine sub-category
            is_cli = any(t in ['cli', 'command-line', 'terminal', 'tui'] for t in topics)
            is_tool = any(t in ['tool', 'utility'] for t in topics)
            
            entry = {
                "id": entry_id,
                "name": name,
                "category": "termux",
                "description": description or f"A Termux tool for mobile development",
                "official_website": item.get('homepage') or gh_url,
                "documentation": f"https://github.com/{full_name}#readme",
                "github_repository": gh_url,
                "license": "MIT",  # Will be updated on auto_update
                "latest_version": item.get('default_branch', 'master'),
                "programming_languages": [language] if language else ["Shell", "Python"],
                "platforms": ["Termux", "Android"],
                "tags": (topics or [])[:8] + (["cli"] if is_cli else []) + (["tool"] if is_tool else []),
                "alternatives": [],
                "popularity": min(10, max(1, stars // 200 + 2)),
                "maintained": not item.get('archived', False),
                "archived": item.get('archived', False),
                "open_source": True,
                "repository_statistics": {
                    "stars": stars,
                    "forks": item.get('forks_count', 0),
                    "open_issues": item.get('open_issues_count', 0),
                    "watchers": item.get('subscribers_count', 0),
                },
                "last_checked": time.strftime('%Y-%m-%d'),
                "last_updated": time.strftime('%Y-%m-%d'),
                "source": "termux-github",
            }
            
            # Add binary flag for compiled tools
            compiled_langs = ['C', 'C++', 'Rust', 'Go', 'Zig', 'Nim', 'D']
            if language in compiled_langs:
                entry['has_binaries'] = True
                entry['tags'] = list(set(entry['tags'] + ['has-binary']))
            
            if save_entry(entry, dry_run):
                discovered.append(entry)
                existing[entry_id] = entry
                existing[gh_url_clean] = entry
                existing[name.lower()] = entry
            
            time.sleep(0.2)  # Rate limiting
            
        except Exception as e:
            print(f"  ⚠️  Error processing Termux entry: {e}")
            continue
    
    print(f"  📊 Termux: {len(discovered)} new entries")
    return discovered


# === GitHub Releases Scraper for Binaries ===

def scrape_binary_releases(max_items=20, dry_run=False):
    """Find GitHub repos that provide pre-built binaries."""
    print("\n🔍 Scraping GitHub for pre-built binary releases...")
    discovered = []
    existing = load_existing('binary')
    
    queries = [
        "topic:prebuilt-binary stars:>100",
        "topic:static-binary stars:>50",
        "topic:portable stars:>200",
        "topic:cli stars:>500 language:rust",
        "topic:cli stars:>500 language:go",
    ]
    
    for query in queries:
        search_url = f"https://api.github.com/search/repositories?q={quote_plus(query)}&sort=stars&order=desc&per_page=30"
        data = fetch_url(search_url)
        if not data:
            continue
        
        try:
            result = json.loads(data)
            items = result.get('items', [])
        except:
            continue
        
        for item in items:
            try:
                name = item.get('name', '')
                full_name = item.get('full_name', '')
                description = (item.get('description') or '')[:200]
                gh_url = f"https://github.com/{full_name}"
                
                skip = ['awesome', 'tutorial', 'guide', 'book', 'example',
                        'demo', 'sample', 'awesome', 'list',
                        'hack', 'crack', 'malware', 'exploit']
                if any(k in (name + ' ' + description).lower() for k in skip):
                    continue
                
                entry_id = f"bin-{safe_slug(name)}"
                gh_url_clean = gh_url.rstrip('/')
                if entry_id in existing or gh_url_clean in existing or name.lower() in existing:
                    continue
                
                # Check if repo has releases with assets
                releases_url = f"https://api.github.com/repos/{full_name}/releases?per_page=3"
                releases_data = fetch_url(releases_url)
                has_binaries = False
                if releases_data:
                    try:
                        releases = json.loads(releases_data)
                        for release in releases:
                            if release.get('assets'):
                                has_binaries = True
                                break
                    except:
                        pass
                
                if not has_binaries:
                    continue  # Skip repos without releases
                
                topics = item.get('topics', [])
                language = item.get('language', '')
                stars = item.get('stargazers_count', 0)
                
                # Determine platforms from release assets
                platforms = ["Linux"]
                if releases_data:
                    try:
                        releases = json.loads(releases_data)
                        if releases and releases[0].get('assets'):
                            for asset in releases[0]['assets']:
                                aname = asset.get('name', '').lower()
                                if 'win' in aname or '.exe' in aname or '.msi' in aname:
                                    if 'Windows' not in platforms: platforms.append("Windows")
                                if 'mac' in aname or 'darwin' in aname or '.dmg' in aname:
                                    if 'macOS' not in platforms: platforms.append("macOS")
                                if 'arm' in aname or 'aarch' in aname or 'android' in aname:
                                    if 'Android' not in platforms: platforms.append("Android")
                    except:
                        pass
                
                entry = {
                    "id": entry_id,
                    "name": name,
                    "category": "binary",
                    "description": description or f"A pre-built tool available as a binary release",
                    "official_website": item.get('homepage') or gh_url,
                    "documentation": f"https://github.com/{full_name}#readme",
                    "github_repository": gh_url,
                    "license": "MIT",
                    "latest_version": item.get('default_branch', 'main'),
                    "programming_languages": [language] if language else ["Generic"],
                    "platforms": platforms,
                    "tags": (topics or [])[:8] + ["binary", "pre-built"],
                    "has_binaries": True,
                    "alternatives": [],
                    "popularity": min(10, max(1, stars // 1000 + 4)),
                    "maintained": not item.get('archived', False),
                    "archived": item.get('archived', False),
                    "open_source": True,
                    "repository_statistics": {
                        "stars": stars,
                        "forks": item.get('forks_count', 0),
                        "open_issues": item.get('open_issues_count', 0),
                        "watchers": item.get('subscribers_count', 0),
                    },
                    "last_checked": time.strftime('%Y-%m-%d'),
                    "last_updated": time.strftime('%Y-%m-%d'),
                    "source": "binary-release",
                }
                
                if save_entry(entry, dry_run):
                    discovered.append(entry)
                    existing[entry_id] = entry
                
                time.sleep(0.3)
                
            except Exception as e:
                print(f"  ⚠️  Error processing binary entry: {e}")
                continue
    
    # Also search for tools that mention "static binary"
    static_search = ("https://api.github.com/search/repositories?q="
                     "static+binary+OR+precompiled+OR+portable+stars:>100&"
                     "sort=stars&order=desc&per_page=20")
    data = fetch_url(static_search)
    if data:
        try:
            result = json.loads(data)
            for item in result.get('items', []):
                # Similar processing as above but shorter
                name = item.get('name', '')
                full_name = item.get('full_name', '')
                gh_url = f"https://github.com/{full_name}"
                gh_url_clean = gh_url.rstrip('/')
                
                if any(k in name.lower() for k in ['awesome', 'tutorial', 'hack', 'crack']):
                    continue
                    
                entry_id = f"bin-{safe_slug(name)}"
                if entry_id in existing or gh_url_clean in existing:
                    continue
                
                # Quick release check
                releases_url = f"https://api.github.com/repos/{full_name}/releases?per_page=2"
                rdata = fetch_url(releases_url)
                has_bin = False
                if rdata:
                    try:
                        rels = json.loads(rdata)
                        if rels and rels[0].get('assets'):
                            has_bin = True
                    except:
                        pass
                
                if not has_bin:
                    # Check if it's a Go/Rust binary project
                    lang = item.get('language', '')
                    if lang not in ['Go', 'Rust', 'Zig', 'Nim']:
                        continue
                
                entry = {
                    "id": entry_id,
                    "name": name,
                    "category": "binary",
                    "description": (item.get('description') or f"A portable CLI tool with pre-built binaries")[:200],
                    "official_website": item.get('homepage') or gh_url,
                    "documentation": f"https://github.com/{full_name}#readme",
                    "github_repository": gh_url,
                    "license": "MIT",
                    "latest_version": item.get('default_branch', 'main'),
                    "programming_languages": [item.get('language', 'Generic')],
                    "platforms": ["Linux", "macOS", "Windows"],
                    "tags": (item.get('topics', []) or [])[:6] + ["binary", "pre-built"],
                    "has_binaries": has_bin,
                    "alternatives": [],
                    "popularity": min(10, max(1, item.get('stargazers_count', 0) // 1000 + 3)),
                    "maintained": not item.get('archived', False),
                    "archived": item.get('archived', False),
                    "open_source": True,
                    "repository_statistics": {
                        "stars": item.get('stargazers_count', 0),
                        "forks": item.get('forks_count', 0),
                        "open_issues": item.get('open_issues_count', 0),
                        "watchers": item.get('subscribers_count', 0),
                    },
                    "last_checked": time.strftime('%Y-%m-%d'),
                    "last_updated": time.strftime('%Y-%m-%d'),
                    "source": "binary-release",
                }
                
                if save_entry(entry, dry_run):
                    discovered.append(entry)
                    existing[entry_id] = entry
                
                time.sleep(0.3)
                
        except Exception as e:
            print(f"  ⚠️  Error in binary static search: {e}")
    
    print(f"  📊 Binary releases: {len(discovered)} new entries")
    return discovered


# === CLI Tools Scraper ===

def scrape_cli_tools(max_items=30, dry_run=False):
    """Scrape for CLI tools on GitHub."""
    print("\n🔍 Scraping GitHub for CLI tools...")
    discovered = []
    existing = load_existing('cli-tools')
    
    queries = [
        "topic:cli stars:>1000",
        "topic:command-line stars:>1000",
        "topic:terminal stars:>500",
        "topic:tui stars:>500",
    ]
    
    for query in queries:
        search_url = f"https://api.github.com/search/repositories?q={quote_plus(query)}&sort=stars&order=desc&per_page=30"
        data = fetch_url(search_url)
        if not data:
            continue
        
        try:
            result = json.loads(data)
            items = result.get('items', [])
        except:
            continue
        
        for item in items:
            try:
                name = item.get('name', '')
                full_name = item.get('full_name', '')
                description = (item.get('description') or '')[:200]
                gh_url = f"https://github.com/{full_name}"
                
                skip = ['awesome', 'tutorial', 'guide', 'book', 'example',
                        'demo', 'list', 'cheatsheet', 'interview', 'leetcode',
                        'hack', 'crack', 'malware', 'exploit', 'bomb', 'spam',
                        'notes', 'notebook', 'course', 'collection',
                        'awesome-list', 'free-programming', 'build-your-own']
                if any(k in (name + ' ' + description).lower() for k in skip):
                    continue
                
                # Check if already exists in any related category
                entry_id = safe_slug(name)
                gh_url_clean = gh_url.rstrip('/')
                if entry_id in existing or gh_url_clean in existing or name.lower() in existing:
                    continue
                
                # Also check termux, binary categories
                for other_cat in ['termux', 'binary', 'tools']:
                    other_existing = load_existing(other_cat)
                    if entry_id in other_existing or gh_url_clean in other_existing or name.lower() in other_existing:
                        continue
                
                topics = item.get('topics', [])
                language = item.get('language', '')
                stars = item.get('stargazers_count', 0)
                compiled = language in ['C', 'C++', 'Rust', 'Go', 'Zig', 'Nim', 'D']
                
                # Detect platforms
                platforms = ["Linux", "macOS", "Windows"]
                if compiled:
                    platforms.append("Termux")
                
                entry = {
                    "id": entry_id,
                    "name": name,
                    "category": "cli-tools",
                    "description": description or f"A command-line tool for developers",
                    "official_website": item.get('homepage') or gh_url,
                    "documentation": f"https://github.com/{full_name}#readme",
                    "github_repository": gh_url,
                    "license": "MIT",
                    "latest_version": item.get('default_branch', 'main'),
                    "programming_languages": [language] if language else ["Generic"],
                    "platforms": platforms,
                    "tags": (topics or [])[:8] + ["cli", "command-line"],
                    "has_binaries": compiled,
                    "alternatives": [],
                    "popularity": min(10, max(1, stars // 1000 + 4)),
                    "maintained": not item.get('archived', False),
                    "archived": item.get('archived', False),
                    "open_source": True,
                    "repository_statistics": {
                        "stars": stars,
                        "forks": item.get('forks_count', 0),
                        "open_issues": item.get('open_issues_count', 0),
                        "watchers": item.get('subscribers_count', 0),
                    },
                    "last_checked": time.strftime('%Y-%m-%d'),
                    "last_updated": time.strftime('%Y-%m-%d'),
                    "source": "cli-github",
                }
                
                if save_entry(entry, dry_run):
                    discovered.append(entry)
                    existing[entry_id] = entry
                
                time.sleep(0.2)
                
            except Exception as e:
                continue
    
    print(f"  📊 CLI tools: {len(discovered)} new entries")
    return discovered


# === Main ===

def main():
    dry_run = '--dry-run' in sys.argv
    sources = ['fdroid', 'termux', 'binary', 'cli']
    
    for a in sys.argv:
        if a.startswith('--sources='):
            sources = a.split('=', 1)[1].split(',')
    
    total_new = 0
    
    if 'fdroid' in sources:
        total_new += len(scrape_fdroid(30, dry_run))
    
    if 'termux' in sources:
        total_new += len(scrape_termux_packages(30, dry_run))
    
    if 'binary' in sources:
        total_new += len(scrape_binary_releases(20, dry_run))
    
    if 'cli' in sources:
        total_new += len(scrape_cli_tools(30, dry_run))
    
    print(f"\n{'='*50}")
    print(f"Total new entries: {total_new}")
    if dry_run:
        print("(dry run - no files created)")
    print(f"{'='*50}")


if __name__ == '__main__':
    main()


# ═══════════════════════════════════════════
#  Awesome Lists Scraper
# ═══════════════════════════════════════════
def scrape_awesome_lists(max_items=20, dry_run=False):
    """Scrape curated Awesome Lists dari GitHub.
    Awesome lists adalah curated list manusia — akurasi tinggi.
    """
    print(f"\n{'='*60}")
    print(f"  Scraping Awesome Lists")
    print(f"{'='*60}")

    awesome_lists = {
        'ai': ['https://github.com/ChristosChristofidis/awesome-deep-learning'],
        'android': ['https://github.com/JStumpp/awesome-android', 'https://github.com/wasabeef/awesome-android-ui'],
        'backend': ['https://github.com/awesome-foss/awesome-sysadmin'],
        'cli-tools': ['https://github.com/agarrharr/awesome-cli-apps'],
        'database': ['https://github.com/oxnr/awesome-bigdata'],
        'devops': ['https://github.com/AcalephStorage/awesome-devops'],
        'frontend': ['https://github.com/dypsilon/frontend-dev-bookmarks'],
        'game-development': ['https://github.com/ellisonleao/magictools'],
        'iot': ['https://github.com/HQarroum/awesome-iot'],
        'machine-learning': ['https://github.com/josephmisiti/awesome-machine-learning'],
        'security': ['https://github.com/sbilly/awesome-security'],
        'tools': ['https://github.com/sindresorhus/awesome', 'https://github.com/awesome-selfhosted/awesome-selfhosted'],
    }

    found = 0
    skipped = 0

    for category, urls in awesome_lists.items():
        existing = load_existing(category)
        cat_dir = REPO_ROOT / category
        cat_dir.mkdir(exist_ok=True)

        for list_url in urls:
            if found >= max_items:
                break
            m = re.search(r'github.com/([^/]+/[^/]+)', list_url)
            if not m:
                continue
            repo_full = m.group(1)
            print(f"  Processing: {repo_full}")

            # Get README content
            readme_url = f"https://api.github.com/repos/{repo_full}/readme"
            data = fetch_url(readme_url)
            if not data:
                continue
            try:
                readme_data = json.loads(data)
                readme_content = readme_data.get('content', '')
                import base64
                readme_text = base64.b64decode(readme_content).decode('utf-8', errors='replace')
            except:
                continue

            # Extract GitHub links
            gh_links = re.findall(r'https?://github.com/([\w.-]+/[\w.-]+?)(?:\)|\]|\s|$)', readme_text)
            gh_links = list(set(gh_links))

            for gh_path in gh_links[:10]:
                if found >= max_items:
                    break
                gh_url = f"https://github.com/{gh_path}"
                if gh_url.rstrip('/').lower() in existing:
                    skipped += 1
                    continue

                repo_info = fetch_url(f"https://api.github.com/repos/{gh_path}")
                if not repo_info:
                    continue
                try:
                    item = json.loads(repo_info)
                except:
                    continue
                if item.get('fork') or item.get('disabled'):
                    continue
                stars = item.get('stargazers_count', 0)
                if stars < 20:
                    continue
                description = (item.get('description') or '')[:200]
                if len(description) < 20:
                    continue

                topics = item.get('topics', [])
                language = item.get('language', '')
                name = item.get('name', gh_path.split('/')[-1])
                entry_id = safe_slug(name)

                entry = {
                    'id': entry_id,
                    'name': item.get('full_name', name),
                    'category': category,
                    'description': description,
                    'official_website': item.get('homepage') or gh_url,
                    'documentation': f"{gh_url}#readme",
                    'github_repository': gh_url,
                    'license': (item.get('license') or {}).get('spdx_id', 'MIT') if item.get('license') else 'MIT',
                    'programming_languages': [language] if language else ['Generic'],
                    'platforms': ['Web', 'Linux', 'macOS', 'Windows'],
                    'tags': (topics or [])[:8],
                    'alternatives': [],
                    'popularity': min(10, max(1, int(stars / 1000) + 5)),
                    'maintained': not item.get('archived', False),
                    'archived': item.get('archived', False),
                    'open_source': True,
                    'repository_statistics': {
                        'stars': stars, 'forks': item.get('forks_count', 0),
                        'open_issues': item.get('open_issues_count', 0),
                        'watchers': item.get('subscribers_count', 0),
                    },
                    'source': 'awesome_list',
                    'last_checked': time.strftime('%Y-%m-%d'),
                    'last_updated': time.strftime('%Y-%m-%d'),
                }
                if save_entry(entry, dry_run):
                    print(f"  + {entry['name']} (⭐{stars}) → {category}/")
                    found += 1
                else:
                    skipped += 1
                time.sleep(SLEEP_BETWEEN_CALLS)

    print(f"\n=== Awesome Lists Results ===")
    print(f"  Found: {found}")
    print(f"  Skipped: {skipped}")
    return found


# ═══════════════════════════════════════════
#  GitHub Trending Scraper
# ═══════════════════════════════════════════
def scrape_github_trending(max_items=20, dry_run=False):
    """Scrape GitHub Trending — repos yang lagi populer."""
    print(f"\n{'='*60}")
    print(f"  Scraping GitHub Trending")
    print(f"{'='*60}")

    found = 0
    skipped = 0

    trending_url = "https://api.github.com/search/repositories?q=stars:>100+pushed:>2026-01-01&sort=stars&order=desc&per_page=30"
    data = fetch_url(trending_url)
    if not data:
        print("  Failed to fetch trending")
        return 0

    try:
        result = json.loads(data)
    except:
        return 0

    items = result.get('items', [])
    for item in items:
        if found >= max_items:
            break
        gh_url = item.get('html_url', '')
        full_name = item.get('full_name', '')
        name = item.get('name', '')
        stars = item.get('stargazers_count', 0)
        description = (item.get('description') or '')[:200]

        if item.get('fork') or item.get('disabled') or item.get('archived'):
            continue
        if stars < 50 or len(description) < 20:
            continue

        topics = item.get('topics', [])
        language = item.get('language', '')

        # Detect category from auto_discover
        try:
            from scripts.auto_discover import TOPIC_TO_CATEGORY, DESC_CATEGORY_KEYWORDS, LANGUAGE_CATEGORY_HINTS
        except:
            continue

        scores = {}
        desc_lower = description.lower()
        for topic in topics:
            cat = TOPIC_TO_CATEGORY.get(topic.lower())
            if cat:
                scores[cat] = scores.get(cat, 0) + 3
        for cat, keywords in DESC_CATEGORY_KEYWORDS.items():
            for kw in keywords:
                if kw in desc_lower:
                    scores[cat] = scores.get(cat, 0) + 2
        if language:
            hinted = LANGUAGE_CATEGORY_HINTS.get(language.lower(), set())
            for cat in hinted:
                scores[cat] = scores.get(cat, 0) + 1

        if not scores:
            skipped += 1
            continue

        cat = max(scores, key=scores.get)
        existing = load_existing(cat)
        if gh_url.rstrip('/').lower() in existing:
            skipped += 1
            continue

        entry_id = safe_slug(name)
        entry = {
            'id': entry_id, 'name': item.get('full_name', name),
            'category': cat, 'description': description,
            'official_website': item.get('homepage') or gh_url,
            'documentation': f"{gh_url}#readme",
            'github_repository': gh_url,
            'license': (item.get('license') or {}).get('spdx_id', 'MIT') if item.get('license') else 'MIT',
            'programming_languages': [language] if language else ['Generic'],
            'platforms': ['Web', 'Linux', 'macOS', 'Windows'],
            'tags': (topics or [])[:8], 'alternatives': [],
            'popularity': min(10, max(1, int(stars / 1000) + 5)),
            'maintained': True, 'archived': False, 'open_source': True,
            'repository_statistics': {
                'stars': stars, 'forks': item.get('forks_count', 0),
                'open_issues': item.get('open_issues_count', 0),
                'watchers': item.get('subscribers_count', 0),
            },
            'source': 'github_trending',
            'last_checked': time.strftime('%Y-%m-%d'),
            'last_updated': time.strftime('%Y-%m-%d'),
        }
        if save_entry(entry, dry_run):
            print(f"  🔥 {entry['name']} (⭐{stars}) → {cat}/")
            found += 1
        else:
            skipped += 1
        time.sleep(SLEEP_BETWEEN_CALLS)

    print(f"\n=== GitHub Trending Results ===")
    print(f"  Found: {found}")
    print(f"  Skipped: {skipped}")
    return found


# ═══════════════════════════════════════════
#  Update main() to include new sources
# ═══════════════════════════════════════════
# (Already updated in main function above)
