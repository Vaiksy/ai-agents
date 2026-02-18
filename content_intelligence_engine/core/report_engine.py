"""
Report Engine – v1.0

Converts technical pipeline output into clean, professional English reports.
Designed for non-technical users and decision-makers.
"""

from typing import Dict, List


def generate_human_report(pipeline_output: dict) -> str:
    """
    Convert technical pipeline output into a clean, readable English report.
    
    Args:
        pipeline_output: Raw pipeline data structure.
    
    Returns:
        Formatted English report as string.
    """
    try:
        report_sections = []
        
        # Header
        profile = pipeline_output.get("client_profile", {})
        report_sections.append(_generate_header(profile))
        
        # Executive Summary
        signal = pipeline_output.get("signal_strength", {})
        meta = pipeline_output.get("meta", {})
        report_sections.append(_generate_executive_summary(signal, meta))
        
        # Market Overview
        saturation = pipeline_output.get("saturation_report", {})
        keywords = pipeline_output.get("keyword_analysis", [])
        report_sections.append(_generate_market_overview(saturation, keywords))
        
        # Competitive Landscape
        gaps = pipeline_output.get("semantic_gap_analysis", [])
        competitive = pipeline_output.get("competitive_intensity", [])
        report_sections.append(_generate_competitive_landscape(gaps, competitive))
        
        # Opportunity Gaps
        report_sections.append(_generate_opportunity_gaps(gaps, competitive))
        
        # Strategic Positioning
        strategy = pipeline_output.get("content_strategy", {})
        report_sections.append(_generate_strategic_positioning(strategy, profile))
        
        # Content Angles
        report_sections.append(_generate_content_angles(strategy))
        
        # Action Plan
        report_sections.append(_generate_action_plan(strategy))
        
        # Join all sections
        return "\n\n".join(report_sections)
        
    except Exception as e:
        return _generate_fallback_report(pipeline_output, str(e))


def _generate_header(profile: dict) -> str:
    """Generate report header."""
    niche = profile.get("niche", "Unknown")
    platform = profile.get("platform", "Unknown")
    audience = profile.get("target_audience", "Unknown")
    
    return f"""═══════════════════════════════════════════════════════════════
CONTENT STRATEGY REPORT
═══════════════════════════════════════════════════════════════

Topic Focus: {niche}
Platform: {platform}
Target Audience: {audience}

Generated: AI-Powered Market Intelligence Analysis
"""


def _generate_executive_summary(signal: dict, meta: dict) -> str:
    """Generate executive summary."""
    confidence = signal.get("confidence", "UNKNOWN")
    pages_analyzed = signal.get("urls_with_content", 0)
    elapsed = meta.get("elapsed_seconds", 0)
    
    confidence_text = {
        "HIGH": "excellent data quality",
        "MEDIUM": "moderate data quality",
        "LOW": "limited data available"
    }.get(confidence, "varying data quality")
    
    return f"""─────────────────────────────────────────────────────────────
EXECUTIVE SUMMARY
─────────────────────────────────────────────────────────────

We analyzed {pages_analyzed} leading content pieces in your market to identify 
strategic opportunities and competitive positioning.

Analysis Quality: Based on {confidence_text}, we have {confidence.lower()} 
confidence in these findings.

Key Finding: Our research reveals specific content gaps and audience needs 
that are currently underserved in your market.
"""


def _generate_market_overview(saturation: dict, keywords: list) -> str:
    """Generate market overview section."""
    dominant = saturation.get("dominant_format", "Mixed formats")
    is_saturated = saturation.get("is_saturated", False)
    list_pct = saturation.get("list_percentage", 0)
    
    # Get top keywords
    top_kw = keywords[:5] if keywords else []
    kw_text = ", ".join([f"'{k['word']}'" for k in top_kw]) if top_kw else "various topics"
    
    saturation_insight = ""
    if is_saturated:
        saturation_insight = f"""
⚠️  MARKET SATURATION ALERT
The market is oversaturated with {dominant.lower()} ({list_pct}% of content).
Opportunity: Stand out by using different content formats and angles.
"""
    else:
        saturation_insight = f"""
✓  HEALTHY MARKET DIVERSITY
The market shows {dominant.lower()}, indicating room for innovation.
"""
    
    return f"""─────────────────────────────────────────────────────────────
MARKET OVERVIEW
─────────────────────────────────────────────────────────────

Current Market Dynamics:
{saturation_insight}

Most Discussed Topics:
{kw_text}

What This Means:
The market is actively discussing these themes, but there are still 
untapped angles and underserved audience needs you can capture.
"""


