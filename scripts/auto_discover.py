#!/usr/bin/env python3
"""
Auto-discover new developer resources from GitHub and add them to the database.
Now with quality filters, smart categorization, and validation rollback.

Usage:
    python scripts/auto_discover.py                         # Normal run
    python scripts/auto_discover.py --dry-run               # Preview only
    python scripts/auto_discover.py --min-stars 50          # Higher quality threshold
    python scripts/auto_discover.py --proposals             # Review pending proposals

Requires: GITHUB_TOKEN env var
"""

import json, os, sys, time, re, glob, math, locale, shutil
locale.setlocale(locale.LC_ALL, 'C')
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "schemas" / "project.schema.json"
PROPOSALS_DIR = REPO_ROOT / ".proposals"

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
HEADERS = {'User-Agent': 'DeveloperHub/1.0'}
if GITHUB_TOKEN:
    HEADERS['Authorization'] = f'Bearer {GITHUB_TOKEN}'

# ─────────────────────── Quality Settings ───────────────────────
MIN_STARS = 10
MIN_DESC_LENGTH = 30
MAX_PROPOSALS_PER_CATEGORY = 10
SLEEP_BETWEEN_CALLS = 0.3

# ─────────────────────── Category Topics Map ───────────────────────
TOPIC_TO_CATEGORY = {
    'android': 'android', 'android-sdk': 'android', 'kotlin': 'android',
    'android-ndk': 'android', 'gradle': 'android', 'android-studio': 'android',
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
    'prebuilt': 'binary', 'prebuilt-binary': 'binary', 'portable': 'binary',
    'static-binary': 'binary', 'pre-compiled': 'binary',
    'appimage': 'binary', 'portable-app': 'binary',
}

# ─────────────────────── Smarter Language→Category hints ───────────────────────
LANGUAGE_CATEGORY_HINTS = {
    'python': {'backend', 'ai', 'languages', 'devops', 'cloud'},
    'javascript': {'frontend', 'backend', 'languages'},
    'typescript': {'frontend', 'backend', 'languages'},
    'java': {'android', 'backend', 'languages'},
    'kotlin': {'android', 'backend', 'languages'},
    'go': {'backend', 'devops', 'cloud', 'languages'},
    'rust': {'languages', 'tools', 'backend'},
    'swift': {'macos', 'mobile', 'languages'},
    'c++': {'languages', 'game-development', 'embedded', 'firmware'},
    'c': {'embedded', 'firmware', 'languages', 'operating-systems'},
    'ruby': {'backend', 'languages'},
    'php': {'backend', 'languages'},
    'dart': {'mobile', 'frontend', 'languages'},
    'r': {'ai', 'languages'},
    'shell': {'cli-tools', 'devops', 'linux'},
    'dockerfile': {'containers', 'devops'},
    'html': {'frontend', 'web'},
    'css': {'frontend', 'web'},
}

DESC_CATEGORY_KEYWORDS = {
    'backend': ['web framework', 'backend', 'server', 'rest api', 'api framework', 'http server', 'middleware'],
    'frontend': ['frontend', 'ui', 'component', 'react', 'vue', 'angular', 'css', 'web app'],
    'ai': ['machine learning', 'deep learning', 'artificial intelligence', 'llm', 'neural', 'nlp', 'gpt', 'tensorflow', 'pytorch'],
    'database': ['database', 'sql', 'nosql', 'data store', 'cache', 'key-value', 'orm'],
    'mobile': ['mobile', 'ios', 'android app', 'cross-platform'],
    'devops': ['devops', 'ci/cd', 'deployment', 'infrastructure', 'monitoring', 'observability'],
    'security': ['security', 'encryption', 'authentication', 'vulnerability', 'penetration'],
    'tools': ['developer tool', 'cli', 'command line', 'productivity'],
    'binary': ['prebuilt', 'pre-compiled', 'pre compiled', 'portable', 'appimage', 'binary distribution', 'compiled binary', 'executable', 'standalone binary', 'binary release', 'download binary', 'wheel', 'whl'],
    'cloud': ['cloud', 'serverless', 'saas', 'paas'],
    'game-development': ['game', 'game engine', 'gamedev', '3d', 'rendering'],
}

