#!/usr/bin/env python3
"""
Daily script: fetch today's research papers from agent-for-news → append to papers.json
"""

import json
import re
import requests
import sys
from datetime import date, timedelta
from pathlib import Path

from curation import inspiration_rejection_reason

SOURCE_BASE = "https://gracieme.github.io/agent-for-news/data"
PAPERS_FILE = Path(__file__).parent.parent / "docs" / "papers.json"


def strip_tags(html):
    text = re.sub(r'<[^>]+>', '', html or '')
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>') \
               .replace('&quot;', '"').replace('&#39;', "'").replace('&nbsp;', ' ')
    return text.strip()


def parse_research_html(html):
    if not html or not isinstance(html, str):
        return []

    papers = []
    card_pattern = re.compile(r'📄\s*论文\s*\d+.*?(?=📄\s*论文\s*\d+|$)', re.DOTALL)
    cards = card_pattern.findall(html)
    if not cards:
        cards = [html]

    def extract_field(card_html, *labels):
        for label in labels:
            pattern = re.compile(
                re.escape(label) + r'.*?</td>\s*<td[^>]*>(.*?)</td>',
                re.DOTALL | re.IGNORECASE
            )
            m = pattern.search(card_html)
            if m:
                return strip_tags(m.group(1))
        return ''

    def extract_doi(card_html):
        m = re.search(r'href=["\']([^"\']+)["\']', card_html)
        if m:
            href = m.group(1)
            if 'doi.org' in href or 'scholar.google' in href or href.startswith('http'):
                return href
        return ''

    for i, card in enumerate(cards):
        title = extract_field(card, '📖 标题：', '标题：')
        author = extract_field(card, '📌 作者：', '作者：')
        journal = extract_field(card, '📰 期刊：', '期刊：')
        year_str = extract_field(card, '📅 年份：', '年份：')
        citations_str = extract_field(card, '📊 引用量：', '引用量：', '引用：')
        abstract = extract_field(card, '📝 摘要：', '摘要：')
        relevance = extract_field(card, '🔗 与本研究的关联性：', '与本研究的关联性：', '关联性：')
        doi = extract_doi(card)

        citations = 0
        m = re.search(r'(\d+)', citations_str)
        if m:
            citations = int(m.group(1))

        year = 0
        m = re.search(r'(19|20)\d{2}', year_str)
        if m:
            year = int(m.group(0))

        if not title:
            continue

        papers.append({
            'title': title,
            'author': author,
            'journal': journal,
            'year': year,
            'citations': citations,
            'abstract': abstract if abstract != '摘要不可用' else '',
            'relevance': relevance,
            'doi': doi,
        })

    return papers


def fetch_daily(date_str):
    url = f"{SOURCE_BASE}/{date_str}.json"
    print(f"Fetching: {url}")
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            return r.json()
        print(f"  Not found (HTTP {r.status_code})")
    except Exception as e:
        print(f"  Error: {e}")
    return None


def load_existing():
    if PAPERS_FILE.exists():
        with open(PAPERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def is_dup(paper, existing):
    doi = (paper.get("doi") or "").strip()
    title = (paper.get("title") or "").strip().lower()
    for p in existing:
        if doi and doi == (p.get("doi") or "").strip():
            return True
        if title and title == (p.get("title") or "").strip().lower():
            return True
    return False


def save(papers):
    with open(PAPERS_FILE, "w", encoding="utf-8") as f:
        json.dump(papers, f, ensure_ascii=False, indent=2)


def main():
    today = date.today().strftime("%Y-%m-%d")
    data = fetch_daily(today)
    if data is None:
        yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        data = fetch_daily(yesterday)

    if data is None:
        print("No data found. Exiting.")
        sys.exit(0)

    new_papers = parse_research_html(data.get("research", ""))
    if not new_papers:
        print("No papers parsed today.")
        sys.exit(0)

    accepted_papers = []
    for paper in new_papers:
        reason = inspiration_rejection_reason(paper, require_transfer_marker=True)
        if reason:
            print(f"  Reject (not inspiration-grade): {paper.get('title','')[:60]} — {reason}")
            continue
        accepted_papers.append(paper)
    new_papers = accepted_papers
    if not new_papers:
        print("No papers passed the inspiration-only gate. Library unchanged.")
        sys.exit(0)

    existing = load_existing()
    added = 0
    for j, paper in enumerate(new_papers):
        if is_dup(paper, existing):
            print(f"  Skip (duplicate): {paper.get('title','')[:60]}")
            continue
        paper["added_date"] = today
        paper["id"] = f"{today}-{j}"
        existing.insert(0, paper)
        added += 1
        print(f"  Added: {paper.get('title','')[:60]}")

    save(existing)
    print(f"\nDone. Added {added} new paper(s). Total: {len(existing)}")


if __name__ == "__main__":
    main()
