#!/usr/bin/env python3
"""
Category Mismatch Detection — scan semua entries dan laporin yang mencurigakan.

Mendeteksi:
- Entry di kategori A tapi deskripsi/name/tags lebih cocok ke kategori B
- Category field tidak cocok dengan folder parent
- Tags yang bertentangan dengan kategori

Usage:
    python scripts/detect_mismatch.py                          # Semua entri
    python scripts/detect_mismatch.py --category ai            # Kategori tertentu
    python scripts/detect_mismatch.py --threshold 0.3          # Sesuaikan sensitivitas
    python scripts/detect_mismatch.py --report                # Generate report file
"""

import json, os, sys, re
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from scripts.categories import CATEGORIES, CATEGORY_LABELS

# ──────────────────── Category Keywords ────────────────────
# Keywords that STRONGLY suggest a category
CATEGORY_KEYWORDS = {
    "ai": [
        "artificial intelligence", "machine learning", "deep learning", "neural network",
        "nlp", "llm", "gpt", "transformer", "computer vision", "natural language",
        "chatbot", "generative ai", "ai model", "ai framework", "tensorflow", "pytorch",
        "openai", "language model", "diffusion", "ai agent", "ml pipeline", "mlops",
        "rag", "embedding", "vector database", "ai", "ml model", "inference",
        "machine-learning", "deep-learning", "ai-framework", "ai-tool",
    ],
    "android": [
        "android", "kotlin", "android sdk", "google play", "android studio",
        "material design", "jetpack", "android app", "dalm", "apk", "aab",
        "androidx", "gradle", "android development", "mobile android",
        "android-application", "android-library",
    ],
    "api": [
        "api", "rest api", "graphql", "grpc", "openapi", "swagger",
        "api gateway", "api client", "api wrapper", "api sdk",
        "restful", "api-development",
    ],
    "backend": [
        "backend", "server-side", "web server", "api server", "microservice",
        "serverless function", "middleware", "express", "django", "flask",
        "fastapi", "spring boot", "laravel", "nodejs server", "gin",
        "backend framework", "server", "server-side", "backend development",
    ],
    "binary": [
        "binary", "executable", "compiler", "assembler", "linker",
        "object file", "elf", "pe", "mach-o", "binary analysis",
        "reverse engineering", "binary exploitation",
    ],
    "blockchain": [
        "blockchain", "ethereum", "web3", "solidity", "cryptocurrency",
        "smart contract", "defi", "nft", "bitcoin", "consensus",
        "distributed ledger", "dapp", "wallet", "token", "crypto",
        "blockchain-development",
    ],
    "cli-tools": [
        "cli", "command line", "terminal", "shell", "command-line",
        "tui", "terminal ui", "console", "command line tool",
        "cli-tool", "cli-utility",
    ],
    "cloud": [
        "cloud", "aws", "azure", "gcp", "google cloud", "amazon web services",
        "cloud computing", "cloud storage", "cloud function", "cloud native",
        "serverless", "iaas", "paas", "saas", "cloud infrastructure",
        "cloud-service", "cloud-platform",
    ],
    "containers": [
        "container", "docker", "kubernetes", "k8s", "podman",
        "container orchestration", "container runtime", "docker image",
        "containerization", "microservice", "service mesh", "istio",
        "containerd", "cri-o", "container-registry",
    ],
    "database": [
        "database", "sql", "nosql", "postgresql", "mysql", "mongodb",
        "redis", "sqlite", "cassandra", "elasticsearch", "clickhouse",
        "data store", "orm", "query", "indexing", "data warehouse",
        "data lake", "database management", "rdbms", "data-pipeline",
        "database-driver", "database-tool",
    ],
    "desktop": [
        "desktop", "electron", "qt", "gtk", "wxwidgets", "winforms",
        "wpf", "javafx", "swing", "native app", "desktop application",
        "cross-platform desktop", "desktop-app",
    ],
    "devops": [
        "devops", "ci/cd", "continuous integration", "continuous deployment",
        "jenkins", "github actions", "gitlab ci", "ansible", "terraform",
        "pulumi", "infrastructure as code", "iac", "monitoring", "observability",
        "prometheus", "grafana", "deployment", "automation", "site reliability",
        "sre", "incident management", "devops-tool",
    ],
    "embedded": [
        "embedded", "microcontroller", "arm", "risc-v", "rtos",
        "bare metal", "driver", "firmware", "stm32", "avr",
        "embedded system", "embedded development",
    ],
    "firmware": [
        "firmware", "bios", "uefi", "bootloader", "microcode",
        "device firmware", "embedded firmware", "firmware update",
    ],
    "frameworks": [
        "framework", "web framework", "application framework",
        "mvc framework", "dependency injection", "ioc container",
        "full-stack framework", "web-framework",
    ],
    "frontend": [
        "frontend", "ui", "user interface", "react", "vue", "angular",
        "svelte", "css", "html", "javascript framework", "component library",
        "design system", "responsive", "spa", "single page application",
        "frontend framework", "ui-library", "web-component",
    ],
    "game-development": [
        "game", "game engine", "unity", "unreal engine", "godot",
        "game development", "gamedev", "2d game", "3d game",
        "game framework", "game-development", "gaming",
    ],
    "iot": [
        "iot", "internet of things", "mqtt", "sensor", "smart home",
        "arduino", "esp32", "esp8266", "raspberry pi", "home automation",
        "iot platform", "iot-framework",
    ],
    "languages": [
        "programming language", "compiler", "interpreter", "type system",
        "language server", "lsp", "language-runtime", "language-core",
        "programming-language",
    ],
    "libraries": [
        "library", "sdk", "client library", "api wrapper",
        "utility library", "helper library", "software library",
    ],
    "linux": [
        "linux", "linux kernel", "linux distribution", "gnu/linux",
        "linux desktop", "linux system", "unix", "posix",
        "linux-utility", "linux-tool",
    ],
    "machine-learning": [
        "machine learning", "ml", "deep learning", "classification",
        "regression", "model training", "model deployment", "feature engineering",
        "data science", "predictive model", "ml-pipeline",
    ],
    "macos": [
        "macos", "mac os", "os x", "apple", "cocoa", "swiftui",
        "mac application", "macos-app",
    ],
    "mobile": [
        "mobile", "ios", "swift", "flutter", "react native",
        "cross-platform mobile", "mobile app", "iphone", "ipad",
        "mobile-development", "mobile-framework",
    ],
    "network": [
        "network", "networking", "tcp/ip", "http", "dns", "proxy",
        "load balancer", "vpn", "firewall", "protocol",
        "network tool", "network protocol",
    ],
    "operating-systems": [
        "operating system", "os", "kernel", "system programming",
        "os development", "system call", "virtual memory",
    ],
    "robotics": [
        "robotics", "robot", "ros", "robot operating system",
        "autonomous", "ros2", "robotics-framework",
    ],
    "security": [
        "security", "authentication", "authorization", "encryption",
        "oauth", "jwt", "ssl", "tls", "cybersecurity", "penetration testing",
        "vulnerability", "cryptography", "secure", "identity",
        "security-tool", "security-framework",
    ],
    "termux": [
        "termux", "termux-app", "termux-api", "termux-package",
        "termux-repo", "termux-tool", "termux-addon",
        "proot", "termux-boot", "termux-widget",
    ],
    "tools": [
        "tool", "utility", "developer tool", "productivity tool",
        "code generator", "scaffolding", "boilerplate",
    ],
    "web": [
        "web", "web browser", "web application", "web platform",
        "web standard", "web component", "web api", "browser extension",
        "web-development", "web-engine",
    ],
    "windows": [
        "windows", "win32", "winforms", "wpf", "uwp", "winui",
        "powerShell", "windows app", ".net", "dotnet",
        "windows-utility", "windows-tool",
    ],
}

