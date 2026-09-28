#!/usr/bin/env python3
"""One-time and repeatable curation for the inspiration-only research library."""

import argparse
import json
from collections import Counter
from pathlib import Path

from curation import inspiration_rejection_reason


PAPERS_FILE = Path(__file__).parent.parent / "docs" / "papers.json"


REMOVED_FILE = PAPERS_FILE.parent / "removed_papers.json"


def load_json(path, default):
    if not path.exists():
        return default
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def curate(papers):
    kept = []
    removed = []
    for paper in papers:
        reason = inspiration_rejection_reason(paper, require_transfer_marker=False)
        if reason:
            removed_copy = dict(paper)
            removed_copy["removed_reason"] = f"inspiration-only curation: {reason}"
            removed.append(removed_copy)
        else:
            kept.append(paper)
    return kept, removed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="write the curated library and archive removed entries")
    args = parser.parse_args()

    papers = load_json(PAPERS_FILE, [])
    kept, removed = curate(papers)
    counts = Counter(item["removed_reason"] for item in removed)

    print(f"Current papers: {len(papers)}")
    print(f"Keep:           {len(kept)}")
    print(f"Remove:         {len(removed)}")
    for reason, count in counts.most_common():
        print(f"  {count:>3}  {reason}")

    if not args.apply:
        print("Dry run only. Re-run with --apply to write changes.")
        return

    existing_removed = load_json(REMOVED_FILE, [])
    existing_ids = {item.get("id") for item in existing_removed}
    existing_removed.extend(item for item in removed if item.get("id") not in existing_ids)
    save_json(PAPERS_FILE, kept)
    save_json(REMOVED_FILE, existing_removed)
    print(f"Wrote {PAPERS_FILE} and archived removed entries in {REMOVED_FILE}.")


if __name__ == "__main__":
    main()
