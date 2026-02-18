"""
Ollama LLM Client – v5.2 (Stable)

All models use qwen2.5-coder:7b
Embeddings completely disabled
Robust connection checking
"""

import json
import re
import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"

# SINGLE MODEL FOR ALL OPERATIONS
MODEL = "qwen2.5-coder:7b"

# Embeddings permanently disabled
EMBEDDINGS_ENABLED = False


def check_ollama_available() -> bool:
    """
    Check if Ollama is running and qwen2.5-coder:7b is available.
    
    Returns:
        bool: True if Ollama is running with qwen model, False otherwise.
    """
    try:
        response = requests.get(OLLAMA_TAGS_URL, timeout=5)
        if response.status_code != 200:
            return False
        
        data = response.json()
        models = [m.get("name", "") for m in data.get("models", [])]
        
        # Check for qwen2.5-coder:7b (or qwen2.5-coder variants)
        for model in models:
            if "qwen2.5-coder:7b" in model or "qwen2.5-coder" in model:
                return True
        
        return False
        
    except Exception:
        return False


def send_prompt(prompt: str, temperature: float = 0.5, 
                max_retries_on_overflow: int = 1) -> str:
    """
    Send prompt to Ollama with context overflow recovery.
    
    Args:
        prompt: Text prompt.
        temperature: Randomness control (0.0-1.0).
        max_retries_on_overflow: Retry count after trimming.
    
    Returns:
        Generated text string.
    
    Raises:
        ConnectionError: Ollama unreachable.
        RuntimeError: Generation failure.
    """
    current_prompt = prompt
    attempts = 0
    
    while attempts <= max_retries_on_overflow:
        payload = {
            "model": MODEL,
            "prompt": current_prompt,
            "temperature": temperature,
            "stream": False,
            "options": {"num_ctx": 2048}
        }
        
        try:
            response = requests.post(
                OLLAMA_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=None
            )
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                "Ollama not running. Start with: ollama serve"
            )
        except requests.exceptions.RequestException as exc:
            raise RuntimeError("Ollama request failed: {}".format(exc))
        
        if response.status_code != 200:
            error_text = response.text[:500].lower()
            if any(kw in error_text for kw in ["context", "too long", "token"]):
                if attempts < max_retries_on_overflow:
                    target = int(len(current_prompt) * 0.7)
                    current_prompt = _trim_prompt(current_prompt, target)
                    attempts += 1
                    continue
                raise RuntimeError("Context limit exceeded after trimming.")
            raise RuntimeError("Ollama error {}: {}".format(
                response.status_code, response.text[:300]
            ))
        
        try:
            data = response.json()
        except json.JSONDecodeError:
            raise RuntimeError("Invalid JSON from Ollama.")
        
        if "response" not in data:
            error_msg = data.get("error", "")
            if error_msg and any(kw in error_msg.lower() for kw in ["context", "token"]):
                if attempts < max_retries_on_overflow:
                    target = int(len(current_prompt) * 0.7)
                    current_prompt = _trim_prompt(current_prompt, target)
                    attempts += 1
                    continue
            raise RuntimeError("Unexpected response. Error: {}".format(error_msg))
        
        return data["response"].strip()
    
    raise RuntimeError("All retry attempts exhausted.")


def _trim_prompt(prompt: str, target_length: int) -> str:
    """Trim prompt preserving instruction header and footer."""
    if len(prompt) <= target_length:
        return prompt
    
    markers_start = ["=== RESEARCH", "--- Sample", "INTELLIGENCE:", "SAMPLES:"]
    markers_end = ["=== END", "Based STRICTLY", "Analyze ONLY", "GENERATE:"]
    
    content_start = len(prompt) // 4
    for m in markers_start:
        idx = prompt.find(m)
        if idx != -1:
            content_start = idx
            break
    
    content_end = len(prompt) * 3 // 4
    for m in markers_end:
        idx = prompt.rfind(m)
        if idx != -1:
            content_end = idx
            break
    
    header = prompt[:content_start]
    footer = prompt[content_end:]
    content = prompt[content_start:content_end]
    
    available = target_length - len(header) - len(footer) - 50
    if available > 0 and len(content) > available:
        content = content[:available] + "\n[... trimmed ...]\n"
    
    return header + content + footer


def send_prompt_for_list(prompt: str, temperature: float = 0.3) -> list:
    """
    Send prompt and parse response as a list of items.
    
    Args:
        prompt: Prompt expecting list output.
        temperature: Randomness.
    
    Returns:
        List of parsed strings.
    """
    raw = send_prompt(prompt, temperature=temperature)
    items = []
    for line in raw.split('\n'):
        line = line.strip()
        if not line:
            continue
        cleaned = re.sub(r'^[\d]+[.\)]\s*', '', line)
        cleaned = re.sub(r'^[-*•]\s*', '', cleaned).strip()
        if cleaned and 3 < len(cleaned) < 200:
            items.append(cleaned)
    return items


def send_summary_prompt(prompt: str, temperature: float = 0.2) -> str:
    """
    Send summarization prompt.
    
    Args:
        prompt: Summarization prompt.
        temperature: Low for factual summaries.
    
    Returns:
        Summary text.
    """
    return send_prompt(prompt, temperature=temperature)


def get_embedding(text: str) -> list:
    """
    DISABLED - Embeddings not available.
    
    Raises:
        RuntimeError: Always. Embeddings are disabled.
    """
    raise RuntimeError(
        "Embeddings are DISABLED. To enable: ollama pull nomic-embed-text"
    )
