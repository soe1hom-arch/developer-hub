#!/usr/bin/env python3
"""
AI Knowledge Layer for Developer Hub.

Provides AI-powered content enrichment:
- Generate concise project summaries
- Explain project purpose
- Suggest use cases
- Compare similar technologies
- Generate beginner-friendly descriptions

All AI-generated content is clearly marked and never overwrites verified metadata.
"""

import json
import sys
import re
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path(__file__).resolve().parent.parent

CATEGORIES = {
    "ai", "android", "api", "backend", "frontend", "database", "cloud",
    "security", "languages", "frameworks", "libraries", "tools",
    "operating-systems", "linux", "windows", "macos", "network",
    "devops", "containers", "firmware", "embedded", "iot",
    "game-development", "mobile", "desktop", "web", "blockchain",
    "machine-learning", "robotics"
}

# Knowledge base for generating descriptions and use cases
PROFILE_TEMPLATES = {
    "language": {
        "purpose": "Programming language for building software applications",
        "use_cases": ["Application development", "Scripting and automation", "System programming"],
    },
    "framework": {
        "purpose": "Development framework providing structure and tools for building applications",
        "use_cases": ["Web applications", "API development", "Enterprise software"],
    },
    "library": {
        "purpose": "Reusable collection of code for specific functionality",
        "use_cases": ["Code reuse", "Abstracting complexity", "Adding features without writing from scratch"],
    },
    "database": {
        "purpose": "Data storage and retrieval system",
        "use_cases": ["Data persistence", "Analytics", "Application state management"],
    },
    "tool": {
        "purpose": "Utility for improving developer productivity and workflow",
        "use_cases": ["Build automation", "Version control", "Project management"],
    },
    "cloud": {
        "purpose": "Cloud computing service for hosting, storage, and infrastructure",
        "use_cases": ["Application hosting", "Scalable infrastructure", "Managed services"],
    },
    "ai/ml": {
        "purpose": "Artificial intelligence and machine learning platform",
        "use_cases": ["Model training", "Inference", "Natural language processing", "Computer vision"],
    },
    "mobile": {
        "purpose": "Mobile development framework or tool",
        "use_cases": ["Mobile app development", "Cross-platform development", "Native UI building"],
    },
    "security": {
        "purpose": "Security tool or framework for protecting applications and data",
        "use_cases": ["Authentication", "Encryption", "Vulnerability scanning"],
    },
}


def classify_project_type(entry):
    """Classify a project into a general type."""
    category = entry.get("category", "")
    tags = [t.lower() for t in entry.get("tags", [])]
    name = entry.get("name", "").lower()
    desc = entry.get("description", "").lower()

    if category in ("languages",):
        return "language"
    if category in ("frameworks",):
        return "framework"
    if category in ("libraries",):
        return "library"
    if category in ("database",):
        return "database"
    if category in ("tools",):
        return "tool"
    if category in ("cloud",):
        return "cloud"
    if category in ("ai", "machine-learning"):
        return "ai/ml"
    if category in ("mobile", "android"):
        return "mobile"
    if category in ("security",):
        return "security"
    if "framework" in tags or "framework" in desc:
        return "framework"
    if "library" in tags or "library" in desc:
        return "library"
    if "database" in tags or "database" in desc:
        return "database"
    if "tool" in tags:
        return "tool"
    return "general"


def generate_summary(entry):
    """Generate a concise summary of the project."""
    name = entry.get("name", "")
    desc = entry.get("description", "")
    category = entry.get("category", "")
    tags = entry.get("tags", [])
    langs = entry.get("programming_languages", [])

    # Based on category
    cat_labels = {
        "ai": "AI platform",
        "android": "Android development tool",
        "backend": "backend framework",
        "frontend": "frontend framework",
        "database": "database system",
        "cloud": "cloud service",
        "security": "security tool",
        "languages": "programming language",
        "frameworks": "framework",
        "libraries": "library",
        "tools": "developer tool",
        "devops": "DevOps tool",
        "mobile": "mobile development tool",
        "web": "web technology",
        "api": "API technology",
        "machine-learning": "machine learning tool",
    }
    label = cat_labels.get(category, "developer resource")

    summary = f"{name} is a {label}"

    if langs:
        summary += f" primarily used with {', '.join(langs[:3])}"

    if tags:
        top_tags = [t for t in tags[:3] if t not in langs]
        if top_tags:
            summary += f", focused on {', '.join(top_tags)}"

    summary += "."

    return {
        "type": "generated_summary",
        "content": summary,
        "source": "Developer Hub Knowledge Layer",
        "disclaimer": "AI-generated summary based on available metadata",
    }


