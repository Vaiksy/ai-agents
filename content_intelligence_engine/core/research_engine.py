"""
Research Engine – v5.0

DuckDuckGo + Bing fallback, caching, content extraction,
heuristic scoring, hierarchical summarization via LLM.
All output as data structures — no terminal printing.
"""

import re
import os
import json
import time
import random
import hashlib
import requests
from collections import Counter
from bs4 import BeautifulSoup
from urllib.parse import unquote

from core.ollama_client import send_summary_prompt


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

DUCKDUCKGO_URL = "https://html.duckduckgo.com/html/"
BING_URL = "https://www.bing.com/search"
MAX_RETRIES = 2
CONTENT_EXTRACT_LIMIT = 5
MAX_CONTENT_LENGTH = 1200
MIN_CONTENT_LENGTH = 300
CACHE_DIR = "cache"
CACHE_MAX_AGE_HOURS = 24

POWER_WORDS = {
    "ultimate", "secret", "proven", "explosive", "mistake", "breakdown",
    "step-by-step", "hack", "strategy", "deadly", "hidden", "crucial",
    "essential", "surprising", "shocking", "powerful", "critical",
    "guaranteed", "instant", "exclusive", "revolutionary", "incredible",
}

STOPWORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'is', 'it', 'its', 'this', 'that', 'are',
    'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
    'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'shall',
    'not', 'no', 'nor', 'so', 'if', 'then', 'than', 'too', 'very', 'just',
    'about', 'above', 'after', 'again', 'all', 'also', 'am', 'as', 'any',
    'because', 'before', 'below', 'between', 'both', 'each', 'few', 'get',
    'got', 'he', 'her', 'here', 'him', 'his', 'how', 'i', 'into', 'me',
    'more', 'most', 'my', 'new', 'now', 'only', 'other', 'our', 'out',
    'over', 'own', 'same', 'she', 'some', 'such', 'them', 'there', 'these',
    'they', 'those', 'through', 'under', 'up', 'us', 'we', 'what', 'when',
    'where', 'which', 'while', 'who', 'whom', 'why', 'you', 'your', 'one',
    'two', 'use', 'used', 'using', 'make', 'like', 'know', 'see', 'way',
    'even', 'well', 'back', 'much', 'many', 'still', 'come', 'take', 'say',
    'said', 'need', 'look', 'think', 'want', 'give', 'first', 'last', 'long',
    'great', 'little', 'right', 'good', 'big', 'high', 'different', 'small',
    'large', 'next', 'early', 'young', 'important', 'let', 'thing', 'things',
    'go', 'going', 'went', 'really', 'read', 'best', 'top', 'help', 'try',
    'every', 'keep', 'work', 'working', 'put', 'end', 'start', 'turn',
}

NICHE_KEYWORD_MAP = {
    "founder": ["founder", "startup", "indie", "entrepreneur", "bootstrapped", "solopreneur"],
    "startup": ["startup", "founder", "venture", "mvp", "fundraising", "entrepreneur"],
    "indie": ["indie", "hacker", "bootstrapped", "solopreneur", "maker", "builder"],
    "entrepreneur": ["entrepreneur", "founder", "business", "startup", "venture"],
    "creator": ["creator", "content", "audience", "brand", "influencer"],
    "marketer": ["marketer", "marketing", "growth", "funnel", "conversion"],
    "developer": ["developer", "dev", "code", "programming", "software"],
    "freelancer": ["freelancer", "freelance", "client", "contract", "agency"],
}

NICHE_QUERY_ENRICHMENT = {
    "founder": ["founder workflow", "startup execution", "indie hacker", "startup growth"],
    "startup": ["startup operations", "early stage growth", "startup toolkit"],
    "indie": ["indie hacker tools", "bootstrapped growth", "solo builder"],
    "entrepreneur": ["entrepreneur systems", "business automation"],
    "creator": ["creator tools", "content workflow", "creator economy"],
    "marketer": ["marketing automation", "growth strategy"],
    "developer": ["dev tools", "developer workflow"],
    "freelancer": ["freelance workflow", "client management"],
}


def _headers() -> dict:
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.5",
        "DNT": "1",
    }


def _delay() -> None:
    time.sleep(random.uniform(1.5, 3.5))


def _cache_path(niche: str, platform: str) -> str:
    key = "{}__{}".format(niche.lower().strip(), platform.lower().strip())
    h = hashlib.md5(key.encode()).hexdigest()[:12]
    return os.path.join(CACHE_DIR, "{}.json".format(h))


