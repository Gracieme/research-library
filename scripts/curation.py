"""Shared inspiration-only curation rules for ingestion and library cleanup."""

RETIRED_RESEARCH_TERMS = (
    "micm",
    "multimodal interactional competence model",
    "language-related episode",
    "lre onset",
    "negotiation of meaning",
    "csl peer interaction",
)

WEAK_RELEVANCE_MARKERS = (
    "关联度较低",
    "关联性较低",
    "关联有限",
    "关联性有限",
    "间接关联",
    "仅在主题词层面",
    "关键词相关",
    "外围理论层",
    "外围情境层",
    "外围-语境层",
    "外围概念层",
    "外围参考",
    "部分相关",
    "表层关联",
    "表层相交",
    "表层重叠",
    "边缘相关",
    "背景参考",
    "最宽泛",
    "仅在emi这一宏观场景",
    "仅在\"translanguaging\"这一关键词层面",
    "差距较大",
    "距离较远",
    "微弱关联",
    "没有实质交集",
    "无实质关联",
    "极表层",
    "参考价值极为有限",
    "关联性较弱",
    "直接关联较弱",
    "有一定间接关联",
    "存在一定间接关联",
    "没有直接对接",
    "没有直接关联",
    "几乎没有直接关联",
    "反面参照",
)

MAINLINE_TERM_GROUPS = (
    ("teacher vulnerability", "teacher voice", "emotional labor", "institutional discourse", "dual language immersion", "autoethnograph"),
    ("assessment fairness", "curriculum fairness", "critical language testing", "language assessment", "transnational qualification", "language policy", "epistemic injustice"),
    ("emi", "identity negotiation", "teacher action research", "teacher mediation", "language ideology", "multilingual pedagogy"),
    ("curriculum localization", "textbook discourse", "linguistic participation", "domain legitimacy", "textbook monolingualism"),
    ("social media", "xiaohongshu", "digital multilingualism", "platform discourse", "intercultural participation", "linguistic capital"),
)


def inspiration_rejection_reason(paper, require_transfer_marker=True):
    """Return a reason when a paper should not enter the inspiration-only library."""
    title = str(paper.get("title") or "")
    abstract = str(paper.get("abstract") or "")
    relevance = str(paper.get("relevance") or "")
    text = f"{title} {abstract} {relevance}".lower()

    if any(term in text for term in RETIRED_RESEARCH_TERMS):
        return "retired MICM/LRE/negotiation-of-meaning research line"
    if any(marker in relevance for marker in WEAK_RELEVANCE_MARKERS):
        return "relevance note explicitly says the paper is weak or peripheral"
    if not any(any(term in text for term in group) for group in MAINLINE_TERM_GROUPS):
        return "does not connect to a published mainline or approved extension"
    if require_transfer_marker and "可迁移动作：" not in relevance:
        return "missing a concrete transferable research move"
    return ""


def is_inspiring_paper(paper, require_transfer_marker=True):
    return not inspiration_rejection_reason(paper, require_transfer_marker)