def _generate_competitive_landscape(gaps: list, competitive: list) -> str:
    """Generate competitive landscape section."""
    total_gaps = len([g for g in gaps if g.get("is_gap")])
    
    # Find low competition opportunities
    low_comp = [c for c in competitive if c.get("intensity_level") == "LOW"]
    
    comp_text = ""
    if low_comp:
        low_topics = ", ".join([f"'{c.get('gap', '')}'" for c in low_comp[:3]])
        comp_text = f"""
🎯 LOW COMPETITION AREAS IDENTIFIED:
{low_topics}

These topics have minimal existing content, giving you a first-mover advantage.
"""
    else:
        comp_text = """
The market is moderately competitive. Strategic positioning will be key.
"""
    
    return f"""─────────────────────────────────────────────────────────────
COMPETITIVE LANDSCAPE
─────────────────────────────────────────────────────────────

Market Gaps Identified: {total_gaps} distinct opportunities
{comp_text}

Strategic Advantage:
By focusing on these underserved areas, you can establish authority 
before competitors recognize these opportunities.
"""


def _generate_opportunity_gaps(gaps: list, competitive: list) -> str:
    """Generate opportunity gaps section."""
    gap_items = [g for g in gaps if g.get("is_gap")][:8]
    
    if not gap_items:
        return """─────────────────────────────────────────────────────────────
OPPORTUNITY GAPS
─────────────────────────────────────────────────────────────

The market is well-covered. Focus on differentiation through:
• Unique personal experiences and case studies
• Contrarian perspectives on existing topics
• Deeper analysis than competitors provide
"""
    
    # Build competitive intensity map
    comp_map = {c.get("gap", ""): c.get("intensity_level", "UNKNOWN") 
                for c in competitive}
    
    gap_lines = []
    for i, gap in enumerate(gap_items, 1):
        subdomain = gap.get("subdomain", "")
        intensity = comp_map.get(subdomain, "MEDIUM")
        
        indicator = {
            "LOW": "🟢 Low Competition",
            "MEDIUM": "🟡 Moderate Competition",
            "HIGH": "🔴 High Competition",
            "UNKNOWN": "⚪ Competition Unknown"
        }.get(intensity, "⚪")
        
        gap_lines.append(f"{i}. {subdomain.title()} — {indicator}")
    
    gaps_text = "\n".join(gap_lines)
    
    return f"""─────────────────────────────────────────────────────────────
TOP OPPORTUNITY GAPS
─────────────────────────────────────────────────────────────

These topics are underserved in current market content:

{gaps_text}

Recommendation:
Start with low-competition gaps (🟢) to build initial traction, then 
expand into moderate-competition areas (🟡) as you establish authority.
"""


def _generate_strategic_positioning(strategy: dict, profile: dict) -> str:
    """Generate strategic positioning section."""
    positioning = strategy.get("positioning", "").strip()
    pillars = strategy.get("pillars", "").strip()
    
    if not positioning:
        goal = profile.get("business_goal", "build authority")
        positioning = f"""Position yourself as the go-to expert who helps your audience 
{goal} through practical, actionable insights."""
    
    # Extract pillars if available
    pillar_lines = []
    if pillars:
        # Try to parse pillars
        for line in pillars.split("\n"):
            line = line.strip()
            if line and len(line) > 10 and not line.startswith("#"):
                pillar_lines.append("• " + line.lstrip("•-*123456789. "))
    
    if not pillar_lines:
        pillar_lines = [
            "• Share unique insights from your expertise",
            "• Provide actionable, step-by-step guidance",
            "• Address common pain points directly",
        ]
    
    pillars_text = "\n".join(pillar_lines[:5])
    
    return f"""─────────────────────────────────────────────────────────────
STRATEGIC POSITIONING
─────────────────────────────────────────────────────────────

Your Unique Positioning:
{positioning}

Core Content Pillars:
{pillars_text}

This positioning differentiates you from competitors while addressing 
real audience needs identified in our research.
"""