# ─────────────────────── Strict Exclusion Patterns ───────────────────────
EXCLUDE_PATTERNS = [
    # Non-tool / learning resources
    'awesome-', 'awesome-list', 'free-programming', 'free-books',
    '-books', '-tutorial', '-guide', '-course', '-learning',
    'cs-video-courses', 'developer-roadmap', 'build-your-own-x',
    'project-based-learning', 'system-design', 'system-design',
    'interview-', 'cheatsheet', 'cheat-sheet',
    'tldr-pages', 'tldr', 'freecodecamp', 'leetcode',
    'javascript-algorithms', 'python-interview',
    'the-book-of', 'rust-book',
    'notes', '-notes', 'notebook',
    # Personal / config / boilerplate
    'dotfiles', 'config', 'dotfile',
    'boilerplate', 'starter', 'template', 'scaffold', 'scaffolding',
    'sandbox', 'playground', 'play-around', 'playground',
    'demo-app', 'sample-app', 'example', 'hello-world', 'helloworld',
    'my-', 'test-', 'learn-', 'practice-',
    'nvim-config', 'vimrc', 'vim-config', 'zshrc', 'bashrc',
    'starter-kit', 'starter-template', 'kickstart',
    # Malware only (educational security tools are allowed)
    'malware',
    'whatsapp-hack', 'instagram-hack', 'facebook-hack',  # Targeted harassment
    'termux-social', 'termux-extra', 'termux-style',
    # Non-relevant
    'termux-boot', 'termux-tasker', 'termux-styling',
    'android-tv', 'android-auto', 'android-wear', 'android-things',
    'game-assets', 'game-data', 'roms', 'iso', 'firmware-dump',
]

DESC_BLOCK_KEYWORDS = [
    'book', 'tutorial', 'learn', 'guide', 'course',
    'notes', 'interview', 'cheat sheet', 'awesome list',
    'curated list', 'awesome ', 'resources for',
    'my personal', 'dotfiles', 'config files',
    'sample project', 'demo project', 'tutorial project',
    'starter template', 'boilerplate', 'playground',
]

# ─────────────────────── API Helper ───────────────────────
def gh_api(path):
    url = f"https://api.github.com{path}"
    req = Request(url, headers=HEADERS)
    for attempt in range(3):
        try:
            with urlopen(req, timeout=15) as r:
                return json.loads(r.read())
        except HTTPError as e:
            body = e.read().decode()
            if e.code == 403 and 'rate limit' in body.lower():
                reset_time = int(dict(e.headers).get('X-RateLimit-Reset', time.time() + 60))
                wait = max(reset_time - time.time(), 1) + 5
                print(f"  ⏳ Rate limited. Waiting {int(wait)}s...")
                time.sleep(wait)
                continue
            if e.code == 404:
                return None
            print(f"  ⚠️  GitHub API error {e.code}: {body[:100]}")
            return None
        except Exception as e:
            if attempt < 2:
                time.sleep(2)
                continue
            return None
    return None

# ─────────────────────── Smart Category Detection ───────────────────────
def detect_category(name, description, topics, language, search_category):
    """Detect best category using all signals."""
    scores = {}
    desc_lower = (description or '').lower()
    name_lower = name.lower()

    # 1. Score from topics
    for topic in topics:
        cat = TOPIC_TO_CATEGORY.get(topic)
        if cat:
            scores[cat] = scores.get(cat, 0) + 3

    # 2. Score from language hints
    if language:
        lang_key = language.lower()
        hinted = LANGUAGE_CATEGORY_HINTS.get(lang_key, set())
        for cat in hinted:
            scores[cat] = scores.get(cat, 0) + 2

    # 3. Score from description keywords
    for cat, keywords in DESC_CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in desc_lower:
                scores[cat] = scores.get(cat, 0) + 2

    # 4. Penalty for generic language-only detection
    if language and not topics and not any(kw in desc_lower for kws in DESC_CATEGORY_KEYWORDS.values() for kw in kws):
        # Language alone without context → likely belongs to its natural category
        lang_cats = LANGUAGE_CATEGORY_HINTS.get(language.lower(), set())
        if len(lang_cats) <= 2:
            pass  # keep existing scores
        else:
            # Generic language — reduce confidence
            for cat in list(scores.keys()):
                scores[cat] = scores.get(cat, 0) - 1

    # 5. Fallback: use the search category
    if not scores:
        return search_category

    # 6. Pick best — if confident enough
    best_cat = max(scores, key=scores.get)
    best_score = scores[best_cat]

    # Very low confidence? Keep search category
    if best_score < 2:
        return search_category

    # If search category is also valid and close, prefer it (avoids category drift)
    if search_category in scores and scores.get(search_category, 0) >= best_score - 1:
        return search_category

    return best_cat


