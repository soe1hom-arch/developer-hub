#!/usr/bin/env python3
"""
Relationship Graph for Developer Hub.

Builds and analyzes relationships between projects:
- Alternatives (explicitly listed)
- Commonly used together (based on tags, categories)
- Similar projects (based on shared characteristics)
- Dependencies (where known)

Usage:
    python scripts/relationships.py --graph          # Build full relationship graph
    python scripts/relationships.py --project react  # Show relationships for a project
    python scripts/relationships.py --similar react  # Find similar projects
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from scripts.categories import CATEGORIES
from collections import defaultdict, Counter


# Known "commonly used together" relationships
COMMON_STACKS = {
    "react": ["nextjs", "tailwindcss", "typescript", "nodejs", "express"],
    "nextjs": ["react", "tailwindcss", "vercel", "typescript"],
    "vue": ["vite", "tailwindcss", "typescript"],
    "angular": ["typescript", "rxjs", "nodejs"],
    "django": ["python", "postgresql", "redis"],
    "fastapi": ["python", "postgresql", "redis"],
    "express": ["nodejs", "mongodb", "redis"],
    "spring-boot": ["java", "postgresql", "redis"],
    "flutter": ["dart", "firebase"],
    "react-native": ["react", "typescript", "firebase"],
    "docker": ["kubernetes", "github-actions", "nginx"],
    "kubernetes": ["docker", "prometheus"],
    "postgresql": ["redis", "django", "fastapi"],
    "mongodb": ["express", "nodejs", "react"],
    "redis": ["postgresql", "django", "fastapi"],
    "pytorch": ["python", "hugging-face", "tensorflow"],
    "tensorflow": ["python", "pytorch", "keras"],
    "retrofit": ["okhttp", "room-database", "hilt", "kotlin"],
    "okhttp": ["retrofit", "kotlin"],
    "hilt": ["room-database", "retrofit", "jetpack-compose"],
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


def build_graph(entries):
    """Build a relationship graph from entries."""
    by_id = {e.get("id", ""): e for e in entries}
    by_name = {}
    for e in entries:
        by_name[e.get("name", "").lower()] = e.get("id", "")
        for tag in e.get("tags", []):
            by_name[tag.lower()] = e.get("id", "")

    # Tag-based similarity
    tag_entries = defaultdict(set)
    for e in entries:
        eid = e.get("id", "")
        for tag in e.get("tags", []):
            tag_entries[tag.lower()].add(eid)
        for lang in e.get("programming_languages", []):
            tag_entries[lang.lower()].add(eid)

    # Category-based grouping
    cat_entries = defaultdict(list)
    for e in entries:
        cat_entries[e.get("category", "")].append(e.get("id", ""))

    graph = {}
    for e in entries:
        eid = e.get("id", "")
        if not eid:
            continue

        relationships = {
            "alternatives": [],
            "commonly_used_with": [],
            "similar": [],
            "same_category": [],
        }

        # 1. Explicit alternatives
        for alt_name in e.get("alternatives", []):
            alt_lower = alt_name.lower()
            # Find by name
            found_id = by_name.get(alt_lower)
            if found_id and found_id != eid:
                relationships["alternatives"].append({
                    "id": found_id,
                    "name": alt_name,
                    "relationship": "alternative",
                })

        # 2. Commonly used together (from predefined stacks)
        if eid in COMMON_STACKS:
            for related_id in COMMON_STACKS[eid]:
                if related_id in by_id and related_id != eid:
                    relationships["commonly_used_with"].append({
                        "id": related_id,
                        "name": by_id[related_id].get("name", ""),
                        "relationship": "common_stack",
                    })

        # 3. Similar projects (shared tags)
        e_tags = set(t.lower() for t in e.get("tags", []))
        e_langs = set(l.lower() for l in e.get("programming_languages", []))
        e_all = e_tags | e_langs

        tag_scores = Counter()
        for tag in e_all:
            for other_id in tag_entries.get(tag, set()):
                if other_id != eid:
                    tag_scores[other_id] += 1

        for other_id, score in tag_scores.most_common(5):
            if score >= 2:  # At least 2 shared tags
                other = by_id.get(other_id)
                if other:
                    relationships["similar"].append({
                        "id": other_id,
                        "name": other.get("name", ""),
                        "similarity_score": score,
                        "relationship": "similar",
                    })

        # 4. Same category
        cat = e.get("category", "")
        for other_id in cat_entries.get(cat, []):
            if other_id != eid and len(relationships["same_category"]) < 10:
                other = by_id.get(other_id)
                if other:
                    relationships["same_category"].append({
                        "id": other_id,
                        "name": other.get("name", ""),
                        "relationship": "same_category",
                    })

        graph[eid] = relationships

    return graph


def find_similar(entries, target_id, by_id):
    """Find similar projects using tag-based similarity."""
    target = by_id.get(target_id)
    if not target:
        return []

    target_tags = set(t.lower() for t in target.get("tags", []))
    target_langs = set(l.lower() for l in target.get("programming_languages", []))
    target_all = target_tags | target_langs | {target.get("category", "").lower()}

    scores = []
    for entry in entries:
        eid = entry.get("id", "")
        if eid == target_id:
            continue

        e_tags = set(t.lower() for t in entry.get("tags", []))
        e_langs = set(l.lower() for l in entry.get("programming_languages", []))
        e_all = e_tags | e_langs | {entry.get("category", "").lower()}

        intersection = target_all & e_all
        union = target_all | e_all
        if union:
            jaccard = len(intersection) / len(union)
            scores.append((jaccard, entry))

    scores.sort(key=lambda x: x[0], reverse=True)
    return scores[:8]


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Relationship Graph")
    parser.add_argument("--graph", action="store_true", help="Build full relationship graph")
    parser.add_argument("--project", "-p", help="Show relationships for a project")
    parser.add_argument("--similar", "-s", help="Find similar projects")
    parser.add_argument("--json", action="store_true", help="Output JSON")

    args = parser.parse_args()

    entries = load_entries()
    by_id = {e.get("id", ""): e for e in entries}

    if args.graph:
        graph = build_graph(entries)
        print(f"Relationship graph built: {len(graph)} nodes")
        # Summary stats
        total_rels = sum(len(v["alternatives"]) + len(v["commonly_used_with"])
                        + len(v["similar"]) + len(v["same_category"])
                        for v in graph.values())
        print(f"Total relationships: {total_rels}")
        return

    if args.similar:
        similar = find_similar(entries, args.similar, by_id)
        target = by_id.get(args.similar, {})
        print(f"Projects similar to '{target.get('name', args.similar)}':")
        for score, entry in similar:
            print(f"  {entry.get('name', '?'):25s} [{entry.get('category','?'):18s}] similarity={score:.2f}")
        return

    if args.project:
        graph = build_graph(entries)
        rels = graph.get(args.project, {})
        project = by_id.get(args.project, {})
        print(f"Relationships for '{project.get('name', args.project)}':\n")

        if rels.get("alternatives"):
            print("  🔄 Alternatives:")
            for r in rels["alternatives"]:
                print(f"     - {r['name']}")

        if rels.get("commonly_used_with"):
            print("\n  🔗 Commonly used with:")
            for r in rels["commonly_used_with"]:
                print(f"     - {r['name']}")

        if rels.get("similar"):
            print("\n  📊 Similar projects:")
            for r in rels["similar"][:5]:
                print(f"     - {r['name']} (score: {r['similarity_score']})")

        if rels.get("same_category"):
            print(f"\n  📂 Same category ({project.get('category', '?')}):")
            for r in rels["same_category"][:5]:
                print(f"     - {r['name']}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
