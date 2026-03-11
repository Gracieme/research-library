#!/usr/bin/env python3
"""
Verify papers in papers.json by checking that their DOIs resolve correctly.
Removes papers whose DOIs return 404 or are scholar.google.com links.
Outputs a summary and exits with code 1 if any papers were removed.
"""

import json
import re
import sys
import time
from pathlib import Path

import requests

PAPERS_FILE = Path(__file__).parent.parent / "docs" / "papers.json"
REMOVED_FILE = Path(__file__).parent.parent / "docs" / "removed_papers.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (research-library DOI verifier; contact via GitHub)"
}
TIMEOUT = 15


def is_suspicious_doi(doi: str) -> bool:
    """Flag DOIs that use scholar.google.com as a proxy (not a real DOI link)."""
    return "scholar.google.com" in doi


def check_doi(doi: str) -> tuple[bool, str]:
    """
    Returns (is_valid, reason).
    A DOI is valid if it redirects/resolves without a 404.
    """
    if not doi or not doi.startswith("http"):
        return False, "no valid DOI URL"

    if is_suspicious_doi(doi):
        return False, "uses scholar.google.com proxy instead of real DOI"

    try:
        r = requests.head(doi, headers=HEADERS, timeout=TIMEOUT,
                          allow_redirects=True)
        if r.status_code == 404:
            return False, f"DOI returns 404"
        if r.status_code == 405:
            # Some servers reject HEAD; try GET
            r = requests.get(doi, headers=HEADERS, timeout=TIMEOUT,
                             allow_redirects=True, stream=True)
            r.close()
            if r.status_code == 404:
                return False, f"DOI returns 404"
        return True, f"OK ({r.status_code})"
    except requests.exceptions.ConnectionError:
        return False, "connection error"
    except requests.exceptions.Timeout:
        return False, "timeout"
    except Exception as e:
        return False, f"error: {e}"


def load_removed() -> list:
    if REMOVED_FILE.exists():
        with open(REMOVED_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_json(path: Path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    with open(PAPERS_FILE, "r", encoding="utf-8") as f:
        papers = json.load(f)

    print(f"Verifying {len(papers)} papers...\n")

    valid = []
    removed = []

    for paper in papers:
        title = paper.get("title", "")[:70]
        doi = paper.get("doi", "")
        ok, reason = check_doi(doi)
        status = "✅" if ok else "❌"
        print(f"{status} [{paper.get('id', '?')}] {title}")
        if not ok:
            print(f"   Reason: {reason}")
            paper["removed_reason"] = reason
            removed.append(paper)
        else:
            valid.append(paper)
        time.sleep(1)  # be polite to servers

    print(f"\n--- Summary ---")
    print(f"Valid:   {len(valid)}")
    print(f"Removed: {len(removed)}")

    if removed:
        save_json(PAPERS_FILE, valid)
        existing_removed = load_removed()
        existing_ids = {p.get("id") for p in existing_removed}
        for p in removed:
            if p.get("id") not in existing_ids:
                existing_removed.append(p)
        save_json(REMOVED_FILE, existing_removed)
        print(f"\nRemoved papers saved to docs/removed_papers.json")
        print("Removed titles:")
        for p in removed:
            print(f"  - {p.get('title', '')[:80]}")
        sys.exit(1)
    else:
        print("\nAll papers verified. No changes made.")
        sys.exit(0)


if __name__ == "__main__":
    main()
