"""
ai_provider.py — Abstract base class for AI content generation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from logger import get_logger

log = get_logger("ai_provider")

# Required keys in the generated JSON
_REQUIRED_KEYS: List[str] = ["title", "summary", "bullets", "skills"]

# Shared prompt template used by every provider
PROMPT_TEMPLATE = """You are a technical recruiter optimizing a GitHub project for LinkedIn internship visibility.

Project Information:
- Repository: {repo_name}
- Project: {project_name}
- GitHub URL: {github_url}
- Description: {description}
- Language: {language}
- Topics: {topics}

README content (excerpt):
{readme_excerpt}

Rules:
- Use strong action verbs
- Quantify impact when possible
- Avoid fluff
- Maximum 5 bullets
- Professional tone
- Output valid JSON only

Return ONLY a JSON object with these keys:
{{
  "title": "Concise, professional project title",
  "summary": "2-3 sentence summary highlighting impact",
  "bullets": ["bullet1", "bullet2", ...],
  "skills": ["skill1", "skill2", ...]
}}

Output valid JSON only. No markdown, no explanation, no code fences."""


class AIProvider(ABC):
    """Interface that every AI provider must implement."""

    @abstractmethod
    def generate_project_content(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate LinkedIn-optimised content for a project.

        Args:
            project_data: Dict with keys ``repo_name``, ``project_name``,
                ``github_url``, ``description``, ``language``, ``topics``,
                ``readme_excerpt``.

        Returns:
            Dict with keys ``title``, ``summary``, ``bullets``, ``skills``.

        Raises:
            ValueError: If the provider returns invalid JSON.
        """
        ...

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    @staticmethod
    def build_prompt(project_data: Dict[str, Any]) -> str:
        """Fill the shared prompt template with project data."""
        return PROMPT_TEMPLATE.format(
            repo_name=project_data.get("repo_name", "N/A"),
            project_name=project_data.get("project_name", "N/A"),
            github_url=project_data.get("github_url", ""),
            description=project_data.get("description", "No description"),
            language=project_data.get("language", "Unknown"),
            topics=", ".join(project_data.get("topics", [])),
            readme_excerpt=project_data.get("readme_excerpt", "Not available")[:2000],
        )

    @staticmethod
    def validate_response(data: Any) -> Dict[str, Any]:
        """
        Validate that *data* is a dict containing all required keys.

        Raises:
            ValueError: On missing keys or wrong type.
        """
        if not isinstance(data, dict):
            raise ValueError(f"Expected dict, got {type(data).__name__}")
        missing = [k for k in _REQUIRED_KEYS if k not in data]
        if missing:
            raise ValueError(f"Missing keys in AI response: {missing}")
        if not isinstance(data["bullets"], list):
            raise ValueError("'bullets' must be a list")
        if not isinstance(data["skills"], list):
            raise ValueError("'skills' must be a list")
        return data
