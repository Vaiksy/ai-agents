"""
ollama_provider.py — Local LLM provider via Ollama REST API.

Sends POST requests to ``http://localhost:11434/api/generate``.
Retries up to 2 times on invalid JSON responses.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict

import requests

from ai_provider import AIProvider
from logger import get_logger

log = get_logger("ollama")

_MAX_RETRIES = 2


class OllamaProvider(AIProvider):
    """AI provider backed by a locally-running Ollama instance."""

    def __init__(self, model: str = "llama3", base_url: str = "http://localhost:11434") -> None:
        self._model = model
        self._base_url = base_url.rstrip("/")
        log.info("Ollama provider initialised (model=%s, url=%s)", model, self._base_url)

    # ------------------------------------------------------------------
    # AIProvider interface
    # ------------------------------------------------------------------

    def generate_project_content(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate content via Ollama with retry logic."""
        prompt = self.build_prompt(project_data)

        last_error: Exception | None = None
        for attempt in range(1, _MAX_RETRIES + 2):  # 1-indexed, up to 3 attempts
            log.debug("Ollama attempt %d/%d", attempt, _MAX_RETRIES + 1)
            try:
                raw = self._call_ollama(prompt)
                parsed = self._extract_json(raw)
                return self.validate_response(parsed)
            except (ValueError, json.JSONDecodeError, requests.RequestException) as exc:
                last_error = exc
                log.warning("Attempt %d failed: %s", attempt, exc)

        raise ValueError(f"Ollama failed after {_MAX_RETRIES + 1} attempts: {last_error}")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _call_ollama(self, prompt: str) -> str:
        """POST to /api/generate and return the concatenated response."""
        url = f"{self._base_url}/api/generate"
        payload = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.3},
        }
        resp = requests.post(url, json=payload, timeout=120)
        resp.raise_for_status()
        body = resp.json()
        return body.get("response", "")

    @staticmethod
    def _extract_json(text: str) -> Dict[str, Any]:
        """
        Extract a JSON object from *text*, stripping markdown fences
        and surrounding prose if present.
        """
        # Remove markdown code fences
        cleaned = re.sub(r"```(?:json)?", "", text).strip()
        cleaned = cleaned.strip("`").strip()

        # Try to locate the first { ... } block
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("No JSON object found in Ollama response")

        json_str = cleaned[start : end + 1]
        return json.loads(json_str)
