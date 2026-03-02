"""
cloud_provider.py — Optional cloud LLM provider via OpenAI-compatible API.

Activated only when ``USE_CLOUD=true`` and ``CLOUD_API_KEY`` is set.
"""

from __future__ import annotations

import json
from typing import Any, Dict

from openai import OpenAI

from ai_provider import AIProvider
from logger import get_logger

log = get_logger("cloud")


class CloudProvider(AIProvider):
    """AI provider backed by an OpenAI-compatible cloud API."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        base_url: str = "https://api.openai.com/v1",
    ) -> None:
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = model
        log.info("Cloud provider initialised (model=%s, base_url=%s)", model, base_url)

    # ------------------------------------------------------------------
    # AIProvider interface
    # ------------------------------------------------------------------

    def generate_project_content(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate content via cloud LLM."""
        prompt = self.build_prompt(project_data)

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a technical recruiter writing LinkedIn project entries. "
                            "Always respond with valid JSON only — no markdown, no explanation."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=1024,
            )
            raw = response.choices[0].message.content or ""
            parsed = json.loads(raw)
            return self.validate_response(parsed)
        except json.JSONDecodeError as exc:
            log.error("Cloud LLM returned invalid JSON: %s", exc)
            raise ValueError(f"Cloud LLM returned invalid JSON: {exc}") from exc
        except Exception as exc:
            log.error("Cloud LLM request failed: %s", exc)
            raise
