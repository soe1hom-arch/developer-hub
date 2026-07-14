#!/usr/bin/env python3
"""
Category Rules Engine — aturan deteksi & validasi per kategori.
Setiap kategori punya: must-have signals, must-NOT-have signals, dan specific checks.

Digunakan oleh: quality_check.py, auto_discover.py
"""

# ─── MUST-HAVE: keywords yang WAJIB ada untuk kategori ini ───
CATEGORY_MUST_HAVE = {
    "ai": {
        "keywords": ["artificial intelligence", "machine learning", "deep learning",
                     "neural network", "nlp", "llm", "gpt", "transformer",
                     "computer vision", "ai model", "ai framework", "inference",
                     "diffusion model", "language model", "embedding", "vector database"],
        "languages": ["python", "c++", "cuda"],
        "topics": ["ai", "machine-learning", "deep-learning", "llm", "nlp"],
        "must_not_keywords": ["game", "frontend", "ui component", "css"],
        "description_min_length": 50,
    },
    "android": {
        "keywords": ["android", "android sdk", "android app", "android library",
                     "jetpack", "material design", "google play", "apk", "aab",
                     "kotlin multiplatform"],
        "languages": ["kotlin", "java", "groovy"],
        "topics": ["android", "kotlin", "android-sdk", "jetpack", "androidx"],
        "must_not_keywords": ["ios only", "swift ui", "iphone", "cocoa"],
        "description_min_length": 40,
    },
    "android-tools": {
        "keywords": ["adb", "fastboot", "android debug", "android tool", "sideload",
                     "android recovery", "bootloader", "android rom", "dalm",
                     "android utility", "android device"],
        "languages": ["python", "shell", "java", "kotlin"],
        "topics": ["android-tool", "adb", "fastboot", "android-debug", "android-utility"],
        "must_not_keywords": ["android app", "android library", "jetpack"],
    },
    "api": {
        "keywords": ["api", "rest api", "graphql", "grpc", "openapi", "swagger",
                     "api gateway", "api client", "api wrapper", "api sdk"],
        "languages": [],
        "topics": ["api", "rest-api", "graphql", "grpc", "openapi"],
        "must_not_keywords": ["ui", "frontend", "game", "desktop"],
    },
    "backend": {
        "keywords": ["backend", "server", "web framework", "http server",
                     "microservice", "api server", "server-side", "middleware",
                     "web application", "mvc framework"],
        "languages": ["python", "javascript", "typescript", "go", "rust", "java",
                      "php", "ruby", "c#", "elixir"],
        "topics": ["backend", "web-framework", "rest-api", "server", "microservice"],
        "must_not_keywords": ["frontend", "ui component", "css framework", "game engine"],
    },
    "binary": {
        "keywords": ["prebuilt", "pre-compiled", "standalone binary", "portable app",
                     "binary release", "download binary", "appimage", "executable",
                     "compiled binary", "binary distribution", "portable executable",
                     "single binary", "static binary"],
        "languages": ["go", "rust", "c", "c++", "zig"],
        "topics": ["prebuilt-binary", "prebuilt", "binary-release", "appimage",
                   "portable-app", "static-binary", "compiled-binary"],
        "must_not_keywords": ["library", "framework", "sdk", "api wrapper",
                              "source code", "build from source"],
        "checks": ["has_releases", "has_assets"],
    },
    "blockchain": {
        "keywords": ["blockchain", "ethereum", "web3", "solidity", "cryptocurrency",
                     "smart contract", "defi", "nft", "dapp", "token", "crypto",
                     "distributed ledger", "bitcoin", "wallet", "consensus"],
        "languages": ["solidity", "rust", "go", "javascript", "typescript", "python"],
        "topics": ["blockchain", "ethereum", "web3", "solidity", "cryptocurrency"],
        "must_not_keywords": ["game", "frontend", "mobile app", "desktop"],
    },
    "cli-tools": {
        "keywords": ["cli", "command line", "terminal", "shell", "command-line",
                     "tui", "terminal ui", "console", "cli tool", "command line utility"],
        "languages": ["go", "rust", "python", "typescript", "c", "c++"],
        "topics": ["cli", "cli-tool", "command-line", "tui", "terminal"],
        "must_not_keywords": ["library", "framework", "gui", "desktop app"],
    },
    "cloud": {
        "keywords": ["cloud", "aws", "azure", "gcp", "google cloud", "amazon web services",
                     "cloud computing", "cloud storage", "cloud function", "serverless",
                     "cloud infrastructure", "cloud native", "iaas", "paas", "saas"],
        "languages": [],
        "topics": ["cloud", "aws", "azure", "gcp", "serverless", "cloud-computing"],
        "must_not_keywords": ["game", "frontend", "mobile"],
    },
    "containers": {
        "keywords": ["container", "docker", "kubernetes", "k8s", "podman",
                     "container orchestration", "container runtime", "service mesh",
                     "istio", "containerd", "cri-o", "docker image"],
        "languages": ["go", "rust"],
        "topics": ["docker", "kubernetes", "container", "k8s", "podman"],
        "must_not_keywords": ["frontend", "game", "mobile"],
    },
    "database": {
        "keywords": ["database", "sql", "nosql", "data store", "orm", "query",
                     "indexing", "data warehouse", "data lake", "rdbms",
                     "postgresql", "mysql", "mongodb", "redis", "sqlite",
                     "cassandra", "elasticsearch", "clickhouse", "data pipeline"],
        "languages": ["go", "rust", "c", "c++", "java", "python"],
        "topics": ["database", "sql", "nosql", "postgresql", "mysql", "redis",
                   "mongodb", "sqlite", "data-pipeline", "data-engineering"],
        "must_not_keywords": ["frontend", "ui", "game", "mobile app"],
    },
    "desktop": {
        "keywords": ["desktop", "electron", "qt", "gtk", "wxwidgets", "javafx",
                     "swing", "winforms", "wpf", "native app", "desktop application",
                     "cross-platform desktop"],
        "languages": ["c++", "c#", "java", "python", "javascript", "typescript", "rust"],
        "topics": ["desktop", "electron", "qt", "gtk", "javafx", "desktop-app"],
        "must_not_keywords": ["mobile", "web", "backend", "cli"],
    },
    "devops": {
        "keywords": ["devops", "ci/cd", "continuous integration", "continuous deployment",
                     "jenkins", "github actions", "gitlab ci", "ansible", "terraform",
                     "infrastructure as code", "iac", "monitoring", "observability",
                     "prometheus", "grafana", "sre", "incident management"],
        "languages": ["go", "python", "ruby", "hcl"],
        "topics": ["devops", "ci", "cd", "monitoring", "iac", "infrastructure"],
        "must_not_keywords": ["frontend", "game", "mobile"],
    },
    "embedded": {
        "keywords": ["embedded", "microcontroller", "arm", "risc-v", "rtos",
                     "bare metal", "driver", "firmware", "stm32", "avr",
                     "embedded system", "mcu", "esp32", "esp8266"],
        "languages": ["c", "c++", "rust", "assembly"],
        "topics": ["embedded", "microcontroller", "rtos", "arm", "risc-v"],
        "must_not_keywords": ["web", "mobile", "desktop", "game"],
    },
    "firmware": {
        "keywords": ["firmware", "bios", "uefi", "bootloader", "microcode",
                     "device firmware", "embedded firmware", "firmware update"],
        "languages": ["c", "c++", "rust", "assembly"],
        "topics": ["firmware", "uefi", "bios", "bootloader"],
        "must_not_keywords": ["web", "mobile", "desktop", "game", "app"],
    },
    "frameworks": {
        "keywords": ["framework", "web framework", "application framework",
                     "full-stack", "meta-framework", "development framework"],
        "languages": [],
        "topics": ["framework", "web-framework", "meta-framework"],
        "must_not_keywords": ["library", "tool", "cli", "ui component"],
        "should_not": ["simple", "lightweight wrapper", "small library"],
    },
    "frontend": {
        "keywords": ["frontend", "ui framework", "css framework", "ui component",
                     "react", "vue", "angular", "svelte", "web ui",
                     "component library", "design system", "ui kit"],
        "languages": ["javascript", "typescript", "css", "html"],
        "topics": ["frontend", "react", "vue", "angular", "svelte", "css", "ui"],
        "must_not_keywords": ["backend", "server", "database", "game engine"],
    },
    "game-development": {
        "keywords": ["game engine", "game framework", "game development", "3d rendering",
                     "game", "gamedev", "3d graphics", "unity", "unreal", "godot",
                     "sprite", "animation", "physics engine"],
        "languages": ["c#", "c++", "javascript", "python", "rust", "lua", "gdscript"],
        "topics": ["game-development", "game-engine", "unity", "godot", "unreal"],
        "must_not_keywords": ["backend", "database", "enterprise", "business"],
    },
    "iot": {
        "keywords": ["iot", "internet of things", "arduino", "raspberry pi",
                     "sensor", "home assistant", "smart home", "mqtt",
                     "esp32", "esp8266", "microcontroller"],
        "languages": ["c", "c++", "python", "javascript"],
        "topics": ["iot", "arduino", "raspberry-pi", "home-assistant", "mqtt"],
        "must_not_keywords": ["game", "frontend", "mobile app"],
    },
    "languages": {
        "keywords": ["programming language", "compiler", "interpreter", "language",
                     "type system", "parser", "lexer", "syntax", "language server"],
        "languages": [],
        "topics": ["programming-language", "compiler", "language", "interpreter"],
        "must_not_keywords": ["framework", "library for", "sdk", "tool for"],
        "special": "language_implementation",
    },
    "libraries": {
        "keywords": ["library", "sdk", "client library", "wrapper", "api client",
                     "package for", "driver for", "sdk for"],
        "languages": [],
        "topics": ["library", "libraries", "sdk", "client-library"],
        "must_not_keywords": ["framework", "application", "game", "tool", "cli",
                              "server", "app", "platform", "engine"],
        "checks": ["package_registry"],
    },
    "linux": {
        "keywords": ["linux", "unix", "linux tool", "linux utility", "linux desktop",
                     "linux kernel", "systemd", "linux package", "linux app"],
        "languages": ["c", "c++", "rust", "python", "shell"],
        "topics": ["linux", "unix", "linux-tool", "linux-desktop", "linux-utility"],
        "must_not_keywords": ["windows only", "macos only", "ios"],
    },
    "machine-learning": {
        "keywords": ["machine learning", "deep learning", "model training",
                     "ml pipeline", "mlops", "feature engineering", "model serving",
                     "hyperparameter", "training pipeline", "model deployment"],
        "languages": ["python", "c++", "cuda", "julia"],
        "topics": ["machine-learning", "deep-learning", "mlops", "ml-pipeline"],
        "must_not_keywords": ["game", "frontend", "mobile"],
        "description_min_length": 60,
    },
    "macos": {
        "keywords": ["macos", "mac os", "apple", "swift", "cocoa", "appkit",
                     "mac app", "mac application", "macos utility", "osx"],
        "languages": ["swift", "objective-c", "c", "c++"],
        "topics": ["macos", "apple", "swift", "osx", "macos-app", "cocoa"],
        "must_not_keywords": ["windows only", "linux only", "android"],
    },
    "mobile": {
        "keywords": ["mobile", "ios", "flutter", "react native", "cross-platform mobile",
                     "mobile app", "iphone", "ipad", "mobile development",
                     "swift ui", "kotlin multiplatform mobile"],
        "languages": ["dart", "swift", "objective-c", "kotlin", "javascript", "typescript", "c#"],
        "topics": ["mobile", "ios", "flutter", "react-native", "swift", "mobile-app"],
        "must_not_keywords": ["desktop", "backend", "server", "web frontend"],
    },
    "network": {
        "keywords": ["network", "networking", "proxy", "http", "tcp/ip", "dns",
                     "load balancer", "vpn", "protocol", "packet", "bandwidth",
                     "reverse proxy", "api gateway", "http client", "http server"],
        "languages": ["go", "rust", "c", "c++", "python"],
        "topics": ["network", "networking", "proxy", "http", "tcp"],
        "must_not_keywords": ["game", "frontend", "mobile", "database"],
    },
    "operating-systems": {
        "keywords": ["operating system", "os kernel", "kernel", "linux kernel",
                     "freebsd", "nixos", "distro", "operating system distribution",
                     "system programming", "os development"],
        "languages": ["c", "c++", "rust", "assembly"],
        "topics": ["operating-system", "os", "kernel", "os-kernel", "linux-kernel"],
        "must_not_keywords": ["app", "tool", "library", "framework", "game"],
    },
    "robotics": {
        "keywords": ["robotics", "ros", "robot", "robot operating system",
                     "control system", "autonomous", "navigation", "slam",
                     "manipulator", "robot framework", "motion planning"],
        "languages": ["c++", "python", "c"],
        "topics": ["robotics", "ros", "robot", "robot-framework", "slam"],
        "must_not_keywords": ["game", "frontend", "mobile", "web"],
    },
    "security": {
        "keywords": ["security", "vulnerability", "encryption", "authentication",
                     "penetration testing", "cybersecurity", "malware", "exploit",
                     "firewall", "intrusion detection", "cryptography", "audit",
                     "zero trust", "access control", "identity management"],
        "languages": ["python", "go", "rust", "c", "c++", "javascript"],
        "topics": ["security", "vulnerability", "encryption", "cybersecurity"],
        "must_not_keywords": ["game", "frontend", "mobile app"],
    },
    "termux": {
        "keywords": ["termux", "termux package", "termux app", "termux api",
                     "termux tool", "proot", "android terminal", "termux addon"],
        "languages": ["shell", "python", "c", "c++"],
        "topics": ["termux", "termux-package", "termux-app", "proot"],
        "must_not_keywords": ["windows", "macos", "desktop", "ios"],
    },
    "tools": {
        "keywords": ["developer tool", "productivity tool", "utility", "devtool",
                     "code quality", "linting", "formatting", "code analysis",
                     "build tool", "package manager", "version control"],
        "languages": [],
        "topics": ["tool", "developer-tool", "productivity", "devtool"],
        "must_not_keywords": ["framework", "library", "game", "os", "kernel"],
        "catch_all": True,  # tools is catch-all, lower confidence needed
    },
    "web": {
        "keywords": ["web", "html", "css", "browser", "web technology",
                     "web standard", "web api", "web component", "wasm",
                     "webassembly", "browser extension", "web app"],
        "languages": ["javascript", "typescript", "css", "html", "wasm"],
        "topics": ["web", "html", "css", "browser", "webassembly", "web-component"],
        "must_not_keywords": ["server", "backend", "database", "mobile", "desktop"],
    },
    "windows": {
        "keywords": ["windows", "win32", "dotnet", "c#", "powershell",
                     "windows app", "windows utility", "windows desktop",
                     "uwp", "winforms", "wpf", "winui"],
        "languages": ["c#", "c++", "powershell", "visual basic", "f#"],
        "topics": ["windows", "dotnet", "csharp", "uwp", "powershell"],
        "must_not_keywords": ["linux only", "macos only", "android", "ios"],
    },
}


