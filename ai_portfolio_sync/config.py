"""
config.py — Centralised configuration loaded from .env file.

All settings are exposed as module-level constants for easy import.
Provides a factory function to select the correct AI provider at runtime.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Load .env from the project root (one level above this file)
# ---------------------------------------------------------------------------
_ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(_ENV_PATH)

# ---------------------------------------------------------------------------
# GitHub
# ---------------------------------------------------------------------------
GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
GITHUB_USERNAME: str = os.getenv("GITHUB_USERNAME", "")

# ---------------------------------------------------------------------------
# LinkedIn
# ---------------------------------------------------------------------------
LINKEDIN_EMAIL: str = os.getenv("LINKEDIN_EMAIL", "")
LINKEDIN_PASSWORD: str = os.getenv("LINKEDIN_PASSWORD", "")

# ---------------------------------------------------------------------------
# AI Provider Selection
# ---------------------------------------------------------------------------
USE_CLOUD: bool = os.getenv("USE_CLOUD", "false").lower() == "true"

# Ollama (local — default)
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Cloud (optional)
CLOUD_API_KEY: str = os.getenv("CLOUD_API_KEY", "")
CLOUD_MODEL: str = os.getenv("CLOUD_MODEL", "gpt-4o-mini")
CLOUD_BASE_URL: str = os.getenv("CLOUD_BASE_URL", "https://api.openai.com/v1")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DATA_DIR: Path = Path(__file__).resolve().parent / "data"
CACHE_FILE: Path = DATA_DIR / "project_cache.json"


def get_ai_provider():
    """Factory: return the appropriate AIProvider instance based on config."""
    if USE_CLOUD:
        if not CLOUD_API_KEY:
            print("ERROR: USE_CLOUD=true but CLOUD_API_KEY is not set.")
            sys.exit(1)
        from cloud_provider import CloudProvider
        return CloudProvider(
            api_key=CLOUD_API_KEY,
            model=CLOUD_MODEL,
            base_url=CLOUD_BASE_URL,
        )
    else:
        from ollama_provider import OllamaProvider
        return OllamaProvider(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL,
        )
