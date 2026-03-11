#!/usr/bin/env python3
"""
Verify papers in papers.json by checking that their DOIs resolve correctly.
Removes papers whose DOIs return 404 or are scholar.google.com links.
Papers that time out or have connection errors are flagged but NOT removed
(to avoid false positives from transient network issues).
"""

import json
import sys
import time
from pathlib import Path

import requests
from requests.exceptions import ConnectionError, Timeout, RequestException

PAPERS_FILE = Path(__file__).parent.parent / "docs" / "papers.json"
REMOVED_FILE = Path(__file__).parent.parent / "docs" / "removed_papers.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (research-library DOI verifier; contact via GitHub)"
}
TIMEOUT = 15


def is_suspicious_doi(doi: str) -> bool:
    """Flag DOIs that use scholar.google.com as a proxy (not a real DOI link)."""
    return "scholar.google.com" in doi


def check_doi(doi: str) -> tuple[str, str]:
    """
    Returns (status, reason) where status is 'valid', 'invalid', or 'unknown'.
    - 'invalid': definitively fake (404 or scholar.google proxy)
    - 'unknown': could not verify due to network issues (do not remove)
    - 'valid': DOI resolves successfully
    """
    if not doi or not doi.startswith("http"):
        return "invalid", "no valid DOI URL"

    if is_suspicious_doi(doi):
        return "invalid", "uses scholar.google.com proxy instead of real DOI"

    try:
        r = requests.head(doi, headers=HEADERS, timeout=TIMEOUT,
                          allow_redirects=True)
        if r.status_code == 404:
            return "invalid", "DOI returns 404"
        if r.status_code in (405, 403):
            # Server rejected HEAD; try a GET but only read a tiny bit
            try:
                r2 = requests.get(doi, headers=HEADERS, timeout=TIMEOUT,
                                  allow_redirects=True)
                if r2.status_code == 404:
                    return "invalid", "DOI returns 404"
                return "valid", f"OK ({r2.status_code})"
            except Exception:
                # If GET also fails, treat as unknown (don't remove)
                return "unknown", "HEAD rejected, GET also failed"
        return "valid", f"OK ({r.status_code})"

    except (ConnectionError, Timeout) as e:
        return "unknown", f"network error: {type(e).__name__}"
    except RequestException as e:
        return "unknown", f"request error: {type(e).__name__}"
    except Exception as e:
        return "unknown", f"unexpected error: {type(e).__name__}"


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
    unknown = []

    for paper in papers:
        title = paper.get("title", "")[:70]
        doi = paper.get("doi", "")
        status, reason = check_doi(doi)

        if status == "valid":
            print(f"✅ [{paper.get('id', '?')}] {title}")
            valid.append(paper)
        elif status == "invalid":
            print(f"❌ [{paper.get('id', '?')}] {title}")
            print(f"   Reason: {reason}")
            paper["removed_reason"] = reason
            removed.append(paper)
        else:
            print(f"⚠️  [{paper.get('id', '?')}] {title}")
            print(f"   Could not verify: {reason} (kept)")
            valid.append(paper)
            unknown.append(paper)

        time.sleep(1)  # be polite to servers

    print(f"\n--- Summary ---")
    print(f"Valid:       {len(valid)}")
    print(f"Removed:     {len(removed)}")
    print(f"Unverified:  {len(unknown)} (kept, network issues)")

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
