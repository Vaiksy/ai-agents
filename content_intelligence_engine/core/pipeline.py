"""
Pipeline Module – v5.2 (Stable)

Orchestrates the full intelligence pipeline.
Returns JSON-serializable data with human report
"""

import time
from typing import Dict, Any, Optional, Callable

from core.research_engine import (
    research_niche, analyze_keyword_frequency,
    check_niche_alignment
)
from core.intelligence_engine import (
    generate_dynamic_subdomains, analyze_structural_saturation,
    detect_gaps, run_competitive_checks, assess_signal,
    extract_insights
)
from core.strategy_engine import generate_strategy
from core.ollama_client import check_ollama_available


def _ensure_json_serializable(obj: Any) -> Any:
    """
    Recursively convert objects to JSON-serializable types.
    
    Args:
        obj: Any Python object.
    
    Returns:
        JSON-serializable version of the object.
    """
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    
    if isinstance(obj, dict):
        return {k: _ensure_json_serializable(v) for k, v in obj.items()}
    
    if isinstance(obj, (list, tuple)):
        return [_ensure_json_serializable(item) for item in obj]
    
    if isinstance(obj, set):
        return list(obj)
    
    # For any other type, try to convert to string
    try:
        return str(obj)
    except Exception:
        return None


def run_pipeline(
    niche: str, 
    platform: str, 
    audience: str, 
    goal: str,
    progress_callback: Optional[Callable[[str], None]] = None
) -> Dict[str, Any]:
    """
    Execute full content intelligence pipeline.
    
    Args:
        niche: Content niche.
        platform: Target platform.
        audience: Target audience description.
        goal: Business goal.
        progress_callback: Optional function to call with progress updates.
    
    Returns:
        Dict with success, human_report, data, and error fields.
    
    Raises:
        ConnectionError: If Ollama is not running.
        RuntimeError: If critical pipeline step fails.
        ValueError: If inputs are invalid.
    """
    def _progress(message: str):
        """Send progress update if callback provided."""
        if progress_callback:
            progress_callback(message)
    
    # Validate inputs
    for name, val in [("niche", niche), ("platform", platform),
                      ("audience", audience), ("goal", goal)]:
        if not val or not val.strip():
            raise ValueError("{} cannot be empty.".format(name))
    
    start_time = time.time()
    log = []
    
    result = {
        "client_profile": {
            "niche": niche,
            "platform": platform,
            "target_audience": audience,
            "business_goal": goal,
        },
        "pipeline_log": log,
        "signal_strength": {},
        "niche_alignment": {},
        "keyword_analysis": [],
        "saturation_report": {},
        "semantic_gap_analysis": [],
        "competitive_intensity": [],
        "content_intelligence": "",
        "content_strategy": {},
        "meta": {},
    }
    
    try:
        # Step 0: Check Ollama
        _progress("Checking system...")
        log.append("Checking Ollama availability...")
        
        if not check_ollama_available():
            raise ConnectionError(
                "Ollama is not running or qwen2.5-coder:7b is not installed. "
                "Start Ollama with: ollama serve"
            )
        
        log.append("Ollama running with qwen2.5-coder:7b")
        
        # Step 1: Research
        _progress("Researching your market...")
        log.append("Step 1: Research...")
        research_data = research_niche(niche, platform, log=log)
        
        if not research_data:
            raise RuntimeError("No research data collected. Try a different niche.")
        
        log.append("Research complete: {} results.".format(len(research_data)))
        
        # Step 2: Niche alignment
        _progress("Analyzing market alignment...")
        log.append("Step 2: Niche alignment check...")
        alignment = check_niche_alignment(research_data, niche)
        result["niche_alignment"] = alignment
        if alignment.get("drift_detected"):
            log.append("WARNING: {}".format(alignment.get("drift_warning", "")))
        
        # Step 3: Keywords
        _progress("Extracting key themes...")
        log.append("Step 3: Keyword analysis...")
        keywords = analyze_keyword_frequency(research_data)
        result["keyword_analysis"] = [{"word": w, "count": c} for w, c in keywords]
        log.append("Found {} keywords.".format(len(keywords)))
        
        # Step 4: Signal strength
        _progress("Assessing data quality...")
        log.append("Step 4: Signal assessment...")
        signal = assess_signal(research_data)
        result["signal_strength"] = signal
        log.append("Confidence: {}".format(signal.get("confidence", "UNKNOWN")))
        
        # Step 5: Saturation
        _progress("Analyzing competition...")
        log.append("Step 5: Saturation analysis...")
        saturation = analyze_structural_saturation(research_data)
        result["saturation_report"] = saturation
        log.append("Format: {} | Saturated: {}".format(
            saturation.get("dominant_format", "Unknown"), 
            saturation.get("is_saturated", False)
        ))
        
        # Step 6: Dynamic subdomains
        _progress("Identifying content opportunities...")
        log.append("Step 6: Dynamic subdomain generation...")
        subdomains = generate_dynamic_subdomains(niche, log=log)
        result["meta"]["subdomains"] = subdomains
        
        # Step 7: Semantic gap detection
        _progress("Finding market gaps...")
        log.append("Step 7: Gap detection...")
        gap_results = detect_gaps(research_data, subdomains, log=log)
        result["semantic_gap_analysis"] = gap_results
        gap_count = sum(1 for g in gap_results if g.get("is_gap"))
        log.append("Gaps found: {}/{}".format(gap_count, len(gap_results)))
        
        # Step 8: Competitive intensity
        _progress("Checking competitive intensity...")
        log.append("Step 8: Competitive intensity checks...")
        competitive = run_competitive_checks(gap_results, niche, log=log)
        result["competitive_intensity"] = competitive
        
        # Step 9: Intelligence extraction
        _progress("Extracting market insights...")
        log.append("Step 9: Intelligence extraction...")
        insights = extract_insights(research_data, keywords, log=log)
        result["content_intelligence"] = insights
        
        # Step 10: Strategy generation
        _progress("Generating your strategy...")
        log.append("Step 10: Strategy generation (2-pass)...")
        strategy = generate_strategy(
            niche=niche, platform=platform,
            target_audience=audience, business_goal=goal,
            insights=insights, keywords=keywords, signal=signal,
            saturation=saturation, gap_results=gap_results,
            competitive=competitive, log=log
        )
        
        # Clean strategy output
        strategy_clean = {}
        for key, val in strategy.items():
            if not key.startswith("_"):
                strategy_clean[key] = val
        
        result["content_strategy"] = strategy_clean
        
        # Meta
        elapsed = round(time.time() - start_time, 1)
        result["meta"]["elapsed_seconds"] = elapsed
        result["meta"]["research_count"] = len(research_data)
        result["meta"]["pages_with_content"] = signal.get("urls_with_content", 0)
        result["meta"]["pages_summarized"] = signal.get("urls_with_summaries", 0)
        result["meta"]["gaps_found"] = gap_count
        result["meta"]["total_subdomains"] = len(subdomains)
        
        # Include research samples(cleaned)
        result["research_samples"] = [{
            "title": r.get("title", ""),
            "snippet": r.get("snippet", "")[:200],
            "url": r.get("url", ""),
            "score": r.get("score", 0),
            "has_content": bool(r.get("content", "").strip()),
            "has_summary": bool(r.get("summary", "").strip()),
        } for r in research_data]
        
        log.append("Pipeline complete in {}s.".format(elapsed))
        
        _progress("Finalizing report...")
        
        # Ensure everything is JSON serializable
        result = _ensure_json_serializable(result)
        
        return result
        
    except Exception as e:
        log.append("ERROR: {}".format(str(e)))
        result["meta"]["error"] = str(e)
        result["meta"]["elapsed_seconds"] = round(time.time() - start_time, 1)
        raise