def suggest_use_cases(entry):
    """Suggest common use cases for the project."""
    project_type = classify_project_type(entry)
    profile = PROFILE_TEMPLATES.get(project_type, {
        "purpose": "Developer tool or platform",
        "use_cases": ["Software development", "Application building"],
    })

    # Add specific use cases based on tags and description
    desc = entry.get("description", "").lower()
    tags = [t.lower() for t in entry.get("tags", [])]
    additional_use_cases = []

    use_case_keywords = {
        "web": "Web development",
        "api": "API development and integration",
        "mobile": "Mobile application development",
        "data": "Data processing and analysis",
        "testing": "Software testing and quality assurance",
        "devops": "DevOps and infrastructure automation",
        "cloud": "Cloud-native development",
        "security": "Application security",
        "ui": "User interface development",
        "database": "Data management and storage",
        "ml": "Machine learning",
        "ai": "Artificial intelligence",
        "nlp": "Natural language processing",
        "real-time": "Real-time applications",
        "async": "Asynchronous programming",
        "container": "Container management",
        "monitoring": "System monitoring and observability",
    }

    for keyword, use_case in use_case_keywords.items():
        if keyword in desc or keyword in tags:
            additional_use_cases.append(use_case)

    all_use_cases = profile["use_cases"] + additional_use_cases
    # Remove duplicates while preserving order
    seen = set()
    unique_cases = []
    for uc in all_use_cases:
        if uc not in seen:
            seen.add(uc)
            unique_cases.append(uc)

    return {
        "type": "suggested_use_cases",
        "purpose": profile["purpose"],
        "use_cases": unique_cases[:5],
        "source": "Developer Hub Knowledge Layer",
        "disclaimer": "AI-generated suggestions based on project metadata",
    }


def beginner_description(entry):
    """Generate a beginner-friendly description."""
    name = entry.get("name", "")
    desc = entry.get("description", "")
    project_type = classify_project_type(entry)

    intro = {
        "language": f"{name} is a programming language that lets you write instructions for computers.",
        "framework": f"{name} is a framework that provides a foundation for building applications.",
        "library": f"{name} is a library that gives you pre-written code to solve common problems.",
        "database": f"{name} is a system that stores and organizes data so applications can use it.",
        "tool": f"{name} is a tool that helps developers work more efficiently.",
        "cloud": f"{name} provides cloud computing services so you don't have to manage your own servers.",
        "ai/ml": f"{name} provides AI capabilities so applications can understand, learn, and make decisions.",
        "mobile": f"{name} helps you build applications for mobile devices.",
        "security": f"{name} helps keep applications and data safe from unauthorized access.",
        "general": f"{name} is a {entry.get('category', 'developer')} resource.",
    }

    beginner = intro.get(project_type, intro["general"])

    return {
        "type": "beginner_description",
        "content": f"{beginner} {desc}",
        "source": "Developer Hub Knowledge Layer",
        "disclaimer": "AI-generated beginner-friendly description",
    }


