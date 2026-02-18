"""
Strategy Engine – v5.2 (Compatible with unified model)

Differentiated strategy with saturation avoidance, gap targeting,
competitive awareness, and 2-pass self-refinement. Pure data return.
"""

from core.ollama_client import send_prompt, MODEL
import re


def generate_strategy(
    niche: str, platform: str, target_audience: str, business_goal: str,
    insights: str, keywords: list = None, signal: dict = None,
    saturation: dict = None, gap_results: list = None,
    competitive: list = None, log: list = None
) -> dict:
    """
    Generate differentiated content strategy with 2-pass refinement.

    Returns:
        Dict with strategy sections and raw text.
    """
    if log is None:
        log = []
    keywords = keywords or []
    signal = signal or {"confidence": "UNKNOWN"}
    saturation = saturation or {"is_saturated": False, "list_percentage": 0}
    gap_results = gap_results or []
    competitive = competitive or []

    # Pass 1
    log.append("Strategy Pass 1: Generating...")
    p1 = _build_main_prompt(niche, platform, target_audience, business_goal,
                             insights, keywords, signal, saturation,
                             gap_results, competitive)

    raw = send_prompt(p1, temperature=0.6)
    if not raw or len(raw.strip()) < 100:
        raise RuntimeError("Strategy Pass 1 insufficient output.")
    log.append("Pass 1: {} chars.".format(len(raw)))

    # Pass 2: Refine
    log.append("Strategy Pass 2: Critique and refine...")
    p2 = _build_refine_prompt(raw, niche, platform, saturation, gap_results)

    try:
        refined = send_prompt(p2, temperature=0.4)
        if refined and len(refined.strip()) > len(raw) * 0.5:
            log.append("Pass 2: {} chars (refined).".format(len(refined)))
            final = refined
        else:
            log.append("Pass 2 too short. Using Pass 1.")
            final = raw
    except (ConnectionError, RuntimeError):
        log.append("Pass 2 failed. Using Pass 1.")
        final = raw

    sections = _split_sections(final)
    sections["_raw"] = final
    sections["_pass1"] = raw

    return sections


def _build_main_prompt(niche, platform, audience, goal, insights,
                        keywords, signal, saturation, gaps, competitive):
    kw_text = ""
    if keywords:
        kw_text = "Keywords: " + ", ".join("'{}' ({}x)".format(w, c) for w, c in keywords[:10])

    sat_inst = ""
    if saturation.get("is_saturated"):
        pct = max(saturation.get("list_percentage", 0), saturation.get("content_list_percentage", 0))
        sat_inst = "\nSATURATION: {}% list-based. AVOID listicle format entirely.\n".format(pct)

    gap_list = [g for g in gaps if g.get("is_gap")]
    gap_inst = ""
    if gap_list:
        names = ", ".join(g["subdomain"] for g in gap_list[:5])
        gap_inst = "\nMARKET GAPS: {}\n".format(names)
        low = [c for c in competitive if c.get("intensity_level") == "LOW"]
        if low:
            gap_inst += "LOW COMPETITION: {}\n".format(", ".join(c["gap"] for c in low[:3]))

    niche_inst = ""
    if any(w in niche.lower() for w in ["founder", "startup", "entrepreneur"]):
        niche_inst = "\nFOUNDER ALIGNMENT: Execution-oriented language. 1 operational pillar.\n"

    return """Senior content strategist. Differentiated plan.

RULES:
1. NO fake statistics. 2. NO cliches. 3. NO filler.
4. Be SPECIFIC. 5. Each script: 1 contrarian insight.
6. Short sentences. {platform} style.
7. Include: 1 bold positioning, 1 tension hook, 1 anti-consensus statement.
{sat}{gap}{niche_inst}

CLIENT: {niche} | {platform} | {audience} | Goal: {goal}
Confidence: {conf}
{kw}

INTELLIGENCE:
{insights}

GENERATE:

## 1. STRATEGIC POSITIONING STATEMENT
3-5 sentences. What brand IS and IS NOT. Bold differentiator.

## 2. CONTENT PILLARS
3-5 pillars targeting market gaps. Specific topics.

## 3. OPTIMIZED HOOKS
10 hooks <15 words. 2 tension. 1 anti-consensus. No listicle if saturated.

## 4. SHORT-FORM CONTENT SCRIPTS
5 scripts: Hook + contrarian + body (3-5 sentences) + CTA. No fake stats.

## 5. CTA VARIATIONS
6 CTAs for "{goal}". Triggers: urgency, social proof, curiosity, value, identity, scarcity.

## 6. 7-DAY CONTENT CALENDAR
Mon-Sun: Day, Type, Pillar, Topic, Hook, CTA, Time.""".format(
        niche=niche, platform=platform, audience=audience, goal=goal,
        insights=insights, kw=kw_text, conf=signal.get("confidence", "UNKNOWN"),
        sat=sat_inst, gap=gap_inst, niche_inst=niche_inst,
    )


def _build_refine_prompt(strategy, niche, platform, saturation, gaps):
    checks = ""
    if saturation.get("is_saturated"):
        checks += "\n- Uses listicle despite saturation?"
    gap_list = [g for g in gaps if g.get("is_gap")]
    if gap_list:
        checks += "\n- Targets gaps: {}?".format(", ".join(g["subdomain"] for g in gap_list[:5]))
    if any(w in niche.lower() for w in ["founder", "startup"]):
        checks += "\n- Drifts from founder context?"

    return """Brutal editor. Critique and rewrite.

CHECK:
1. Generic → specific. 2. Weak differentiation → strengthen.
3. Niche drift → refocus. 4. Saturated angles → replace.
5. Cliches → plain. 6. Fake stats → remove. 7. Filler → cut.{checks}

Niche: {niche} | Platform: {platform}

STRATEGY:
{strategy}

OUTPUT improved version. Same structure. Sharper.""".format(
        niche=niche, platform=platform, strategy=strategy, checks=checks,
    )


def _split_sections(raw: str) -> dict:
    patterns = [
        ("positioning", r"(?:##?\s*1\.?\s*)?STRATEGIC POSITIONING"),
        ("pillars", r"(?:##?\s*2\.?\s*)?CONTENT PILLARS"),
        ("hooks", r"(?:##?\s*3\.?\s*)?OPTIMIZED HOOKS"),
        ("scripts", r"(?:##?\s*4\.?\s*)?SHORT-FORM CONTENT SCRIPTS"),
        ("ctas", r"(?:##?\s*5\.?\s*)?CTA VARIATIONS"),
        ("calendar", r"(?:##?\s*6\.?\s*)?7-DAY CONTENT CALENDAR"),
    ]

    boundaries = []
    for key, pat in patterns:
        m = re.search(pat, raw, re.IGNORECASE)
        if m:
            boundaries.append((m.start(), key, m.end()))

    if len(boundaries) < 3:
        return {"full_strategy": raw}

    boundaries.sort(key=lambda x: x[0])
    sections = {}
    for i, (start, key, hend) in enumerate(boundaries):
        end = boundaries[i+1][0] if i+1 < len(boundaries) else len(raw)
        sections[key] = raw[hend:end].strip().lstrip(":-").strip()

    return sections