# ─── Scoring weights ───
SIGNAL_WEIGHTS = {
    "keyword_match": 3,       # Description keyword matches category
    "topic_match": 3,         # GitHub topic matches category
    "language_hint": 2,       # Programming language hints at category
    "name_pattern": 2,        # Project name suggests category
    "must_not_violation": -5, # Has keyword that contradicts category
    "specific_check_pass": 3, # Passes category-specific check
    "specific_check_fail": -3, # Fails category-specific check
    "catch_all_penalty": 0,   # No penalty for catch-all
}


def get_signals(entry, gh_info=None):
    """Dapatkan semua signals untuk entry terhadap semua kategori.
    Returns: dict of {category: score}
    """
    from scripts.categories import CATEGORIES
    name = (entry.get('name', '') or '').lower()
    desc = (entry.get('description', '') or '').lower()
    tags = [t.lower() for t in entry.get('tags', [])]
    langs = [l.lower() for l in entry.get('programming_languages', [])]
    entry_cat = entry.get('category', '')
    
    scores = {}
    details = {}
    
    for cat, rules in CATEGORY_MUST_HAVE.items():
        score = 0
        signals = []
        
        # Keyword match
        for kw in rules.get('keywords', []):
            if kw in desc:
                score += SIGNAL_WEIGHTS['keyword_match']
                signals.append(f"keyword: '{kw}'")
                break  # Count once per category
        
        # Topic match
        for topic in rules.get('topics', []):
            if topic in tags:
                score += SIGNAL_WEIGHTS['topic_match']
                signals.append(f"topic: '{topic}'")
                break
        
        # Language hint
        for lang in rules.get('languages', []):
            if lang in langs:
                score += SIGNAL_WEIGHTS['language_hint']
                signals.append(f"lang: '{lang}'")
                break
        
        # Name pattern
        name_words = set(name.split())
        for kw in rules.get('keywords', [])[:5]:
            kw_words = set(kw.split())
            if kw_words & name_words:  # Intersection
                score += SIGNAL_WEIGHTS['name_pattern']
                signals.append(f"name: '{kw}'")
                break
        
        # Must-not check
        for mn in rules.get('must_not_keywords', []):
            if mn in desc or mn in tags:
                score += SIGNAL_WEIGHTS['must_not_violation']
                signals.append(f"MUST_NOT: '{mn}'")
        
        # Description length
        min_desc = rules.get('description_min_length', 20)
        if len(desc) < min_desc:
            score -= 2
            signals.append(f"desc too short ({len(desc)} < {min_desc})")
        
        # Specific checks
        if 'checks' in rules:
            if gh_info:
                for check in rules['checks']:
                    if check == 'has_releases' and gh_info.get('has_releases'):
                        score += 3
                        signals.append("has releases")
                    elif check == 'has_assets' and gh_info.get('has_assets'):
                        score += 3
                        signals.append("has assets")
                    elif check == 'package_registry':
                        lang = gh_info.get('language', '')
                        if lang.lower() in ('python', 'javascript', 'typescript', 'ruby', 'php'):
                            score += 2
                            signals.append(f"package registry ({lang})")
        
        # Catch-all penalty
        if rules.get('catch_all') and score > 5:
            score -= 2  # Reduce score for catch-all categories
        
        scores[cat] = score
        details[cat] = {'score': score, 'signals': signals}
    
    return scores, details


def get_best_category(entry, gh_info=None):
    """Dapatkan kategori terbaik beserta confidence."""
    scores, details = get_signals(entry, gh_info)
    if not scores:
        return 'tools', 0.3, details
    
    best_cat = max(scores, key=scores.get)
    best_score = scores[best_cat]
    
    # Normalize to 0-1 confidence
    max_possible = sum(SIGNAL_WEIGHTS.values()) if not entry.get('tags') else sum(SIGNAL_WEIGHTS.values()) + 5
    confidence = min(1.0, max(0.0, (best_score + 10) / 30))
    
    # Check if second best is close
    sorted_cats = sorted(scores.items(), key=lambda x: -x[1])
    if len(sorted_cats) > 1:
        second_score = sorted_cats[1][1]
        # Only reduce confidence if entry category is NOT among top candidates
        entry_cat = entry.get("category", "")
        top_cats = [c for c, _ in sorted_cats[:3]]
        if entry_cat not in top_cats and best_score - second_score < 3:
            confidence *= 0.7  # Reduce confidence if categories are close


    return best_cat, confidence, details
# ─── Initialize ───
# Re-export with CATEGORIES for convenience
CATEGORY_RULES = CATEGORY_MUST_HAVE