def _load_cache(niche: str, platform: str) -> list:
    """Load cached results if fresh."""
    path = _cache_path(niche, platform)
    if not os.path.exists(path):
        return []
    try:
        age_h = (time.time() - os.path.getmtime(path)) / 3600
        if age_h > CACHE_MAX_AGE_HOURS:
            return []
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, list) and data else []
    except (json.JSONDecodeError, OSError):
        return []


def _save_cache(niche: str, platform: str, data: list) -> None:
    """Save results to cache."""
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        path = _cache_path(niche, platform)
        serializable = [{
            "title": d.get("title", ""), "snippet": d.get("snippet", ""),
            "url": d.get("url", ""), "content": d.get("content", ""),
            "score": d.get("score", 0), "summary": d.get("summary", ""),
        } for d in data]
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(serializable, f, indent=2, ensure_ascii=False)
    except OSError:
        pass


def _detect_niche_category(niche: str) -> str:
    niche_l = niche.lower()
    for cat, kws in NICHE_KEYWORD_MAP.items():
        if any(kw in niche_l for kw in kws):
            return cat
    return ""


def _alignment_keywords(niche: str) -> list:
    cat = _detect_niche_category(niche)
    if cat and cat in NICHE_KEYWORD_MAP:
        return NICHE_KEYWORD_MAP[cat]
    return [w for w in niche.lower().split() if len(w) > 3 and w not in STOPWORDS]


def check_niche_alignment(research_data: list, niche: str) -> dict:
    """Check research result alignment with niche."""
    kws = _alignment_keywords(niche)
    if not kws:
        return {"aligned_count": len(research_data), "total_count": len(research_data),
                "alignment_ratio": 1.0, "drift_detected": False,
                "drift_warning": None, "alignment_keywords": []}

    aligned = 0
    for s in research_data:
        combined = (s.get("title", "") + " " + s.get("snippet", "") + " " + s.get("content", "")).lower()
        if any(kw in combined for kw in kws):
            aligned += 1

    total = len(research_data)
    ratio = aligned / total if total > 0 else 0.0
    drift = ratio < 0.4
    warning = None
    if drift:
        warning = "Drift: only {}/{} results match niche keywords {}.".format(aligned, total, kws[:5])

    return {"aligned_count": aligned, "total_count": total,
            "alignment_ratio": round(ratio, 2), "drift_detected": drift,
            "drift_warning": warning, "alignment_keywords": kws[:5]}


def build_queries(niche: str, platform: str) -> list:
    """Build niche-aligned search queries."""
    cat = _detect_niche_category(niche)
    primary = "{} {} content strategy 2024".format(niche, platform)
    queries = [primary]

    if cat and cat in NICHE_QUERY_ENRICHMENT:
        enrich = random.choice(NICHE_QUERY_ENRICHMENT[cat])
        queries.append("{} {} {}".format(niche, enrich, platform))
    else:
        short = ' '.join(niche.split()[:3])
        queries.append("{} {} tips".format(short, platform))

    return queries


def _fetch_ddg(query: str) -> str:
    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            r = requests.post(DUCKDUCKGO_URL, data={"q": query, "b": ""}, headers=_headers(), timeout=15)
            r.raise_for_status()
            return r.text
        except requests.exceptions.RequestException as e:
            last_err = e
            if attempt < MAX_RETRIES - 1:
                _delay()
    raise RuntimeError("DDG failed: {}".format(last_err))


