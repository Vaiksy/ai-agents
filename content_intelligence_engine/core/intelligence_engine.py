"""
Intelligence Engine – v5.1 (Fixed - Embeddings Disabled)

Dynamic subdomains, keyword-based gap detection, structural saturation,
competitive intensity, split LLM calls. Pure data return.

EMBEDDINGS DISABLED - nomic-embed-text not installed
"""

import re
import time
from collections import Counter

from core.ollama_client import send_prompt, send_prompt_for_list
# EMBEDDINGS DISABLED - these imports are kept but never used
# from core.embedding_engine import embed_pages, compute_gap_scores, check_embedding_available
from core.research_engine import check_competitive_intensity


STOPWORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'is', 'it', 'this', 'that', 'are', 'was',
    'have', 'has', 'do', 'does', 'will', 'would', 'could', 'should', 'not',
    'no', 'so', 'if', 'than', 'very', 'just', 'about', 'all', 'also', 'as',
    'any', 'get', 'how', 'into', 'more', 'most', 'new', 'now', 'only',
    'other', 'our', 'out', 'some', 'them', 'there', 'these', 'they', 'those',
    'up', 'we', 'what', 'when', 'where', 'which', 'who', 'why', 'you',
    'your', 'one', 'use', 'like', 'know', 'see', 'way', 'even', 'well',
    'back', 'much', 'many', 'still', 'come', 'take', 'say', 'need', 'think',
    'want', 'give', 'first', 'last', 'right', 'good', 'help', 'try',
    'every', 'keep', 'work', 'start', 'top', 'best', 'make', 'used',
}

SEMANTIC_GAP_THRESHOLD = 0.35


def generate_dynamic_subdomains(niche: str, log: list = None) -> list:
    """Generate niche-specific subdomains via LLM."""
    if log is None:
        log = []

    prompt = """Given niche: "{niche}"
List exactly 15 major subdomains or problem areas for content creators in this niche.
Each item: 2-5 words. One per line. No numbers or bullets.
List:""".format(niche=niche)

    try:
        items = send_prompt_for_list(prompt, temperature=0.3)
        cleaned = [i.strip().rstrip('.') for i in items
                   if i.strip() and 2 <= len(i.split()) <= 8 and len(i) < 100][:15]

        if len(cleaned) < 5:
            log.append("LLM returned few subdomains. Using fallback.")
            return _fallback_subdomains()

        log.append("Generated {} dynamic subdomains.".format(len(cleaned)))
        return cleaned

    except (ConnectionError, RuntimeError) as exc:
        log.append("Subdomain generation failed: {}. Using fallback.".format(str(exc)[:60]))
        return _fallback_subdomains()


def _fallback_subdomains() -> list:
    return [
        "getting started", "common mistakes", "advanced strategies",
        "tools and resources", "case studies", "industry trends",
        "monetization", "audience building", "content creation",
        "community building", "automation", "analytics and metrics",
        "collaboration", "personal branding", "scaling operations",
    ]


def analyze_structural_saturation(research_data: list) -> dict:
    """Detect format saturation at title + content level."""
    total = len(research_data)
    if total == 0:
        return {"list_count": 0, "guide_count": 0, "comparison_count": 0,
                "total": 0, "list_percentage": 0.0, "content_list_percentage": 0.0,
                "dominant_format": "Unknown", "is_saturated": False, "top_bigrams": []}

    list_re = re.compile(r'\b(\d+|top|best|list|ultimate)\b', re.I)
    guide_re = re.compile(r'\b(guide|how[\s-]to|tutorial|step[\s-]by)\b', re.I)
    compare_re = re.compile(r'\b(vs\.?|versus|compar|alternative)\b', re.I)

    lc = gc = cc = 0
    for s in research_data:
        t = s.get("title", "") + " " + s.get("snippet", "")
        if list_re.search(t): lc += 1
        if guide_re.search(t): gc += 1
        if compare_re.search(t): cc += 1

    # Content-level
    content_list_re = re.compile(
        r'(^\d+\.|top\s+\d+|best\s+\d+|in\s+this\s+guide|here\s+are\s+\d+|step\s+\d+|#\d+)',
        re.I | re.M
    )
    clc = 0
    samples_text = 0
    for s in research_data:
        txt = s.get("summary", "") or s.get("content", "")
        if not txt:
            continue
        samples_text += 1
        if content_list_re.search(txt):
            clc += 1

    t_pct = (lc / total) * 100 if total else 0
    c_pct = (clc / samples_text) * 100 if samples_text else 0
    combined_pct = max(t_pct, c_pct)

    if combined_pct > 50:
        dominant = "Listicle saturation"
    elif gc > total * 0.4:
        dominant = "Guide/tutorial heavy"
    elif cc > total * 0.3:
        dominant = "Comparison heavy"
    else:
        dominant = "Mixed formats"

    # Bigrams
    texts = [s.get("title", "") + " " + s.get("snippet", "") for s in research_data]
    combined_text = re.sub(r'[^a-z\s]', ' ', ' '.join(texts).lower())
    words = [w for w in combined_text.split() if w not in STOPWORDS and len(w) > 2]
    bigrams = Counter("{} {}".format(words[i], words[i+1]) for i in range(len(words)-1))

    return {
        "list_count": lc, "guide_count": gc, "comparison_count": cc,
        "total": total, "list_percentage": round(t_pct, 1),
        "content_list_count": clc, "content_list_percentage": round(c_pct, 1),
        "dominant_format": dominant, "is_saturated": combined_pct > 50,
        "top_bigrams": [{"phrase": p, "count": c} for p, c in bigrams.most_common(10)],
    }