# Tags that CONFLICT with certain categories
CATEGORY_CONFLICTS = {
    "languages": ["code-counter", "line-counter", "code-statistics", "code-analysis"],
    "tools": ["language", "programming-language", "compiler", "interpreter"],
    "mobile": ["android", "android-tools", "apk"],
    "android": ["ios", "swift", "flutter", "react-native"],
    "frontend": ["backend", "server", "database", "api-server"],
    "backend": ["css", "html", "ui-library", "frontend"],
    "ai": ["game", "gaming", "desktop"],
    "desktop": ["mobile", "ios", "android"],
    "database": ["game", "gaming", "desktop", "mobile-ui"],
}

# Words that are too generic to be useful
STOP_WORDS = {"a", "an", "the", "for", "and", "or", "with", "from", "this",
              "that", "your", "its", "all", "new", "easy", "simple", "fast",
              "built", "using", "based", "platform", "support", "make", "making",
              "create", "build", "provide", "allows", "open", "source"}


def extract_keywords(text):
    """Extract meaningful keywords from text."""
    text = text.lower()
    # Remove punctuation
    text = re.sub(r'[^\w\s-]', ' ', text)
    words = text.split()
    # Filter stop words and short words
    keywords = [w for w in words if w not in STOP_WORDS and len(w) > 2]
    # Also extract multi-word phrases (2-3 words)
    phrases = []
    for i in range(len(words) - 1):
        pair = f"{words[i]} {words[i+1]}"
        if pair not in STOP_WORDS:
            phrases.append(pair)
    for i in range(len(words) - 2):
        triple = f"{words[i]} {words[i+1]} {words[i+2]}"
        if triple not in STOP_WORDS:
            phrases.append(triple)
    return keywords + phrases