def _parse_ddg(html: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for link in soup.find_all("a", class_="result__a"):
        title = link.get_text(strip=True)
        if not title:
            continue
        raw = link.get("href", "")
        url = ""
        if "uddg=" in raw:
            m = re.search(r'uddg=([^&]+)', raw)
            if m:
                url = unquote(m.group(1))
        elif raw.startswith("http"):
            url = raw
        if not url or not url.startswith("http") or "duckduckgo.com" in url:
            continue

        snippet = ""
        parent = link.find_parent("div", class_="result") or link.find_parent("div", class_="result__body")
        if parent:
            st = parent.find("a", class_="result__snippet") or parent.find("td", class_="result__snippet")
            if st:
                snippet = st.get_text(strip=True)

        results.append({"title": title, "snippet": snippet, "url": url})
    return results


def _fetch_bing(query: str) -> str:
    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            r = requests.get(BING_URL, params={"q": query}, headers=_headers(), timeout=15)
            r.raise_for_status()
            return r.text
        except requests.exceptions.RequestException as e:
            last_err = e
            if attempt < MAX_RETRIES - 1:
                _delay()
    raise RuntimeError("Bing failed: {}".format(last_err))


def _parse_bing(html: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for item in soup.find_all("li", class_="b_algo"):
        h2 = item.find("h2")
        if not h2:
            continue
        a = h2.find("a")
        if not a:
            continue
        title = a.get_text(strip=True)
        url = a.get("href", "")
        if not url or not url.startswith("http") or "bing.com" in url:
            continue
        snippet = ""
        p = item.find("p")
        if p:
            snippet = p.get_text(strip=True)
        results.append({"title": title, "snippet": snippet, "url": url})
    return results


def _estimate_bing_count(html: str) -> int:
    soup = BeautifulSoup(html, "html.parser")
    tag = soup.find("span", class_="sb_count")
    if tag:
        nums = re.findall(r'[\d,]+', tag.get_text(strip=True))
        if nums:
            try:
                return int(nums[0].replace(',', ''))
            except ValueError:
                pass
    return -1


def _count_domains(results: list, n: int = 5) -> int:
    domains = set()
    for r in results[:n]:
        m = re.search(r'https?://([^/]+)', r.get("url", ""))
        if m:
            domains.add(re.sub(r'^www\.', '', m.group(1).lower()))
    return len(domains)


def _clean_text(raw: str) -> str:
    text = re.sub(r'[ \t]+', ' ', raw)
    noise = [
        r'cookie[s]?\s*(policy|consent|settings)',
        r'accept\s*(all\s*)?cookies', r'privacy\s*policy',
        r'terms\s*(of|and)\s*(service|use)', r'subscribe\s*to',
        r'sign\s*up\s*for', r'©\s*\d{4}', r'all\s*rights\s*reserved',
        r'skip\s*to\s*(main\s*)?content', r'share\s*(this|on)',
        r'leave\s*a\s*(reply|comment)', r'your\s*email.*published',
    ]
    for p in noise:
        text = re.sub(p, '', text, flags=re.IGNORECASE)
    return '\n'.join(l.strip() for l in text.split('\n') if l.strip() and len(l.strip()) >= 40)


def _extract_meta(soup: BeautifulSoup) -> str:
    texts = []
    for attr in [{"name": "description"}, {"property": "og:description"}, {"name": "twitter:description"}]:
        tag = soup.find("meta", attrs=attr)
        if tag and tag.get("content"):
            t = tag["content"].strip()
            if t not in texts:
                texts.append(t)
    return ' '.join(texts)


def extract_page_content(url: str) -> str:
    """Fetch and extract clean text from URL."""
    try:
        r = requests.get(url, headers=_headers(), timeout=10, allow_redirects=True)
        r.raise_for_status()
        ct = r.headers.get('Content-Type', '')
        if 'text/html' not in ct and 'application/xhtml' not in ct:
            return ""

        soup = BeautifulSoup(r.text, "html.parser")
        meta = _extract_meta(soup)

        for tag_name in ['script', 'style', 'nav', 'footer', 'header', 'aside',
                         'form', 'iframe', 'noscript', 'svg', 'button']:
            for tag in soup.find_all(tag_name):
                tag.decompose()

        noise_re = re.compile(r'(sidebar|menu|nav|footer|header|comment|ad[s]?|popup|modal|cookie|banner|widget|social)', re.I)
        for tag in soup.find_all(True, class_=noise_re):
            tag.decompose()
        for tag in soup.find_all(True, id=noise_re):
            tag.decompose()

        parts = [p.get_text(strip=True) for p in soup.find_all('p') if len(p.get_text(strip=True)) > 30]

        if len(parts) < 3:
            for tag in soup.find_all(['article', 'main']):
                t = tag.get_text(separator=' ', strip=True)
                if t and len(t) > 100:
                    parts.append(t)
                    break

        raw = (meta + "\n" if meta else "") + '\n'.join(parts)
        cleaned = _clean_text(raw)

        if len(cleaned) < MIN_CONTENT_LENGTH:
            return ""
        if len(cleaned) > MAX_CONTENT_LENGTH:
            trunc = cleaned[:MAX_CONTENT_LENGTH]
            lp = trunc.rfind('.')
            if lp > MAX_CONTENT_LENGTH * 0.5:
                trunc = trunc[:lp + 1]
            cleaned = trunc

        return cleaned
    except Exception:
        return ""


def summarize_page(title: str, content: str) -> str:
    """Summarize single page via fast LLM model."""
    if not content or len(content) < 100:
        return ""

    prompt = """Summarize in under 300 words. Focus ONLY on:
- Hook style
- CTA style
- Topic focus
- Positioning angle

Title: {title}
Content: {content}

Summary:""".format(title=title, content=content[:800])

    try:
        summary = send_summary_prompt(prompt)
        words = summary.split()
        if len(words) > 300:
            summary = ' '.join(words[:300]) + "..."
        return summary
    except (ConnectionError, RuntimeError):
        return ""


def compute_heuristic_score(title: str, snippet: str) -> int:
    """Score result using engagement heuristics."""
    combined = (title + " " + snippet).lower()
    score = 0
    if re.search(r'\d+', combined):
        score += 2
    if '?' in combined:
        score += 1
    if len(title.split()) < 12:
        score += 1
    for w in POWER_WORDS:
        if w in combined:
            score += 1
    return score


def analyze_keyword_frequency(research_data: list, top_n: int = 15) -> list:
    """Keyword frequency across all content."""
    texts = []
    for s in research_data:
        for k in ["title", "snippet", "content"]:
            if s.get(k):
                texts.append(s[k])
    combined = re.sub(r'[^a-z\s]', ' ', ' '.join(texts).lower())
    words = [w for w in combined.split() if w not in STOPWORDS and len(w) > 2]
    return Counter(words).most_common(top_n)


def check_competitive_intensity(gap_phrase: str, niche: str) -> dict:
    """Check competitive intensity for a gap phrase."""
    query = '"{}" {}'.format(gap_phrase, niche)
    try:
        html = _fetch_bing(query)
        count = _estimate_bing_count(html)
        parsed = _parse_bing(html)
        domains = _count_domains(parsed)

        if count < 0:
            level = "LOW" if len(parsed) < 3 else ("MEDIUM" if domains <= 3 else "HIGH")
        else:
            if count < 10000 and domains <= 3:
                level = "LOW"
            elif count < 100000:
                level = "MEDIUM"
            else:
                level = "HIGH"

        return {"gap": gap_phrase, "intensity_level": level,
                "result_count": count, "unique_domains": domains}
    except RuntimeError:
        return {"gap": gap_phrase, "intensity_level": "UNKNOWN",
                "result_count": -1, "unique_domains": 0}


def _dedup(results: list) -> list:
    seen = set()
    unique = []
    for r in results:
        n = r["url"].rstrip("/").lower()
        if n not in seen:
            seen.add(n)
            unique.append(r)
    return unique


def research_niche(niche: str, platform: str, log: list = None) -> list:
    """
    Full research pipeline: cache, DDG+Bing, extraction, scoring, summarization.

    Args:
        niche: Content niche.
        platform: Target platform.
        log: Optional list to append log messages to.

    Returns:
        List of research dicts with title, snippet, url, content, score, summary.
    """
    if log is None:
        log = []

    # Cache check
    cached = _load_cache(niche, platform)
    if cached:
        log.append("Loaded {} results from cache.".format(len(cached)))
        return cached

    queries = build_queries(niche, platform)
    all_results = []

    # DuckDuckGo
    log.append("DDG search: '{}'".format(queries[0]))
    try:
        html = _fetch_ddg(queries[0])
        parsed = _parse_ddg(html)
        all_results.extend(parsed)
        log.append("DDG returned {} results.".format(len(parsed)))
    except RuntimeError as e:
        log.append("DDG failed: {}".format(e))

    if len(all_results) < 5:
        _delay()
        log.append("DDG enriched: '{}'".format(queries[1]))
        try:
            html = _fetch_ddg(queries[1])
            parsed = _parse_ddg(html)
            all_results.extend(parsed)
            log.append("DDG enriched: {} results.".format(len(parsed)))
        except RuntimeError as e:
            log.append("DDG enriched failed: {}".format(e))

    # Bing fallback
    if len(all_results) < 5:
        _delay()
        log.append("Bing fallback...")
        try:
            html = _fetch_bing(queries[0])
            parsed = _parse_bing(html)
            all_results.extend(parsed)
            log.append("Bing returned {} results.".format(len(parsed)))
        except RuntimeError as e:
            log.append("Bing failed: {}".format(e))

    deduped = _dedup(all_results)
    if not deduped:
        log.append("No results from any search engine.")
        return []

    deduped = deduped[:12]

    # Score
    for r in deduped:
        r["score"] = compute_heuristic_score(r.get("title", ""), r.get("snippet", ""))
        r["content"] = ""
        r["summary"] = ""

    deduped.sort(key=lambda x: x["score"], reverse=True)

    # Extract content
    extract_n = min(CONTENT_EXTRACT_LIMIT, len(deduped))
    content_ok = 0
    for i in range(extract_n):
        content = extract_page_content(deduped[i]["url"])
        if content:
            deduped[i]["content"] = content
            content_ok += 1
        _delay()

    log.append("Extracted content from {}/{} pages.".format(content_ok, extract_n))

    # Summarize
    summary_count = 0
    for r in deduped:
        if r.get("content"):
            s = summarize_page(r.get("title", ""), r["content"])
            r["summary"] = s
            if s:
                summary_count += 1

    log.append("Summarized {} pages.".format(summary_count))

    _save_cache(niche, platform, deduped)
    return deduped