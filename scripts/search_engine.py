from scripts.categories import CATEGORIES
#!/usr/bin/env python3
"""
Intelligent Search Engine for Developer Hub.

Features:
- Full-text search across all fields
- Fuzzy matching (typo tolerance)
- Keyword indexing
- Synonym matching
- Ranking by relevance
- Search suggestions
- Recent/popular searches tracking

Usage:
    python scripts/search_engine.py --query "androind sdk"    # Fuzzy search
    python scripts/search_engine.py --query "python" --suggest  # Get suggestions
    python scripts/search_engine.py --build-index              # Build search index
"""

import json
import re
import os
import sys
import time
import math
from pathlib import Path
from collections import defaultdict, Counter
from difflib import SequenceMatcher

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_FILE = REPO_ROOT / ".search_index.json"
HISTORY_FILE = REPO_ROOT / ".search_history.json"

# Synonyms for better matching
SYNONYMS = {
    "js": "javascript", "ts": "typescript",
    "py": "python", "rb": "ruby",
    "reactjs": "react", "vuejs": "vue",
    "node": "nodejs", "deno": "nodejs",
    "ml": "machine-learning", "ai": "artificial-intelligence",
    "db": "database", "orm": "object-relational-mapping",
    "ui": "user-interface", "ux": "user-experience",
    "rest": "rest-api", "restapi": "rest-api",
    "graphql": "graphql-api", "gql": "graphql",
    "docker": "container", "k8s": "kubernetes",
    "aws": "amazon-web-services", "gcp": "google-cloud-platform",
    "npm": "node-package-manager",
    "oop": "object-oriented-programming",
    "spa": "single-page-application",
    "ssr": "server-side-rendering",
    "ssg": "static-site-generator",
}


def normalize(text):
    """Normalize text for indexing."""
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9\s\-]', ' ', text)
    return text


def tokenize(text):
    """Tokenize text into words."""
    return [w for w in normalize(text).split() if len(w) > 1]


def expand_synonyms(tokens):
    """Expand tokens with synonyms."""
    expanded = set(tokens)
    for t in tokens:
        if t in SYNONYMS:
            expanded.add(SYNONYMS[t])
        # Reverse lookup
        for k, v in SYNONYMS.items():
            if v == t:
                expanded.add(k)
    return list(expanded)


def fuzzy_match(query, text, threshold=0.6):
    """Check if query fuzzy-matches text."""
    query = normalize(query)
    text = normalize(text)
    if query in text:
        return True
    # Check word-by-word
    q_words = query.split()
    t_words = text.split()
    for qw in q_words:
        matched = False
        for tw in t_words:
            if SequenceMatcher(None, qw, tw).ratio() >= threshold:
                matched = True
                break
        if not matched:
            return False
    return True