def detect_gaps(research_data: list, subdomains: list, log: list = None) -> list:
    """
    Run keyword-based gap detection.
    
    NOTE: Semantic/embedding-based detection is DISABLED because 
    nomic-embed-text is not installed.

    Args:
        research_data: Research dicts with summaries.
        subdomains: Dynamic subdomain list.
        log: Optional log list.

    Returns:
        List of gap result dicts.
    """
    if log is None:
        log = []

    # ALWAYS use keyword-based detection (embeddings disabled)
    log.append("Using keyword-based gap detection (embeddings disabled).")
    return _keyword_gaps(research_data, subdomains)


def _keyword_gaps(research_data: list, subdomains: list) -> list:
    """Keyword-based gap detection."""
    corpus = ' '.join(
        (s.get("title","") + " " + s.get("snippet","") + " " +
         s.get("content","") + " " + s.get("summary","")).lower()
        for s in research_data
    )
    results = []
    for sd in subdomains:
        words = [w.lower() for w in sd.split() if len(w) > 2]
        matches = sum(1 for w in words if w in corpus)
        cov = matches / len(words) if words else 0
        results.append({
            "subdomain": sd, 
            "similarity": round(cov, 3),
            "is_gap": cov < 0.3, 
            "method": "keyword"
        })
    results.sort(key=lambda x: (not x["is_gap"], x["similarity"]))
    return results


def run_competitive_checks(gap_results: list, niche: str, log: list = None) -> list:
    """Run competitive intensity for top gaps."""
    if log is None:
        log = []

    gaps = [g for g in gap_results if g.get("is_gap")]
    if not gaps:
        return []

    check_n = min(5, len(gaps))
    log.append("Checking competitive intensity for {} gaps.".format(check_n))

    results = []
    for gap in gaps[:check_n]:
        intensity = check_competitive_intensity(gap["subdomain"], niche)
        results.append(intensity)
        time.sleep(2.0)

    return results


def assess_signal(research_data: list) -> dict:
    """Assess research data quality."""
    total = len(research_data)
    with_content = sum(1 for r in research_data if r.get("content", "").strip())
    with_summary = sum(1 for r in research_data if r.get("summary", "").strip())
    total_chars = sum(len(r.get("content", "")) for r in research_data)
    scores = [r.get("score", 0) for r in research_data]
    avg = sum(scores) / len(scores) if scores else 0

    if total_chars > 5000:
        conf = "HIGH"
    elif total_chars > 2000:
        conf = "MEDIUM"
    else:
        conf = "LOW"

    return {
        "total_urls": total, "urls_with_content": with_content,
        "urls_with_summaries": with_summary,
        "total_content_chars": total_chars,
        "avg_heuristic_score": round(avg, 1),
        "confidence": conf,
    }


def _build_corpus(research_data: list, max_chars: int = 3000) -> str:
    """Build LLM corpus from summaries with context safety."""
    total = sum(len(r.get("summary", "")) for r in research_data)
    working = research_data
    if total > max_chars:
        working = sorted(research_data, key=lambda x: x.get("score", 0), reverse=True)[:3]

    parts = []
    for i, s in enumerate(working, 1):
        lines = ["--- Sample {} ---".format(i),
                 "Title: {}".format(s.get("title", "N/A"))]
        snippet = s.get("snippet", "").strip()
        if snippet:
            lines.append("Snippet: {}".format(snippet[:200]))
        summary = s.get("summary", "").strip()
        if summary:
            lines.append("Summary: {}".format(summary))
        elif s.get("content", "").strip():
            lines.append("Excerpt: {}".format(s["content"][:300]))
        lines.append("Score: {}".format(s.get("score", 0)))
        lines.append("")
        parts.append('\n'.join(lines))

    result = '\n'.join(parts)
    if len(result) > max_chars:
        result = result[:max_chars] + "\n[... trimmed ...]"
    return result


def _kw_data(keywords: list) -> str:
    if not keywords:
        return "Keywords: none."
    return "Top keywords: " + ", ".join("'{}' ({}x)".format(w, c) for w, c in keywords[:15])


def extract_insights(research_data: list, keywords: list, log: list = None) -> str:
    """
    Run two LLM calls for intelligence extraction.

    Returns:
        Combined insights text.
    """
    if log is None:
        log = []

    corpus = _build_corpus(research_data)
    kw = _kw_data(keywords)

    # Call 1: Structure
    p1 = """Analyze content summaries. Use ONLY data provided. No invented statistics.
Quote at least 2 phrases. If insufficient, say "INSUFFICIENT DATA".

{kw}

{corpus}

Analyze ONLY:
1. HOOK PATTERNS - opening structures, specific hooks, formulas
2. OPENING STRUCTURES - first sentence patterns
3. CTA PATTERNS - call-to-action verbs and context""".format(kw=kw, corpus=corpus)

    log.append("Intelligence Call 1: Hooks, structure, CTAs")
    insights1 = send_prompt(p1, temperature=0.2)

    # Call 2: Theme
    p2 = """Analyze content summaries. Use ONLY data provided. No invented statistics.
Quote at least 2 phrases. If insufficient, say "INSUFFICIENT DATA".

{kw}

{corpus}

Analyze ONLY:
1. EMOTIONAL TONE - register, example phrases
2. RECURRING THEMES - repeated topics, keyword connections
3. POSITIONING - creator positioning, authority signals""".format(kw=kw, corpus=corpus)

    log.append("Intelligence Call 2: Tone, themes, positioning")
    insights2 = send_prompt(p2, temperature=0.3)

    return "=== STRUCTURAL ANALYSIS ===\n\n{}\n\n=== THEMATIC ANALYSIS ===\n\n{}".format(
        insights1, insights2
    )
