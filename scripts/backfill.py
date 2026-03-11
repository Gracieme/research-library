#!/usr/bin/env python3
"""
One-time backfill: fetch all historical research papers from agent-for-news
"""

import json
import re
import requests
from datetime import date, timedelta
from pathlib import Path
from html.parser import HTMLParser

SOURCE_BASE = "https://gracieme.github.io/agent-for-news/data"
PAPERS_FILE = Path(__file__).parent.parent / "docs" / "papers.json"


def strip_tags(html):
    """Remove HTML tags and decode entities."""
    text = re.sub(r'<[^>]+>', '', html or '')
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>') \
               .replace('&quot;', '"').replace('&#39;', "'").replace('&nbsp;', ' ')
    return text.strip()


def parse_research_html(html):
    """Parse the research HTML into a list of paper dicts."""
    if not html or not isinstance(html, str):
        return []

    papers = []

    # Split by paper card (each paper starts with 📄 论文)
    # Cards are wrapped in divs with the gradient header
    card_pattern = re.compile(
        r'📄\s*论文\s*\d+.*?(?=📄\s*论文\s*\d+|$)',
        re.DOTALL
    )
    cards = card_pattern.findall(html)

    # Fallback: if no cards found, treat entire html as one card
    if not cards:
        cards = [html]

    def extract_field(card_html, *labels):
        """Extract text after any of the given label emojis."""
        for label in labels:
            # Match label cell followed by value cell
            pattern = re.compile(
                re.escape(label) + r'.*?</td>\s*<td[^>]*>(.*?)</td>',
                re.DOTALL | re.IGNORECASE
            )
            m = pattern.search(card_html)
            if m:
                return strip_tags(m.group(1))
        return ''

    def extract_doi(card_html):
        """Extract DOI/URL from anchor tag."""
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

        # Parse citations (e.g. "10 次" → 10)
        citations = 0
        m = re.search(r'(\d+)', citations_str)
        if m:
            citations = int(m.group(1))

        # Parse year
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


def fetch(date_str):
    url = f"{SOURCE_BASE}/{date_str}.json"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        pass
    return None


def load():
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


# ── Main ──────────────────────────────────────────────────────────────
existing = load()
total_added = 0
today = date.today()

for i in range(90):
    d = today - timedelta(days=i)
    date_str = d.strftime("%Y-%m-%d")
    data = fetch(date_str)
    if not data:
        continue

    research_html = data.get("research", "")
    new_papers = parse_research_html(research_html)

    if not new_papers:
        continue

    added = 0
    for j, paper in enumerate(new_papers):
        if is_dup(paper, existing):
            continue
        paper["added_date"] = date_str
        paper["id"] = f"{date_str}-{j}"
        existing.append(paper)
        added += 1
        total_added += 1

    if added:
        print(f"{date_str}: +{added} papers (e.g. '{new_papers[0]['title'][:50]}…')")

# Sort newest first
existing.sort(key=lambda p: p.get("added_date", ""), reverse=True)
save(existing)
print(f"\n✅ Done! Added: {total_added}, Total in library: {len(existing)}")