class SearchEngine:
    def __init__(self):
        self.entries = []
        self.by_id = {}
        self.inverted_index = defaultdict(set)  # term -> set of entry IDs
        self.term_frequencies = Counter()
        self.total_entries = 0
        self.recent_searches = []
        self.popular_searches = Counter()
        self._load()
        self._load_history()

    def _load(self):
        """Load all entries from JSON files."""
        self.entries = []
        for entry_dir in REPO_ROOT.iterdir():
            if not entry_dir.is_dir() or entry_dir.name not in CATEGORIES:
                continue
            for json_file in sorted(entry_dir.rglob("*.json")):
                try:
                    with open(json_file) as f:
                        data = json.load(f)
                    self.entries.append(data)
                    self.by_id[data.get("id", "")] = data
                except:
                    continue
        self.total_entries = len(self.entries)

    def _load_history(self):
        """Load search history from file."""
        try:
            if HISTORY_FILE.exists():
                with open(HISTORY_FILE) as f:
                    data = json.load(f)
                    self.recent_searches = data.get("recent", [])
                    self.popular_searches = Counter(data.get("popular", {}))
        except:
            pass

    def _save_history(self):
        """Save search history to file."""
        try:
            with open(HISTORY_FILE, "w") as f:
                json.dump({
                    "recent": self.recent_searches[-50:],
                    "popular": dict(self.popular_searches.most_common(100)),
                }, f)
        except:
            pass

    def build_index(self):
        """Build the inverted search index."""
        self.inverted_index = defaultdict(set)
        self.term_frequencies = Counter()

        for entry in self.entries:
            eid = entry.get("id", "")
            if not eid:
                continue

            # Collect all searchable text
            searchable = " ".join([
                entry.get("name", ""),
                entry.get("description", ""),
                entry.get("category", ""),
                entry.get("license", ""),
                entry.get("author", ""),
                entry.get("organization", ""),
                " ".join(entry.get("tags", [])),
                " ".join(entry.get("programming_languages", [])),
                " ".join(entry.get("platforms", [])),
                entry.get("package_manager", "") or "",
            ])

            tokens = tokenize(searchable)
            tokens = expand_synonyms(tokens)

            for token in set(tokens):
                self.inverted_index[token].add(eid)
                self.term_frequencies[token] += 1

        # Save index
        index_data = {
            "built_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_entries": self.total_entries,
            "total_terms": len(self.inverted_index),
            "terms": {k: list(v) for k, v in self.inverted_index.items()},
            "frequencies": dict(self.term_frequencies),
        }
        with open(INDEX_FILE, "w") as f:
            json.dump(index_data, f)

        print(f"Index built: {self.total_entries} entries, {len(self.inverted_index)} terms")
        return index_data

    def search(self, query, fuzzy=True, max_results=50):
        """Search entries with ranking by relevance."""
        if not query or not query.strip():
            return []

        query = query.strip()
        tokens = tokenize(query)
        tokens = expand_synonyms(tokens)

        if not tokens:
            return []

        # Track search history
        self.recent_searches.insert(0, query)
        self.popular_searches[query.lower()] += 1
        self._save_history()

        # Score each matching entry
        scores = defaultdict(float)
        match_reasons = defaultdict(list)

        for token in tokens:
            matched_ids = set()

            # Exact match in index
            if token in self.inverted_index:
                matched_ids.update(self.inverted_index[token])

            # Fuzzy match against entry text
            if fuzzy:
                for entry in self.entries:
                    eid = entry.get("id", "")
                    if eid in matched_ids:
                        continue
                    searchable = " ".join([
                        entry.get("name", ""),
                        entry.get("description", ""),
                        " ".join(entry.get("tags", [])),
                    ])
                    if fuzzy_match(token, searchable, threshold=0.7):
                        matched_ids.add(eid)

            # Score matched entries
            for eid in matched_ids:
                entry = self.by_id.get(eid)
                if not entry:
                    continue

                score = 0.0
                name = normalize(entry.get("name", ""))
                desc = normalize(entry.get("description", ""))
                tags = [normalize(t) for t in entry.get("tags", [])]
                langs = [normalize(l) for l in entry.get("programming_languages", [])]

                # Name match (highest weight)
                if token in name:
                    score += 10.0
                    match_reasons[eid].append("name")
                elif any(fuzzy_match(token, name, 0.75) for _ in [1]):
                    score += 7.0
                    match_reasons[eid].append("name_fuzzy")

                # Tag match
                if any(token in t for t in tags):
                    score += 8.0
                    match_reasons[eid].append("tag")
                elif any(fuzzy_match(token, t, 0.75) for t in tags):
                    score += 5.0
                    match_reasons[eid].append("tag_fuzzy")

                # Language match
                if any(token in l for l in langs):
                    score += 6.0
                    match_reasons[eid].append("language")

                # Description match
                if token in desc:
                    score += 3.0
                    match_reasons[eid].append("description")
                elif fuzzy_match(token, desc, 0.65):
                    score += 1.5
                    match_reasons[eid].append("desc_fuzzy")

                # Popularity boost
                score += (entry.get("popularity", 5) - 5) * 0.5

                # Maintained boost
                if entry.get("maintained"):
                    score += 1.0

                scores[eid] += score

        # Sort by score descending
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        # Build results
        results = []
        for eid, score in ranked[:max_results]:
            entry = self.by_id.get(eid)
            if entry:
                result = {
                    "id": entry.get("id"),
                    "name": entry.get("name"),
                    "category": entry.get("category"),
                    "description": entry.get("description", "")[:200],
                    "tags": entry.get("tags", []),
                    "programming_languages": entry.get("programming_languages", []),
                    "popularity": entry.get("popularity"),
                    "maintained": entry.get("maintained"),
                    "license": entry.get("license"),
                    "score": round(score, 1),
                    "match_reasons": list(set(match_reasons.get(eid, []))),
                }
                results.append(result)

        return results

    def suggest(self, prefix, max_suggestions=8):
        """Get search suggestions for a prefix."""
        if not prefix or len(prefix) < 2:
            return []

        prefix = normalize(prefix)

        # Find matching terms in index
        matches = []
        # Match from index terms
        for term in self.inverted_index:
            if term.startswith(prefix):
                matches.append((term, len(self.inverted_index[term])))
            elif fuzzy_match(prefix, term, 0.7) and len(term) >= len(prefix):
                matches.append((term, len(self.inverted_index[term])))
        # Also match from entry names
        for entry in self.entries:
            name = normalize(entry.get('name', ''))
            if name.startswith(prefix) and name not in [m[0] for m in matches]:
                eid = entry.get('id', '')
                matches.append((name, len(self.inverted_index.get(name.lower(), [eid]))))

        # Sort by popularity (number of entries containing the term)
        matches.sort(key=lambda x: x[1], reverse=True)

        suggestions = []
        seen = set()
        for term, count in matches[:max_suggestions]:
            if term not in seen:
                suggestions.append({"term": term, "results": count})
                seen.add(term)

        return suggestions

    def get_popular_searches(self, limit=10):
        """Get most popular searches."""
        return [{"query": q, "count": c}
                for q, c in self.popular_searches.most_common(limit)]

    def get_recent_searches(self, limit=10):
        """Get recent searches."""
        seen = set()
        recent = []
        for q in self.recent_searches:
            if q not in seen:
                recent.append(q)
                seen.add(q)
            if len(recent) >= limit:
                break
        return recent


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Developer Hub Search Engine")
    parser.add_argument("--query", "-q", help="Search query")
    parser.add_argument("--suggest", "-s", help="Get search suggestions")
    parser.add_argument("--build-index", action="store_true", help="Build search index")
    parser.add_argument("--popular", action="store_true", help="Show popular searches")
    parser.add_argument("--recent", action="store_true", help="Show recent searches")
    parser.add_argument("--fuzzy", action="store_true", default=True, help="Enable fuzzy matching")
    parser.add_argument("--max", type=int, default=20, help="Max results")

    args = parser.parse_args()
    engine = SearchEngine()

    if args.build_index:
        engine.build_index()
        return

    if args.popular:
        print("Popular searches:")
        for s in engine.get_popular_searches():
            print(f"  {s['query']} ({s['count']}x)")
        return

    if args.recent:
        print("Recent searches:")
        for q in engine.get_recent_searches():
            print(f"  {q}")
        return

    if args.suggest:
        suggestions = engine.suggest(args.suggest)
        print(f"Suggestions for '{args.suggest}':")
        for s in suggestions:
            print(f"  {s['term']} ({s['results']} results)")
        return

    if args.query:
        results = engine.search(args.query, fuzzy=args.fuzzy, max_results=args.max)
        print(f"Search results for '{args.query}': {len(results)} found\n")
        for i, r in enumerate(results, 1):
            reasons = ", ".join(r.get("match_reasons", []))
            print(f"{i:3d}. {r['name']:25s} [{r['category']:18s}] score={r['score']:5.1f} ({reasons})")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