def calculate_category_score(entry_text, category_keywords):
    """
    Calculate how well entry text matches a category.
    Returns a score between 0.0 and 1.0.
    """
    matches = 0
    for kw in category_keywords:
        if kw.lower() in entry_text:
            matches += 1
    if not category_keywords:
        return 0.0
    # Normalize: log scale to prevent spammy matches
    score = min(1.0, matches / max(1, len(category_keywords) * 0.3))
    return score


def detect_mismatches(threshold=0.15, target_category=None):
    """Detect potential category mismatches across all entries."""
    mismatches = []
    
    for cat in sorted(CATEGORIES):
        if target_category and cat != target_category:
            continue
        
        cat_dir = REPO_ROOT / cat
        if not cat_dir.exists():
            continue
        
        for json_file in sorted(cat_dir.glob("*.json")):
            try:
                with open(json_file) as f:
                    entry = json.load(f)
            except (json.JSONDecodeError, Exception):
                continue
            
            name = entry.get("name", "")
            description = entry.get("description", "")
            tags = entry.get("tags", [])
            entry_cat = entry.get("category", "")
            
            # Combine all text for analysis
            combined_text = f"{name} {description} {' '.join(tags)}".lower()
            
            # Check 1: category field vs parent directory
            if entry_cat != cat:
                mismatches.append({
                    "file": str(json_file.relative_to(REPO_ROOT)),
                    "name": name,
                    "current_cat": cat,
                    "field_cat": entry_cat,
                    "issue": "CATEGORY_FIELD_MISMATCH",
                    "message": f"Field category '{entry_cat}' != folder '{cat}'"
                })
                continue
            
            # Check 2: Calculate score for current category
            current_score = calculate_category_score(
                combined_text, CATEGORY_KEYWORDS.get(cat, [])
            )
            
            # Check 3: Calculate score for all other categories
            best_other_cat = None
            best_other_score = 0
            
            for other_cat, keywords in CATEGORY_KEYWORDS.items():
                if other_cat == cat:
                    continue
                score = calculate_category_score(combined_text, keywords)
                if score > best_other_score:
                    best_other_score = score
                    best_other_cat = other_cat
            
            # Check 4: Check if any conflicts exist
            conflicts = []
            if cat in CATEGORY_CONFLICTS:
                for conflict_tag in CATEGORY_CONFLICTS[cat]:
                    if conflict_tag.lower() in combined_text:
                        conflicts.append(conflict_tag)
            
            # Determine if mismatch
            issues = []
            
            # If current score is very low AND another category scores higher
            if current_score < threshold and best_other_score > current_score:
                issues.append(
                    f"Low match with '{cat}' (score: {current_score:.2f}), "
                    f"better match: '{best_other_cat}' ({best_other_score:.2f})"
                )
            
            # If another category scores significantly higher
            if best_other_score > current_score + 0.3:
                issues.append(
                    f"'{best_other_cat}' scores much higher ({best_other_score:.2f}) "
                    f"than '{cat}' ({current_score:.2f})"
                )
            
            if conflicts:
                issues.append(f"Conflict tags in description: {conflicts}")
            
            if issues:
                mismatches.append({
                    "file": str(json_file.relative_to(REPO_ROOT)),
                    "name": name,
                    "current_cat": cat,
                    "field_cat": entry_cat,
                    "issue": "SUSPECTED_MISMATCH",
                    "current_score": round(current_score, 3),
                    "best_other_cat": best_other_cat,
                    "best_other_score": round(best_other_score, 3),
                    "message": "; ".join(issues)
                })
    
    return mismatches