def _generate_content_angles(strategy: dict) -> str:
    """Generate content angles section."""
    hooks = strategy.get("hooks", "").strip()
    
    # Try to extract hooks
    hook_lines = []
    if hooks:
        for line in hooks.split("\n"):
            line = line.strip()
            if line and len(line) > 15 and not line.startswith("#"):
                cleaned = line.lstrip("•-*123456789. \"'")
                if cleaned:
                    hook_lines.append(cleaned)
    
    if len(hook_lines) < 5:
        hook_lines = [
            "The surprising truth about [topic] that nobody talks about",
            "Why most advice on [topic] is wrong (and what works instead)",
            "The contrarian approach to [topic] that's getting results",
            "[Number] unconventional strategies for [outcome]",
            "What I learned from [experience] about [topic]",
        ]
    
    angles_text = "\n\n".join([f"{i}. {hook}" 
                               for i, hook in enumerate(hook_lines[:5], 1)])
    
    return f"""─────────────────────────────────────────────────────────────
5 POWERFUL CONTENT ANGLES
─────────────────────────────────────────────────────────────

These angles are designed to stand out in your market:

{angles_text}

Usage: Start each piece of content with one of these angles to immediately 
capture attention and differentiate from standard content.
"""


def _generate_action_plan(strategy: dict) -> str:
    """Generate 7-day action plan."""
    calendar = strategy.get("calendar", "").strip()
    
    # Try to extract calendar items
    days = []
    if calendar:
        current_day = None
        for line in calendar.split("\n"):
            line = line.strip()
            if any(day in line.lower() for day in ["monday", "tuesday", "wednesday", 
                                                     "thursday", "friday", "saturday", "sunday"]):
                if current_day:
                    days.append(current_day)
                current_day = line
            elif current_day and line and not line.startswith("#"):
                current_day += "\n  " + line.lstrip("•-* ")
        if current_day:
            days.append(current_day)
    
    if len(days) < 7:
        days = [
            "Monday: Research and outline your first piece using gap analysis above",
            "Tuesday: Write draft focusing on one of the 5 content angles",
            "Wednesday: Edit and refine - add personal insights and examples",
            "Thursday: Create supporting visuals or data points",
            "Friday: Publish and promote across relevant channels",
            "Saturday: Engage with audience comments and feedback",
            "Sunday: Analyze performance and plan next week's content",
        ]
    
    plan_text = "\n\n".join(days[:7])
    
    return f"""─────────────────────────────────────────────────────────────
7-DAY ACTION PLAN
─────────────────────────────────────────────────────────────

{plan_text}

Next Steps:
1. Review the opportunity gaps and select your starting topic
2. Use one of the content angles to create your hook
3. Follow the 7-day plan to maintain consistent momentum
4. Track engagement and double down on what resonates

Remember: Consistency beats perfection. Ship your first piece this week.

═══════════════════════════════════════════════════════════════
END OF REPORT
═══════════════════════════════════════════════════════════════
"""


def _generate_fallback_report(pipeline_output: dict, error: str) -> str:
    """Generate fallback report if normal generation fails."""
    profile = pipeline_output.get("client_profile", {})
    niche = profile.get("niche", "your topic")
    platform = profile.get("platform", "your platform")
    
    return f"""═══════════════════════════════════════════════════════════════
CONTENT STRATEGY REPORT
═══════════════════════════════════════════════════════════════

Topic: {niche}
Platform: {platform}

─────────────────────────────────────────────────────────────
ANALYSIS SUMMARY
─────────────────────────────────────────────────────────────

We've completed the market analysis for your content strategy.

While we encountered some technical issues generating the full formatted 
report, the raw analysis data is available in the technical view below.

KEY RECOMMENDATIONS:

1. Research Your Market
   • Study the top 10 content pieces in your niche
   • Identify what formats and angles are working
   • Note what's missing or underserved

2. Define Your Unique Angle
   • What unique perspective can you bring?
   • What experiences or insights do you have that others don't?
   • How can you serve your audience better than existing content?

3. Create Consistently
   • Commit to a publishing schedule (e.g., 2x/week)
   • Focus on one content pillar to start
   • Build momentum before expanding

4. Engage and Iterate
   • Monitor what resonates with your audience
   • Double down on successful topics
   • Adjust based on feedback

For detailed technical data, expand the "Technical View" section below.

═══════════════════════════════════════════════════════════════

Note: Report generation encountered an issue: {error}
The technical data below contains the complete analysis.
"""