def is_quality_entry(item, repo_data, description):
    """Check if repo is a quality developer resource."""
    stars = item.get('stargazers_count', 0)
    language = item.get('language')
    topics = item.get('topics', [])

    # Must have minimum stars
    if stars < MIN_STARS:
        return False, f"Too few stars ({stars} < {MIN_STARS})"

    # Must have a real description
    desc = (description or '').strip()
    if len(desc) < MIN_DESC_LENGTH:
        return False, f"Description too short ({len(desc)} < {MIN_DESC_LENGTH})"

    # Must have detectable language or topics
    if not language and not topics:
        return False, "No language or topics detected"

    # Must not be a fork (usually personal copies)
    if item.get('fork', False):
        return False, "Is a fork"

    # Description must not be tutorial/docs
    desc_lower = desc.lower()
    for kw in DESC_BLOCK_KEYWORDS:
        if kw in desc_lower:
            return False, f"Description contains blocked keyword: '{kw}'"

    # Check if repo has actual content (not empty)
    if repo_data:
        size = repo_data.get('size', 0)
        if size < 10:  # Less than 10KB — basically empty
            return False, f"Repo too small ({size}KB)"

    return True, ""


def load_proposals():
    """Load all pending proposals from .proposals/ directory."""
    proposals = []
    if PROPOSALS_DIR.exists():
        for f in PROPOSALS_DIR.glob('*.json'):
            try:
                with open(f) as fh:
                    data = json.load(fh)
                    proposals.append((f, data))
            except Exception:
                pass
    return proposals