def generate_report(mismatches, output_file=None):
    """Generate a formatted report."""
    lines = []
    lines.append("=" * 70)
    lines.append("  CATEGORY MISMATCH DETECTION REPORT")
    lines.append("=" * 70)
    lines.append(f"  Generated: {__import__('datetime').datetime.now().isoformat()}")
    lines.append(f"  Total flags: {len(mismatches)}")
    lines.append("")
    
    # Group by issue type
    field_mismatches = [m for m in mismatches if m["issue"] == "CATEGORY_FIELD_MISMATCH"]
    suspected = [m for m in mismatches if m["issue"] == "SUSPECTED_MISMATCH"]
    
    if field_mismatches:
        lines.append(f"\n{'─' * 70}")
        lines.append(f"  🔴 CATEGORY FIELD MISMATCHES ({len(field_mismatches)})")
        lines.append(f"{'─' * 70}")
        for m in field_mismatches:
            lines.append(f"  ⚠ {m['name']}")
            lines.append(f"     File: {m['file']}")
            lines.append(f"     {m['message']}")
    
    if suspected:
        lines.append(f"\n{'─' * 70}")
        lines.append(f"  🟡 SUSPECTED MISMATCHES ({len(suspected)})")
        lines.append(f"{'─' * 70}")
        # Group by current category
        by_cat = {}
        for m in suspected:
            by_cat.setdefault(m["current_cat"], []).append(m)
        
        for cat in sorted(by_cat.keys()):
            lines.append(f"\n  📂 {CATEGORY_LABELS.get(cat, cat)} ({len(by_cat[cat])})")
            for m in by_cat[cat]:
                lines.append(f"     • {m['name']}")
                lines.append(f"       → {m['message']}")
    
    lines.append(f"\n{'─' * 70}")
    lines.append(f"  End of report — {len(mismatches)} issues found")
    lines.append(f"{'─' * 70}")
    
    report = "\n".join(lines)
    
    if output_file:
        report_path = REPO_ROOT / "reports" / output_file
        report_path.parent.mkdir(exist_ok=True)
        with open(report_path, "w") as f:
            f.write(report)
        print(f"Report saved to {report_path}")
    
    return report


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Category Mismatch Detection")
    parser.add_argument("--category", help="Check specific category only")
    parser.add_argument("--threshold", type=float, default=0.15, help="Sensitivity threshold (default: 0.15)")
    parser.add_argument("--report", action="store_true", help="Save report to file")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()
    
    mismatches = detect_mismatches(
        threshold=args.threshold,
        target_category=args.category,
    )
    
    if args.json:
        print(json.dumps(mismatches, indent=2))
    elif args.report:
        report = generate_report(mismatches, f"mismatch-report-{__import__('datetime').datetime.now().strftime('%Y%m%d')}.txt")
        print(report)
    else:
        print(f"\nFound {len(mismatches)} potential mismatches:\n")
        for m in mismatches:
            print(f"  [{m['issue']}] {m['name']} ({m['current_cat']})")
            print(f"         {m['message']}")
            print()
