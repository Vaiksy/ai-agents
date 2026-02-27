"""
LLM Interface module for Local Windows AI Assistant.
Converts natural-language user input into structured JSON via Gemini or OpenAI.
"""

from __future__ import annotations

import json
from typing import Any

from config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    LLM_PROVIDER,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    SYSTEM_PROMPT,
)


class LLMInterface:
    """Thin wrapper around Gemini / OpenAI chat completion APIs."""

    def __init__(self) -> None:
        self.provider = LLM_PROVIDER.lower()
        self._client: Any = None
        self._init_client()

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _init_client(self) -> None:
        if self.provider == "gemini":
            if not GEMINI_API_KEY:
                raise EnvironmentError(
                    "GEMINI_API_KEY is not set. "
                    "Run:  set GEMINI_API_KEY=your_key_here"
                )
            from google import genai

            self._client = genai.Client(api_key=GEMINI_API_KEY)

        elif self.provider == "openai":
            if not OPENAI_API_KEY:
                raise EnvironmentError(
                    "OPENAI_API_KEY is not set. "
                    "Run:  set OPENAI_API_KEY=your_key_here"
                )
            from openai import OpenAI

            self._client = OpenAI(api_key=OPENAI_API_KEY)

        else:
            raise ValueError(
                f"Unsupported LLM_PROVIDER '{self.provider}'. "
                "Use 'gemini' or 'openai'."
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process(self, user_input: str) -> str:
        """
        Send the user's natural-language instruction to the configured LLM
        and return the raw JSON string response.
        """
        if self.provider == "gemini":
            return self._call_gemini(user_input)
        else:
            return self._call_openai(user_input)

    # ------------------------------------------------------------------
    # Provider-specific calls
    # ------------------------------------------------------------------

    def _call_gemini(self, user_input: str) -> str:
        """Call Google Gemini API using the google-genai SDK."""
        from google.genai import types

        response = self._client.models.generate_content(
            model=GEMINI_MODEL,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.0,
                response_mime_type="application/json",
            ),
            contents=user_input,
        )

        return response.text.strip()

    def _call_openai(self, user_input: str) -> str:
        """Call OpenAI Chat Completion API."""
        response = self._client.chat.completions.create(
            model=OPENAI_MODEL,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input},
            ],
        )
        return response.choices[0].message.content.strip()