def save_proposal(entry):
    """Save a new entry as a proposal instead of directly to category."""
    PROPOSALS_DIR.mkdir(exist_ok=True)
    filepath = PROPOSALS_DIR / f"{entry['id']}.json"
    entry['_proposed_at'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    with open(filepath, 'w') as f:
        json.dump(entry, f, indent=2)
    return filepath


def validate_and_commit(filepath):
    """Validate a JSON file against schema. If fails, remove it. Returns (success, message)."""
    try:
        import jsonschema
        from jsonschema import validate, ValidationError
    except ImportError:
        # jsonschema not installed, skip validation
        return True, "Skipped (jsonschema not installed)"

    try:
        # Load schema
        with open(SCHEMA_PATH) as f:
            schema = json.load(f)

        # Load entry
        with open(filepath) as f:
            data = json.load(f)

        # Check category matches directory
        parent_dir = filepath.resolve().parent.name
        entry_category = data.get("category", "")
        if parent_dir in CATEGORIES and entry_category != parent_dir:
            filepath.unlink()
            return False, f"Category mismatch: dir='{parent_dir}' field='{entry_category}' — deleted"

        # Validate schema
        validate(instance=data, schema=schema)
        return True, "Valid"

    except (json.JSONDecodeError, ValidationError) as e:
        filepath.unlink()
        return False, f"Validation failed: {e} — deleted"
    except Exception as e:
        filepath.unlink()
        return False, f"Error: {e} — deleted"


def commit_proposal(prop_path, prop_data):
    """Move a proposal to its proper category folder after validation."""
    category = prop_data.get('category', 'tools')
    entry_id = prop_data.get('id', prop_path.stem)

    cat_dir = REPO_ROOT / category
    cat_dir.mkdir(exist_ok=True)
    target = cat_dir / f"{entry_id}.json"

    # Remove internal fields before saving
    final_entry = {k: v for k, v in prop_data.items() if not k.startswith('_')}
    final_entry['auto_discovered'] = True
    final_entry['quality_score'] = calculate_quality_score(final_entry)

    with open(target, 'w') as f:
        json.dump(final_entry, f, indent=2)

    # Validate and rollback on failure
    success, msg = validate_and_commit(target)
    if success:
        prop_path.unlink()  # Remove proposal
        print(f"    ✅ Committed → {category}/{entry_id}.json")
    else:
        print(f"    ❌ {msg}")
        # File already deleted by validate_and_commit on failure
        prop_path.unlink() if prop_path.exists() else None

    return success, msg


def calculate_quality_score(entry):
    """Calculate a quality score (0-100) for an entry."""
    score = 0
    stats = entry.get('repository_statistics', {})

    # Stars (0-40 points)
    stars = stats.get('stars', 0)
    if stars >= 10000: score += 40
    elif stars >= 5000: score += 35
    elif stars >= 1000: score += 30
    elif stars >= 500: score += 25
    elif stars >= 100: score += 20
    elif stars >= 50: score += 15
    elif stars >= 10: score += 10

    # Description (0-15 points)
    desc = entry.get('description', '')
    if len(desc) >= 100: score += 15
    elif len(desc) >= 50: score += 10
    elif len(desc) >= 30: score += 5

    # Has documentation (0-10 points)
    if entry.get('documentation') and 'readme' not in (entry.get('documentation') or ''):
        score += 10
    elif entry.get('documentation'):
        score += 5

    # Has official website (0-10 points)
    if entry.get('official_website') and 'github.com' not in (entry.get('official_website') or ''):
        score += 10

    # Programming languages (0-10 points)
    langs = entry.get('programming_languages', [])
    if len(langs) > 1:
        score += 10
    elif len(langs) == 1 and langs[0] != 'Generic':
        score += 5

    # Tags (0-10 points)
    tags = entry.get('tags', [])
    if len(tags) >= 5: score += 10
    elif len(tags) >= 3: score += 7
    elif len(tags) >= 1: score += 3

    # Maintained (0-5 points)
    if entry.get('maintained', True):
        score += 5

    return min(score, 100)


# ─────────────────────── Main Discovery ───────────────────────
CATEGORY_QUERIES = {
    'ai': ['ai', 'machine-learning', 'deep-learning', 'llm'],
    'android': ['android', 'kotlin', 'android-sdk'],
    'android-tools': ['android-tool', 'adb', 'android-debug', 'android-devtools'],
    'backend': ['backend', 'rest-api', 'graphql', 'api'],
    'binary': ['prebuilt-binary', 'prebuilt', 'static-binary', 'appimage', 'portable-app', 'binary-release', 'compiled-binary'],
    'blockchain': ['blockchain', 'ethereum', 'web3', 'solidity'],
    'cli-tools': ['cli', 'cli-tool', 'command-line', 'tui'],
    'cloud': ['cloud', 'serverless', 'aws', 'gcp'],
    'containers': ['docker', 'kubernetes', 'container'],
    'database': ['database', 'sql', 'nosql', 'postgresql'],
    'desktop': ['desktop', 'electron', 'qt'],
    'devops': ['devops', 'ci', 'cd', 'monitoring'],
    'embedded': ['embedded', 'microcontroller'],
    'firmware': ['firmware', 'esp32', 'esp8266'],
    'frameworks': ['framework', 'web-framework'],
    'frontend': ['frontend', 'react', 'vue', 'angular', 'svelte'],
    'game-development': ['game-development', 'game-engine', 'unity'],
    'iot': ['iot', 'arduino', 'raspberry-pi'],
    'languages': ['python', 'golang', 'rust', 'typescript', 'java'],
    'libraries': ['library', 'libraries'],
    'linux': ['linux', 'bash', 'unix'],
    'machine-learning': ['machine-learning', 'deep-learning', 'tensorflow', 'pytorch'],
    'macos': ['macos', 'apple', 'swift'],
    'mobile': ['mobile', 'ios', 'flutter', 'react-native'],
    'network': ['network', 'networking', 'proxy'],
    'operating-systems': ['operating-system', 'os'],
    'robotics': ['robotics', 'ros'],
    'security': ['security', 'authentication', 'encryption'],
    'termux': ['termux', 'termux-repo', 'termux-package'],
    'tools': ['tool', 'developer-tool', 'productivity'],
    'web': ['web', 'html', 'css'],
    'windows': ['windows', 'dotnet'],
}

CATEGORIES = set(CATEGORY_QUERIES.keys())


def discover_new_entries(max_per_category=10, dry_run=False):
    """Discover new developer resources from GitHub."""
    print(f"🔍 Auto-Discovery (min ⭐{MIN_STARS}, max {max_per_category}/category)")
    if dry_run:
        print("   DRY RUN — no files will be created")

    discovered = []
    proposal_count = 0

    # Load existing entries to avoid duplicates
    existing_ids = set()
    existing_gh = set()
    existing_names = set()
    for cat_dir in CATEGORIES:
        d = REPO_ROOT / cat_dir
        if d.exists():
            for f in d.glob('*.json'):
                try:
                    with open(f) as fh:
                        data = json.load(fh)
                        existing_ids.add(data.get('id', ''))
                        existing_gh.add(data.get('github_repository', '').rstrip('/').lower())
                        existing_names.add(data.get('name', '').lower())
                except Exception:
                    pass

    # Also check proposals
    for prop_path, prop_data in load_proposals():
        existing_ids.add(prop_data.get('id', ''))
        existing_gh.add(prop_data.get('github_repository', '').rstrip('/').lower())

    for category, queries in CATEGORY_QUERIES.items():
        found = 0
        for query_topic in queries:
            if found >= max_per_category:
                break

            # Skip if already have enough proposals in queue
            existing_in_cat = sum(1 for _, p in load_proposals() if p.get('category') == category)
            if existing_in_cat >= MAX_PROPOSALS_PER_CATEGORY:
                continue

            q = f"q=topic:{query_topic}+stars:>={MIN_STARS}&sort=stars&per_page=30"
            results = gh_api(f'/search/repositories?{q}')
            if not results or 'items' not in results:
                continue

            for item in results['items']:
                if found >= max_per_category:
                    break

                name = item['name']
                full_name = item['full_name']
                gh_url = f"https://github.com/{full_name}".lower()

                # ── Blocklist check ──
                skip = False
                for pat in EXCLUDE_PATTERNS:
                    if pat.lower() in name.lower() or pat.lower() in full_name.lower():
                        skip = True
                        break
                if skip:
                    continue

                # ── Duplicate check ──
                if gh_url in existing_gh or name.lower() in existing_names:
                    continue

                if name.lower() in ('project', 'app', 'demo', 'test', 'my-project', 'sample'):
                    continue

                # ── Quality check ──
                topics = item.get('topics', [])
                language = item.get('language')
                description = item.get('description', '') or ''

                ok, reason = is_quality_entry(item, None, description)
                if not ok:
                    continue

                # Must have real code (skip docs-only)
                if not language and not topics:
                    continue

                # Get full repo data
                repo_data = gh_api(f'/repos/{full_name}')
                if not repo_data:
                    continue
                if repo_data.get('archived', False):
                    continue

                # Re-check with repo_data (size check)
                ok, reason = is_quality_entry(item, repo_data, description)
                if not ok:
                    continue

                # ── Category detection ──
                detected_cat = detect_category(name, description, topics, language, category)

                # Cross-check: if detected category doesn't match search category,
                # verify it's related (avoid category drift)
                if detected_cat != category:
                    if not repo_data:
                        continue

                # ── Build entry ──
                entry_id = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
                if not entry_id or entry_id in existing_ids:
                    entry_id = f"{entry_id}-{detected_cat}" if entry_id else f"{detected_cat}-{int(time.time())}"

                license_spdx = None
                if repo_data.get('license'):
                    license_spdx = repo_data['license'].get('spdx_id') or repo_data['license'].get('key')

                # Smart platform detection
                if detected_cat == 'termux':
                    plats = ["Termux", "Android", "Linux"]
                elif detected_cat == 'android-tools':
                    plats = ["Android", "Linux", "Windows", "macOS"]
                elif detected_cat == 'binary':
                    has_win = 'windows' in (description or '').lower() or any('win' in (t or '') for t in (topics or []))
                    has_mac = 'macos' in (description or '').lower() or 'macos' in (topics or [])
                    has_termux = 'termux' in (description or '').lower() or 'termux' in (topics or [])
                    plats = ["Linux"]
                    if has_win: plats.append("Windows")
                    if has_mac: plats.append("macOS")
                    if has_termux: plats.append("Termux")
                elif detected_cat == 'cli-tools':
                    plats = ["Linux", "macOS", "Windows", "Termux"]
                elif detected_cat in ('android', 'mobile'):
                    plats = ["Android", "iOS", "Linux", "macOS", "Windows"]
                elif detected_cat in ('game-development',):
                    plats = ["Windows", "macOS", "Linux", "Web"]
                elif detected_cat in ('web', 'frontend'):
                    plats = ["Web", "Linux", "macOS", "Windows"]
                elif detected_cat in ('embedded', 'firmware', 'iot', 'robotics'):
                    plats = ["Linux", "Embedded"]
                else:
                    plats = ["Web", "Linux", "macOS", "Windows", "Android", "Termux"]

                entry = {
                    "id": entry_id,
                    "name": item['name'],
                    "category": detected_cat,
                    "description": description.strip()[:200],
                    "official_website": repo_data.get('homepage') or f"https://github.com/{full_name}",
                    "documentation": f"https://github.com/{full_name}#readme",
                    "github_repository": f"https://github.com/{full_name}",
                    "license": license_spdx or "MIT",
                    "programming_languages": [language] if language else ["Generic"],
                    "platforms": plats,
                    "tags": (topics or [])[:8],
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
                    "auto_discovered": True,
                }

                # ── Save as proposal ──
                if not dry_run:
                    prop_path = save_proposal(entry)
                    proposal_count += 1
                    print(f"  📄 Proposal: +{entry['name']} ({detected_cat}) ⭐{item.get('stargazers_count', 0)} → .proposals/{entry_id}.json")
                else:
                    print(f"  📄 [DRY RUN] Would propose: +{entry['name']} ({detected_cat}) ⭐{item.get('stargazers_count', 0)}")

                discovered.append(entry)
                existing_ids.add(entry_id)
                existing_gh.add(gh_url)
                existing_names.add(name.lower())
                found += 1
                time.sleep(SLEEP_BETWEEN_CALLS)

        if found == 0:
            print(f"  No new entries for '{category}'")

    print(f"\n=== Summary ===")
    print(f"Proposed: {len(discovered)} new entries")
    if dry_run:
        print(f"(dry run — no files created)")
    else:
        print(f"Proposals saved to .proposals/ — run with --commit to finalize")

    return discovered


def commit_all_proposals():
    """Validate and commit all pending proposals."""
    proposals = load_proposals()
    if not proposals:
        print("No pending proposals found.")
        return

    print(f"📦 Processing {len(proposals)} proposals...")
    committed = 0
    failed = 0

    for prop_path, prop_data in proposals:
        print(f"  Checking: {prop_data.get('name', prop_path.stem)} ({prop_data.get('category', '?')})")
        success, msg = commit_proposal(prop_path, prop_data)
        if success:
            committed += 1
        else:
            failed += 1
        time.sleep(0.1)

    print(f"\n=== Results ===")
    print(f"  ✅ Committed: {committed}")
    print(f"  ❌ Failed/Removed: {failed}")


if __name__ == '__main__':
    dry_run = '--dry-run' in sys.argv
    do_commit = '--commit' in sys.argv

    max_per_cat = 10
    for a in sys.argv:
        if a.startswith('--max-per-category='):
            max_per_cat = int(a.split('=')[1])
        if a.startswith('--min-stars='):
            MIN_STARS = int(a.split('=')[1])

    if do_commit:
        commit_all_proposals()
    else:
        discover_new_entries(max_per_cat, dry_run)
        if not dry_run:
            print(f"\n💡 Run with --commit to validate and move proposals to categories")
            print(f"   Or review proposals in .proposals/ directory")
