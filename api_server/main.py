#!/usr/bin/env python3
"""
Developer Hub REST API - FastAPI Server (v2.0)

Upgraded with:
- Intelligent search (fuzzy, suggestions, ranking)
- Relationship graph
- Recommendations engine
- Trending & discovery
- Analytics dashboard
- Quality scoring

Run: uvicorn api_server.main:app --reload
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional, Annotated
from pydantic import StringConstraints
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.search_engine import SearchEngine
from scripts.relationships import build_graph, find_similar, load_entries as load_rel_entries
from scripts.recommendations import (
    recommend_for_project, get_trending, get_recently_updated,
    recommend_stack, STACKS
)
from scripts.scoring import calculate_score, star_rating
from scripts.ai_knowledge import generate_summary, suggest_use_cases, beginner_description, compare_projects
from scripts.cache import api_cache, search_cache, data_cache
from scripts.analytics import compute_analytics

app = FastAPI(
    title="Developer Hub API",
    description="Open-source API for discovering developer resources — APIs, SDKs, libraries, frameworks, tools, and more",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.responses import Response
import hashlib

@app.middleware("http")
async def cache_middleware(request, call_next):
    # Add cache headers
    response = await call_next(request)
    if request.method == "GET" and response.status_code == 200:
        # Cache for 60s on search endpoints, 300s on others
        if "/search" in request.url.path or "/suggest" in request.url.path:
            response.headers["Cache-Control"] = "public, max-age=60"
        elif "/stats" in request.url.path or "/trending" in request.url.path:
            response.headers["Cache-Control"] = "public, max-age=300"
        else:
            response.headers["Cache-Control"] = "public, max-age=120"
        response.headers["X-Cache"] = "miss"
    return response

# Initialize engines
search_engine = SearchEngine()
entries = load_rel_entries()
by_id = {e.get("id", ""): e for e in entries}
relationship_graph = None


@app.on_event("startup")
async def startup():
    global relationship_graph
    search_engine.build_index()
    relationship_graph = build_graph(entries)


@app.get("/api")
async def root():
    analytics = compute_analytics(entries)
    return {
        "name": "Developer Hub API",
        "version": "2.0.0",
        "total_projects": analytics["overview"]["total_projects"],
        "total_categories": analytics["overview"]["total_categories"],
        "endpoints": {
            "GET /projects": "List all projects",
            "GET /projects/{id}": "Get project by ID",
            "GET /search?q=": "Intelligent search with fuzzy matching",
            "GET /suggest?q=": "Search suggestions",
            "GET /category/{name}": "Filter by category",
            "GET /language/{name}": "Filter by programming language",
            "GET /relationships/{id}": "Project relationships graph",
            "GET /recommendations/{id}": "Smart recommendations",
            "GET /trending": "Trending projects",
            "GET /recent": "Recently updated",
            "GET /stacks": "Popular tech stacks",
            "GET /stacks/{name}": "Stack details",
            "GET /score/{id}": "Quality score",
            "GET /stats": "Analytics dashboard",
            "GET /popular-searches": "Popular search queries",
            "GET /health": "Health check",
        },
        "source": "https://github.com/soe1hom-arch/developer-hub",
    }


@app.get("/search")
async def search(
    q: str = Query(..., min_length=1, max_length=200, pattern=r'^[ -~]+$'),
    fuzzy: bool = Query(True),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
):
    # Check cache
    cache_key = f"search:{q}:{fuzzy}:{page}:{per_page}"
    cached = search_cache.get(cache_key)
    if cached:
        return cached
    """Intelligent search with fuzzy matching and relevance ranking."""
    results = search_engine.search(q, fuzzy=fuzzy, max_results=200)
    # Apply pagination
    start = (page - 1) * per_page
    end = start + per_page
    page_results = results[start:end]

    result = {
        "query": q,
        "total": len(results),
        "page": page,
        "per_page": per_page,
        "total_pages": max(1, (len(results) + per_page - 1) // per_page),
        "results": page_results,
    }
    search_cache.set(cache_key, result)
    return result


@app.get("/suggest")
async def suggest(q: str = Query(..., min_length=2)):
    """Get search suggestions for autocomplete."""
    suggestions = search_engine.suggest(q)
    return {"query": q, "suggestions": suggestions}


@app.get("/popular-searches")
async def popular_searches(limit: int = Query(10, ge=1, le=50)):
    """Get most popular search queries."""
    return {"searches": search_engine.get_popular_searches(limit)}


@app.get("/projects")
async def list_projects(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    category: Optional[str] = None,
    sort_by: Optional[str] = None,
):
    """List all projects with pagination and sorting."""
    filtered = entries
    if category:
        filtered = [e for e in filtered if e.get("category") == category]

    if sort_by == "popularity":
        filtered.sort(key=lambda e: e.get("popularity", 0), reverse=True)
    elif sort_by == "name":
        filtered.sort(key=lambda e: e.get("name", ""))
    else:
        filtered.sort(key=lambda e: e.get("last_updated", ""), reverse=True)

    total = len(filtered)
    start = (page - 1) * per_page
    end = start + per_page

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": max(1, (total + per_page - 1) // per_page),
        "results": filtered[start:end],
    }


@app.get("/projects/{project_id}")
async def get_project(project_id: str):
    """Get a single project by its ID with quality score."""
    entry = by_id.get(project_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")

    result = dict(entry)
    result["quality_score"] = calculate_score(entry)
    return result


@app.get("/category/{category_name}")
async def by_category(category_name: str):
    """Get all projects in a specific category."""
    results = [e for e in entries if e.get("category") == category_name]
    if not results:
        raise HTTPException(status_code=404, detail=f"Category '{category_name}' not found")
    return {"category": category_name, "total": len(results), "results": results}


@app.get("/language/{language_name}")
async def by_language(language_name: str):
    """Get all projects that use a specific programming language."""
    query = language_name.lower()
    results = [
        e for e in entries
        if any(query in lang.lower() for lang in e.get("programming_languages", []))
    ]
    return {"language": language_name, "total": len(results), "results": results}


@app.get("/relationships/{project_id}")
async def relationships(project_id: str):
    """Get relationship graph for a project."""
    if not relationship_graph:
        raise HTTPException(status_code=503, detail="Relationship graph not loaded")

    if project_id not in by_id:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")

    rels = relationship_graph.get(project_id, {
        "alternatives": [], "commonly_used_with": [], "similar": [], "same_category": []
    })

    # Enrich with quality scores
    for key in rels:
        for item in rels[key]:
            related = by_id.get(item.get("id"))
            if related:
                item["popularity"] = related.get("popularity")
                item["category"] = related.get("category")

    return {"project_id": project_id, "relationships": rels}


@app.get("/recommendations/{project_id}")
async def recommendations(project_id: str):
    """Get smart recommendations for a project."""
    if project_id not in by_id:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")

    recs = recommend_for_project(project_id, entries, by_id)
    result = []
    for score, reasons, entry in recs:
        result.append({
            "id": entry.get("id"),
            "name": entry.get("name"),
            "category": entry.get("category"),
            "description": entry.get("description", "")[:150],
            "popularity": entry.get("popularity"),
            "score": round(score, 1),
            "reasons": reasons,
        })

    return {
        "project_id": project_id,
        "project_name": by_id[project_id].get("name"),
        "recommendations": result,
    }


@app.get("/trending")
async def trending(limit: int = Query(10, ge=1, le=50)):
    """Get trending projects."""
    trending_list = get_trending(entries, by_id, max_results=limit)
    return {
        "trending": [
            {
                "id": entry.get("id"),
                "name": entry.get("name"),
                "category": entry.get("category"),
                "popularity": entry.get("popularity"),
                "trend_score": round(score, 1),
            }
            for score, entry in trending_list
        ]
    }


@app.get("/recent")
async def recent(limit: int = Query(10, ge=1, le=50)):
    """Get recently updated projects."""
    recent_list = get_recently_updated(entries, max_results=limit)
    return {
        "recent": [
            {
                "id": entry.get("id"),
                "name": entry.get("name"),
                "category": entry.get("category"),
                "last_updated": entry.get("last_updated"),
            }
            for _, entry in recent_list
        ]
    }


@app.get("/stacks")
async def list_stacks():
    """List all available tech stacks."""
    return {
        "stacks": [
            {"id": key, "name": stack["name"], "description": stack["description"],
             "project_count": len(stack["projects"])}
            for key, stack in STACKS.items()
        ]
    }


@app.get("/stacks/{stack_name}")
async def get_stack(stack_name: str):
    """Get projects in a specific tech stack."""
    result = recommend_stack(stack_name, by_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Stack '{stack_name}' not found")
    return result


@app.get("/score/{project_id}")
async def score(project_id: str):
    """Get quality score for a project."""
    entry = by_id.get(project_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")

    sc = calculate_score(entry)
    return {
        "project_id": project_id,
        "project_name": entry.get("name"),
        "scores": sc,
        "stars": {
            "documentation": star_rating(sc["documentation"]),
            "maintenance": star_rating(sc["maintenance"]),
            "popularity": star_rating(sc["popularity"]),
            "version": star_rating(sc["version"]),
            "license": star_rating(sc["license"]),
        },
    }


@app.get("/stats")
async def stats():
    """Get comprehensive analytics dashboard data."""
    analytics = compute_analytics(entries)
    return analytics



@app.get("/knowledge/{project_id}")
async def knowledge(project_id: str):
    """Get AI-enriched content for a project."""
    entry = by_id.get(project_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
    return {
        "project_id": project_id,
        "project_name": entry.get("name"),
        "summary": generate_summary(entry),
        "use_cases": suggest_use_cases(entry),
        "beginner_description": beginner_description(entry),
    }


@app.get("/compare")
async def compare(a: str = Query(...), b: str = Query(...)):
    """Compare two projects side by side."""
    entry_a = by_id.get(a)
    entry_b = by_id.get(b)
    if not entry_a:
        raise HTTPException(status_code=404, detail=f"Project '{a}' not found")
    if not entry_b:
        raise HTTPException(status_code=404, detail=f"Project '{b}' not found")
    return compare_projects(entry_a, entry_b)


@app.get("/health")

async def health():
    """API health check."""
    return {
        "status": "ok",
        "entries_loaded": len(entries),
        "api_version": "2.0.0",
        "index_terms": len(search_engine.inverted_index),
        "relationship_nodes": len(relationship_graph) if relationship_graph else 0,
    }


# Mount static website - serve index.html at root
app.mount("/", StaticFiles(directory=str(REPO_ROOT / "website"), html=True), name="website")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
