#!/usr/bin/env python3
"""
Daily script: fetch research papers from agent-for-news and append to papers.json
"""

import json
import requests
import sys
from datetime import date, timedelta
from pathlib import Path

SOURCE_BASE = "https://gracieme.github.io/agent-for-news/data"
PAPERS_FILE = Path(__file__).parent.parent / "docs" / "papers.json"


def fetch_daily_data(date_str: str) -> dict | None:
    url = f"{SOURCE_BASE}/{date_str}.json"
    print(f"Fetching: {url}")
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            return r.json()
        print(f"  Not found (HTTP {r.status_code})")
        return None
    except Exception as e:
        print(f"  Error: {e}")
        return None


def load_existing() -> list:
    if PAPERS_FILE.exists():
        with open(PAPERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def is_duplicate(paper: dict, existing: list) -> bool:
    doi = paper.get("doi", "").strip()
    title = paper.get("title", "").strip().lower()
    for p in existing:
        if doi and doi == p.get("doi", "").strip():
            return True
        if title and title == p.get("title", "").strip().lower():
            return True
    return False


def save(papers: list):
    with open(PAPERS_FILE, "w", encoding="utf-8") as f:
        json.dump(papers, f, ensure_ascii=False, indent=2)


def main():
    today = date.today().strftime("%Y-%m-%d")

    # Try today, then yesterday (in case of timezone differences)
    data = fetch_daily_data(today)
    if data is None:
        yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        data = fetch_daily_data(yesterday)

    if data is None:
        print("No data found. Exiting.")
        sys.exit(0)

    research = data.get("research", {})
    # Support both {"papers": [...]} and direct list
    if isinstance(research, dict):
        new_papers = research.get("papers", [])
    elif isinstance(research, list):
        new_papers = research
    else:
        print("Unexpected research format. Exiting.")
        sys.exit(0)

    if not new_papers:
        print("No research papers in today's data.")
        sys.exit(0)

    existing = load_existing()
    added = 0

    for paper in new_papers:
        if is_duplicate(paper, existing):
            print(f"  Skip (duplicate): {paper.get('title', '')[:60]}")
            continue
        paper["added_date"] = today
        # Generate a unique id
        paper["id"] = f"{today}-{added}"
        existing.insert(0, paper)
        added += 1
        print(f"  Added: {paper.get('title', '')[:60]}")

    save(existing)
    print(f"\nDone. Added {added} new paper(s). Total: {len(existing)}")


if __name__ == "__main__":
    main()
