#!/usr/bin/env python3
"""
Developer Hub AI Assistant.

Uses the project database to recommend technologies based on user needs.

Example:
    python scripts/ai_assistant.py "I want to build an Android social media app"
    python scripts/ai_assistant.py "Build a REST API with Python"
    python scripts/ai_assistant.py --interactive
"""

import json
import sys
import re
from pathlib import Path
from collections import defaultdict

from scripts.categories import CATEGORIES

REPO_ROOT = Path(__file__).resolve().parent.parent

def load_database():
    """Load all project entries into memory."""
    entries = []
    for entry in REPO_ROOT.iterdir():
        if not entry.is_dir() or entry.name not in CATEGORIES:
            continue
        for json_file in sorted(entry.rglob("*.json")):
            try:
                with open(json_file) as f:
                    data = json.load(f)
                entries.append(data)
            except:
                pass
    return entries


def build_index(entries):
    """Build searchable index from entries."""
    index = defaultdict(set)
    for entry in entries:
        name = entry.get("name", "").lower()
        desc = entry.get("description", "").lower()
        tags = [t.lower() for t in entry.get("tags", [])]
        langs = [l.lower() for l in entry.get("programming_languages", [])]
        cat = entry.get("category", "").lower()
        platforms = [p.lower() for p in entry.get("platforms", [])]

        keywords = set(tags + langs + [name] + [cat] + platforms)
        for word in re.findall(r'\w+', name + " " + desc):
            keywords.add(word)

        for kw in keywords:
            if len(kw) > 2:
                index[kw].add(entry.get('id', ''))

    return index


# Recommendation templates by project type
STACK_TEMPLATES = {
    "android": {
        "language": "Kotlin or Java",
        "framework": "Jetpack Compose + Android Jetpack",
        "database": "Room Database (local), Supabase (cloud)",
        "authentication": "Firebase Authentication",
        "networking": "Retrofit + OkHttp",
        "image_loading": "Coil (Kotlin) or Glide (Java)",
        "dependency_injection": "Hilt",
        "architecture": "MVVM with Repository pattern",
        "api": "REST API or GraphQL",
        "deployment": "Google Play Store",
    },
    "web_app": {
        "language": "TypeScript / JavaScript",
        "frontend": "React, Next.js, or Vue",
        "backend": "Node.js + Express or FastAPI",
        "database": "PostgreSQL or MongoDB",
        "hosting": "Vercel, Netlify, or Cloudflare Pages",
        "styling": "Tailwind CSS",
        "authentication": "NextAuth.js or Firebase Auth",
    },
    "api_server": {
        "language": "Python, TypeScript, or Go",
        "framework": "FastAPI (Python), Express (Node.js), or Spring Boot (Java)",
        "database": "PostgreSQL + Redis for caching",
        "api_style": "REST or GraphQL",
        "testing": "Pytest, Jest, or Postman",
        "deployment": "Docker + Kubernetes or serverless (AWS Lambda)",
        "monitoring": "Prometheus + Grafana",
    },
    "machine_learning": {
        "language": "Python",
        "framework": "PyTorch or TensorFlow",
        "mlops": "MLflow or Kubeflow",
        "model_hosting": "Hugging Face, Ollama (local)",
        "api_layer": "FastAPI or Flask",
        "data_processing": "Pandas, NumPy, Apache Spark",
    },
}


def analyze_request(query, entries, index):
    """Analyze a natural language request and recommend technologies."""
    query_lower = query.lower()

    # Detect project type
    detected_types = []
    type_keywords = {
        "android": ["android", "mobile app", "play store", "kotlin"],
        "web_app": ["web", "website", "web app", "frontend", "spa", "dashboard"],
        "api_server": ["api", "rest", "backend", "server", "microservice", "graphql"],
        "machine_learning": ["machine learning", "ai", "ml", "deep learning", "model", "llm"],
        "game": ["game", "gaming", "unity", "unreal"],
        "desktop": ["desktop", "gui", "electron"],
        "cli": ["cli", "command line", "terminal"],
    }

    for dtype, keywords in type_keywords.items():
        if any(kw in query_lower for kw in keywords):
            detected_types.append(dtype)

    if not detected_types:
        detected_types.append("web_app")

    # Extract relevant keywords
    words = set(re.findall(r'\w+', query_lower))
    relevant_ids = set()
    for word in words:
        if word in index:
            relevant_ids.update(index[word])

    relevant_entries = [e for e in entries if e.get('id','') in relevant_ids]

    # Score relevance
    scored = []
    for entry in relevant_entries:
        score = 0
        for dtype in detected_types:
            if entry.get("category") == dtype:
                score += 3
        name = entry.get("name", "").lower()
        desc = entry.get("description", "").lower()
        for word in words:
            if word in name:
                score += 2
            if word in desc:
                score += 1
        if score > 0:
            scored.append((score, entry))

    scored.sort(key=lambda x: x[0], reverse=True)
    top_recommendations = [e for _, e in scored[:8]]

    return {
        "query": query,
        "detected_type": detected_types[0],
        "stack": STACK_TEMPLATES.get(detected_types[0], STACK_TEMPLATES["web_app"]),
        "recommended_projects": top_recommendations,
    }


def print_response(response):
    """Print a formatted AI recommendation response."""
    print("=" * 60)
    print(f"  🔍 Developer Hub AI Assistant")
    print("=" * 60)
    print(f"\n📋 Request: \"{response['query']}\"")
    print(f"🏷️  Type: {response['detected_type'].replace('_', ' ').title()}")
    print()

    print("📌 Recommended Stack:")
    print("-" * 60)
    for key, value in response["stack"].items():
        label = key.replace("_", " ").title()
        print(f"  {label:20s} : {value}")
    print()

    if response["recommended_projects"]:
        print("📦 Related Projects from Developer Hub:")
        print("-" * 60)
        for entry in response["recommended_projects"]:
            pop_stars = "★" * (entry.get("popularity", 5) // 2)
            print(f"  {entry.get('name', '?'):25s} "
                  f"[{entry.get('category', '?'):20s}] "
                  f"{pop_stars} "
                  f"{entry.get('latest_version', '')[:10]}")
    print()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Developer Hub AI Assistant")
    parser.add_argument("query", nargs="*", help="Your development question")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")

    args = parser.parse_args()

    print("Loading Developer Hub database...", end=" ", flush=True)
    entries = load_database()
    index = build_index(entries)
    print(f"{len(entries)} projects loaded.")

    if args.interactive:
        print("\nAsk me about your next project! (type 'quit' to exit)\n")
        while True:
            try:
                query = input("You: ").strip()
                if query.lower() in ("quit", "exit", "q"):
                    break
                if not query:
                    continue
                response = analyze_request(query, entries, index)
                print_response(response)
            except (KeyboardInterrupt, EOFError):
                break
        print("\nHappy coding! 🚀")
    elif args.query:
        query = " ".join(args.query)
        response = analyze_request(query, entries, index)
        print_response(response)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