def compare_projects(entry_a, entry_b):
    """Compare two projects side by side."""
    name_a = entry_a.get("name", "A")
    name_b = entry_b.get("name", "B")

    comparison = {
        "type": "technology_comparison",
        "projects": [name_a, name_b],
        "aspects": [],
        "source": "Developer Hub Knowledge Layer",
        "disclaimer": "AI-generated comparison based on available metadata",
    }

    # Compare category
    cat_a = entry_a.get("category", "")
    cat_b = entry_b.get("category", "")
    if cat_a == cat_b:
        comparison["aspects"].append({
            "aspect": "Category",
            "a": cat_a,
            "b": cat_b,
            "verdict": "Same category",
        })
    else:
        comparison["aspects"].append({
            "aspect": "Category",
            "a": cat_a,
            "b": cat_b,
            "verdict": "Different categories — choose based on project requirements",
        })

    # Compare popularity
    pop_a = entry_a.get("popularity", 5)
    pop_b = entry_b.get("popularity", 5)
    comparison["aspects"].append({
        "aspect": "Popularity",
        "a": f"{pop_a}/10",
        "b": f"{pop_b}/10",
        "verdict": f"{name_a if pop_a > pop_b else name_b} is more popular",
    })

    # Compare maintenance
    maint_a = entry_a.get("maintained", False)
    maint_b = entry_b.get("maintained", False)
    comparison["aspects"].append({
        "aspect": "Maintained",
        "a": "✅ Yes" if maint_a else "❌ No",
        "b": "✅ Yes" if maint_b else "❌ No",
        "verdict": "Both maintained" if maint_a and maint_b else f"{'Neither' if not maint_a and not maint_b else name_a if maint_a else name_b} is actively maintained",
    })

    # Compare license
    lic_a = entry_a.get("license", "Unknown")
    lic_b = entry_b.get("license", "Unknown")
    comparison["aspects"].append({
        "aspect": "License",
        "a": lic_a,
        "b": lic_b,
        "verdict": "Both open-source-friendly" if "MIT" in lic_a or "Apache" in lic_a or "BSD" in lic_a else "Check license compatibility",
    })

    # Compare languages
    langs_a = entry_a.get("programming_languages", [])
    langs_b = entry_b.get("programming_languages", [])
    common = set(langs_a) & set(langs_b)
    if common:
        comparison["aspects"].append({
            "aspect": "Shared Languages",
            "a": ", ".join(langs_a),
            "b": ", ".join(langs_b),
            "verdict": f"Both use {', '.join(common)}",
        })

    return comparison


def main():
    import argparse
    parser = argparse.ArgumentParser(description="AI Knowledge Layer")
    parser.add_argument("--project", "-p", help="Generate AI content for a project")
    parser.add_argument("--compare", nargs=2, metavar=("ID_A", "ID_B"), help="Compare two projects")
    parser.add_argument("--beginner", help="Generate beginner-friendly description")
    parser.add_argument("--json", action="store_true", help="Output JSON")

    args = parser.parse_args()

    # Load entries
    entries = []
    by_id = {}
    for d in REPO_ROOT.iterdir():
        if not d.is_dir() or d.name not in CATEGORIES:
            continue
        for f in sorted(d.rglob("*.json")):
            try:
                with open(f) as fh:
                    data = json.load(fh)
                eid = data.get("id", "")
                entries.append(data)
                by_id[eid] = data
            except:
                pass

    if args.compare:
        a = by_id.get(args.compare[0])
        b = by_id.get(args.compare[1])
        if not a:
            print(f"Project '{args.compare[0]}' not found")
            sys.exit(1)
        if not b:
            print(f"Project '{args.compare[1]}' not found")
            sys.exit(1)

        comparison = compare_projects(a, b)
        if args.json:
            print(json.dumps(comparison, indent=2))
            return

        print(f"📊 Comparison: {a.get('name')} vs {b.get('name')}\n")
        for aspect in comparison["aspects"]:
            print(f"  {aspect['aspect']}:")
            print(f"    {a.get('name')}: {aspect['a']}")
            print(f"    {b.get('name')}: {aspect['b']}")
            print(f"    → {aspect['verdict']}\n")
        return

    target_id = args.project or args.beginner
    if not target_id:
        parser.print_help()
        return

    entry = by_id.get(target_id)
    if not entry:
        print(f"Project '{target_id}' not found")
        sys.exit(1)

    results = []

    # Always generate summary
    results.append(generate_summary(entry))

    # Use cases
    results.append(suggest_use_cases(entry))

    # Beginner description
    results.append(beginner_description(entry))

    if args.json:
        print(json.dumps(results, indent=2))
        return

    print(f"🧠 AI Knowledge Layer: {entry.get('name')}\n")
    print("=" * 55)

    for res in results:
        rtype = res.get("type", "")
        if rtype == "generated_summary":
            print(f"\n📝 Summary:\n  {res['content']}")
        elif rtype == "suggested_use_cases":
            print(f"\n🎯 Purpose:\n  {res['purpose']}")
            print(f"\n💡 Use Cases:")
            for uc in res["use_cases"]:
                print(f"  • {uc}")
        elif rtype == "beginner_description":
            print(f"\n👶 Beginner Friendly:\n  {res['content']}")
    print()


if __name__ == "__main__":
    main()
