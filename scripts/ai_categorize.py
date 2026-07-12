#!/usr/bin/env python3
"""
AI-powered automation for categorizing and enriching project entries.

This module provides utilities for:
- Categorizing new projects
- Generating concise descriptions
- Suggesting relevant tags
- Recommending alternatives
- Detecting deprecated/abandoned projects
- Checking documentation quality

AI never overwrites existing verified data without validation.
"""

import json
import os
import sys
import time
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Common tag mappings for known projects
KNOWN_TAGS = {
    "react": ["ui", "components", "virtual-dom", "jsx", "declarative"],
    "vue": ["ui", "components", "reactive", "frontend"],
    "angular": ["ui", "components", "typescript", "mvc"],
    "django": ["framework", "web", "python", "orm", "batteries-included"],
    "flask": ["framework", "web", "python", "microframework", "wsgi"],
    "express": ["framework", "web", "nodejs", "http", "middleware"],
    "spring": ["framework", "java", "enterprise", "ioc", "mvc"],
    "tensorflow": ["machine-learning", "deep-learning", "neural-networks", "python"],
    "pytorch": ["machine-learning", "deep-learning", "neural-networks", "python"],
    "kubernetes": ["orchestration", "containers", "devops", "cloud-native"],
    "docker": ["containers", "virtualization", "devops", "images"],
    "postgresql": ["database", "relational", "sql", "acid"],
    "redis": ["database", "cache", "key-value", "in-memory"],
    "mongodb": ["database", "nosql", "document", "json"],
}


def categorize_by_keywords(name, description, tags):
    """Suggest categories based on project name, description, and existing tags."""
    text = f"{name} {description} {' '.join(tags)}".lower()

    category_keywords = {
        "ai": ["artificial intelligence", "machine learning", "deep learning", "nlp", "llm", "gpt"],
        "android": ["android", "kotlin", "android studio", "google play"],
        "backend": ["backend", "server", "api", "rest", "graphql", "microservice"],
        "frontend": ["frontend", "ui", "component", "react", "vue", "angular", "css"],
        "database": ["database", "sql", "nosql", "orm", "cache", "redis", "postgres"],
        "cloud": ["cloud", "aws", "azure", "gcp", "serverless"],
        "security": ["security", "auth", "oauth", "encryption", "vulnerability"],
        "devops": ["devops", "ci/cd", "deployment", "monitoring", "infrastructure"],
        "mobile": ["mobile", "ios", "swift", "kotlin", "react native", "flutter"],
        "web": ["web", "http", "browser", "html", "css", "javascript"],
        "machine-learning": ["machine learning", "ml", "model", "training", "inference"],
        "game-development": ["game", "unity", "unreal", "godot", "gaming"],
        "blockchain": ["blockchain", "ethereum", "web3", "solidity", "crypto"],
        "iot": ["iot", "internet of things", "mqtt", "sensor", "embedded"],
        "api": ["api", "rest", "graphql", "grpc", "openapi"],
    }

    scores = {}
    for category, keywords in category_keywords.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            scores[category] = score

    if scores:
        return max(scores, key=scores.get)
    return None


def suggest_tags(name, description):
    """Suggest tags based on project name and description."""
    text = f"{name} {description}".lower()
    suggested = set()

    tag_keywords = {
        "python": ["python", "django", "flask", "pytorch"],
        "javascript": ["javascript", "js", "node", "npm"],
        "typescript": ["typescript", "ts"],
        "java": ["java", "spring", "maven", "jvm"],
        "rust": ["rust", "cargo", "systems"],
        "go": ["golang", "go "],
        "web": ["web", "http", "api", "rest"],
        "database": ["database", "sql", "nosql", "orm"],
        "framework": ["framework", "library"],
        "open-source": ["open source", "oss", "mit license"],
        "cli": ["cli", "command-line", "terminal"],
        "testing": ["testing", "test", "qa", "unit test"],
    }

    for tag, keywords in tag_keywords.items():
        if any(kw in text for kw in keywords):
            suggested.add(tag)

    return list(suggested)


def detect_deprecated(data):
    """Heuristic detection of potentially deprecated/abandoned projects."""
    flags = []
    if data.get("archived"):
        flags.append("archived")
    if data.get("latest_version") == "0.0.0" or not data.get("latest_version"):
        flags.append("no-version")
    if not data.get("maintained"):
        flags.append("unmaintained")
    if data.get("popularity", 5) <= 2:
        flags.append("low-popularity")
    return flags


def check_documentation_quality(data):
    """Basic documentation quality check based on available fields."""
    score = 0
    checks = []

    if data.get("official_website"):
        score += 2
        checks.append("website")
    if data.get("documentation"):
        score += 2
        checks.append("docs-link")
    if data.get("github_repository"):
        score += 1
        checks.append("github")
    if data.get("installation_examples"):
        score += 2
        checks.append("installation")
    if data.get("examples"):
        score += 2
        checks.append("examples")
    if data.get("tutorials"):
        score += 1
        checks.append("tutorials")

    return {
        "score": score,
        "max_score": 10,
        "quality": "high" if score >= 8 else "medium" if score >= 5 else "low",
        "checks": checks,
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="AI-powered project categorization")
    parser.add_argument("--input", help="Directory with new project JSON files to process")
    parser.add_argument("--check-docs", action="store_true", help="Check documentation quality for all entries")
    parser.add_argument("--detect-deprecated", action="store_true", help="Detect potentially deprecated entries")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without writing")

    args = parser.parse_args()

    if args.input:
        input_dir = Path(args.input)
        if not input_dir.is_dir():
            print(f"Error: {args.input} is not a directory")
            sys.exit(1)

        for json_file in input_dir.glob("*.json"):
            with open(json_file, "r") as f:
                data = json.load(f)

            print(f"\nProcessing: {data.get('name', json_file.name)}")
            category = categorize_by_keywords(
                data.get("name", ""),
                data.get("description", ""),
                data.get("tags", [])
            )
            if category:
                print(f"  Suggested category: {category}")
            tags = suggest_tags(data.get("name", ""), data.get("description", ""))
            if tags:
                print(f"  Suggested tags: {', '.join(tags)}")
            doc_quality = check_documentation_quality(data)
            print(f"  Documentation quality: {doc_quality['quality']} ({doc_quality['score']}/{doc_quality['max_score']})")

    if args.check_docs:
        for category_dir in REPO_ROOT.iterdir():
            if not category_dir.is_dir() or category_dir.name.startswith("."):
                continue
            for json_file in category_dir.rglob("*.json"):
                with open(json_file, "r") as f:
                    data = json.load(f)
                quality = check_documentation_quality(data)
                if quality["quality"] == "low":
                    print(f"  Low docs quality: {data.get('name', json_file.name)} ({quality['score']}/10)")

    if args.detect_deprecated:
        for category_dir in REPO_ROOT.iterdir():
            if not category_dir.is_dir() or category_dir.name.startswith("."):
                continue
            for json_file in category_dir.rglob("*.json"):
                with open(json_file, "r") as f:
                    data = json.load(f)
                flags = detect_deprecated(data)
                if flags:
                    print(f"  Flags for {data.get('name', json_file.name)}: {', '.join(flags)}")


if __name__ == "__main__":
    main()
