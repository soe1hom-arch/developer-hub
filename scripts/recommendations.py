#!/usr/bin/env python3
"""
Recommendation Engine for Developer Hub.

Provides intelligent project recommendations based on:
- Similar projects (tag/category based)
- Better maintained alternatives
- Compatible frameworks
- Popular stacks
- Trending/rising projects

Usage:
    python scripts/recommendations.py --project react      # Get recommendations
    python scripts/recommendations.py --trending           # Trending projects
    python scripts/recommendations.py --stack "android"    # Stack recommendation
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from scripts.categories import CATEGORIES
from collections import defaultdict, Counter


# Predefined popular stacks
STACKS = {
    "android": {
        "name": "Android Development",
        "description": "Modern Android app development stack",
        "projects": ["android-sdk", "jetpack-compose", "android-jetpack", "kotlin",
                     "retrofit", "okhttp", "room-database", "hilt", "coil"],
    },
    "web_frontend": {
        "name": "Modern Web Frontend",
        "description": "React-based frontend development stack",
        "projects": ["react", "nextjs", "typescript", "tailwindcss", "vercel"],
    },
    "python_backend": {
        "name": "Python Backend",
        "description": "Python backend development stack",
        "projects": ["python", "fastapi", "django", "postgresql", "redis"],
    },
    "node_backend": {
        "name": "Node.js Backend",
        "description": "Node.js backend development stack",
        "projects": ["nodejs", "express", "typescript", "mongodb", "redis"],
    },
    "ml_ai": {
        "name": "Machine Learning / AI",
        "description": "Machine learning development stack",
        "projects": ["python", "pytorch", "tensorflow", "hugging-face", "langchain"],
    },
    "devops": {
        "name": "DevOps / Cloud",
        "description": "DevOps and cloud infrastructure stack",
        "projects": ["docker", "kubernetes", "github-actions", "aws", "nginx", "ansible"],
    },
    "mobile_cross": {
        "name": "Cross-Platform Mobile",
        "description": "Cross-platform mobile development stack",
        "projects": ["flutter", "react-native", "dart", "firebase", "typescript"],
    },
}


def load_entries():
    entries = []
    for d in REPO_ROOT.iterdir():
        if not d.is_dir() or d.name not in CATEGORIES:
            continue
        for f in sorted(d.rglob("*.json")):
            try:
                with open(f) as fh:
                    entries.append(json.load(fh))
            except:
                pass
    return entries


def recommend_for_project(project_id, entries, by_id, max_results=8):
    """Get recommendations for a project."""
    target = by_id.get(project_id)
    if not target:
        return []

    target_tags = set(t.lower() for t in target.get("tags", []))
    target_langs = set(l.lower() for l in target.get("programming_languages", []))
    target_cat = target.get("category", "").lower()
    target_platforms = set(p.lower() for p in target.get("platforms", []))

    candidates = []

    for entry in entries:
        eid = entry.get("id", "")
        if eid == project_id:
            continue

        score = 0
        reasons = []

        # Category match
        if entry.get("category", "").lower() == target_cat:
            score += 3
            reasons.append("same_category")

        # Tag overlap
        e_tags = set(t.lower() for t in entry.get("tags", []))
        shared_tags = target_tags & e_tags
        score += len(shared_tags) * 2
        if shared_tags:
            reasons.append(f"{len(shared_tags)}_shared_tags")

        # Language overlap
        e_langs = set(l.lower() for l in entry.get("programming_languages", []))
        shared_langs = target_langs & e_langs
        score += len(shared_langs) * 1.5
        if shared_langs:
            reasons.append("shared_language")

        # Platform compatibility
        e_platforms = set(p.lower() for p in entry.get("platforms", []))
        shared_platforms = target_platforms & e_platforms
        score += len(shared_platforms)
        if shared_platforms:
            reasons.append("compatible_platform")

        # Better maintained alternative
        if not target.get("maintained") and entry.get("maintained"):
            score += 5
            reasons.append("better_maintained")

        # Higher popularity
        if entry.get("popularity", 0) > target.get("popularity", 0):
            diff = entry.get("popularity", 0) - target.get("popularity", 0)
            score += diff * 0.5
            reasons.append("more_popular")

        if score > 0:
            candidates.append((score, reasons, entry))

    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[:max_results]


def get_trending(entries, by_id, max_results=10):
    """Get trending projects based on various factors."""
    scored = []
    for entry in entries:
        score = 0

        # Popularity
        score += (entry.get("popularity", 5) - 5) * 3

        # Maintained
        if entry.get("maintained"):
            score += 2

        # Open source
        if entry.get("open_source"):
            score += 1

        # Not archived
        if not entry.get("archived"):
            score += 1

        # Has good documentation
        if entry.get("official_website") and entry.get("documentation"):
            score += 1

        # Has alternatives listed (shows ecosystem awareness)
        if entry.get("alternatives"):
            score += 0.5

        # Package manager available
        if entry.get("package_manager"):
            score += 0.5

        # Multiple programming languages (broader appeal)
        num_langs = len(entry.get("programming_languages", []))
        score += min(num_langs * 0.5, 2)

        scored.append((score, entry))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:max_results]


def get_recently_updated(entries, max_results=10):
    """Get recently updated projects."""
    from datetime import datetime
    scored = []
    for entry in entries:
        last_updated = entry.get("last_updated", "2000-01-01")
        try:
            d = datetime.strptime(last_updated, "%Y-%m-%d")
            scored.append((d, entry))
        except:
            pass
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:max_results]


def recommend_stack(stack_name, by_id):
    """Get projects for a named stack."""
    stack = STACKS.get(stack_name)
    if not stack:
        return None

    projects = []
    for pid in stack["projects"]:
        entry = by_id.get(pid)
        if entry:
            projects.append(entry)
    return {
        "name": stack["name"],
        "description": stack["description"],
        "projects": projects,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Recommendation Engine")
    parser.add_argument("--project", "-p", help="Get recommendations for a project")
    parser.add_argument("--trending", action="store_true", help="Show trending projects")
    parser.add_argument("--recent", action="store_true", help="Show recently updated")
    parser.add_argument("--stack", "-s", help="Recommend a stack (android, web_frontend, etc.)")
    parser.add_argument("--list-stacks", action="store_true", help="List available stacks")

    args = parser.parse_args()
    entries = load_entries()
    by_id = {e.get("id", ""): e for e in entries}

    if args.list_stacks:
        print("Available stacks:")
        for key, stack in STACKS.items():
            print(f"  {key:20s} - {stack['name']} ({len(stack['projects'])} projects)")
        return

    if args.stack:
        result = recommend_stack(args.stack, by_id)
        if not result:
            print(f"Stack '{args.stack}' not found. Use --list-stacks to see available stacks.")
            return
        print(f"📦 Stack: {result['name']}")
        print(f"   {result['description']}\n")
        for p in result["projects"]:
            pop = "★" * (p.get("popularity", 5) // 2)
            print(f"  {pop} {p.get('name', '?'):25s} [{p.get('category','?'):18s}] v{p.get('latest_version','?')}")
        return

    if args.trending:
        trending = get_trending(entries, by_id)
        print("🔥 Trending Projects:\n")
        for i, (score, entry) in enumerate(trending, 1):
            pop = "★" * (entry.get("popularity", 5) // 2)
            print(f"  {i:2d}. {pop} {entry.get('name', '?'):25s} "
                  f"[{entry.get('category','?'):18s}] trend_score={score:.1f}")
        return

    if args.recent:
        recent = get_recently_updated(entries)
        print("🔄 Recently Updated:\n")
        for i, (d, entry) in enumerate(recent, 1):
            print(f"  {i:2d}. {entry.get('name', '?'):25s} [{entry.get('category','?'):18s}] {d.date()}")
        return

    if args.project:
        recs = recommend_for_project(args.project, entries, by_id)
        target = by_id.get(args.project, {})
        print(f"Recommendations for '{target.get('name', args.project)}':\n")
        for score, reasons, entry in recs:
            pop = "★" * (entry.get("popularity", 5) // 2)
            reason_str = ", ".join(reasons[:2])
            print(f"  {pop} {entry.get('name', '?'):25s} [{entry.get('category','?'):18s}] "
                  f"score={score:.1f} ({reason_str})")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
