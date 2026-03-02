"""
main.py — CLI entry point for AI Portfolio Sync.

Usage:
    python main.py                   # Scan all repos
    python main.py --repo my_repo    # Scan a specific repo
    python main.py --dry-run         # Generate content without LinkedIn
    python main.py --debug           # Verbose logging
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Dict, Any

import config
from cache_manager import CacheManager
from github_service import GitHubService
from linkedin_automation import LinkedInAutomation
from logger import setup_logger, get_logger
from project_detector import ProjectDetector
from project_parser import ProjectParser


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="ai-portfolio-sync",
        description="Sync GitHub projects to LinkedIn using AI-generated content.",
    )
    parser.add_argument(
        "--repo",
        type=str,
        default=None,
        help="Process only this repository name.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate content and print it — skip LinkedIn autofill.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable verbose debug logging.",
    )
    return parser.parse_args()


def main() -> None:
    """Orchestrate the full pipeline: GitHub → Detect → Parse → LinkedIn."""
    args = parse_args()
    setup_logger(debug=args.debug)
    log = get_logger("main")

    log.info("=" * 60)
    log.info("  AI Portfolio Sync — starting")
    log.info("=" * 60)

    # ------------------------------------------------------------------
    # Pre-flight checks
    # ------------------------------------------------------------------
    if not config.GITHUB_TOKEN:
        log.error("GITHUB_TOKEN is not set in .env — aborting.")
        sys.exit(1)
    if not config.GITHUB_USERNAME:
        log.error("GITHUB_USERNAME is not set in .env — aborting.")
        sys.exit(1)
    if not args.dry_run and (not config.LINKEDIN_EMAIL or not config.LINKEDIN_PASSWORD):
        log.error("LinkedIn credentials not set in .env — aborting.")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Initialise components
    # ------------------------------------------------------------------
    cache = CacheManager(config.CACHE_FILE)
    github = GitHubService(token=config.GITHUB_TOKEN, username=config.GITHUB_USERNAME)
    detector = ProjectDetector()
    ai = config.get_ai_provider()
    parser = ProjectParser(github=github, ai=ai)

    log.info("AI provider: %s", type(ai).__name__)

    # ------------------------------------------------------------------
    # 1. Fetch repositories
    # ------------------------------------------------------------------
    repos = github.get_user_repos(repo_filter=args.repo)
    if not repos:
        log.warning("No repositories found. Check GITHUB_USERNAME and token.")
        sys.exit(0)

    # ------------------------------------------------------------------
    # 2. Detect projects & filter cached
    # ------------------------------------------------------------------
    all_projects: List[Dict[str, Any]] = []
    for repo in repos:
        tree = github.get_repo_tree(repo["name"])
        projects = detector.detect(
            repo_name=repo["name"],
            repo_url=repo["html_url"],
            file_paths=tree,
        )
        for p in projects:
            cache_key = f"{p['repo_name']}/{p['project_name']}"
            if cache.is_cached(cache_key):
                log.info("Skipping (cached): %s", cache_key)
                continue
            all_projects.append((p, repo))  # type: ignore[arg-type]

    if not all_projects:
        log.info("No new projects to process. Everything is up to date!")
        sys.exit(0)

    log.info("Found %d new project(s) to process.", len(all_projects))

    # ------------------------------------------------------------------
    # 3. Generate AI content
    # ------------------------------------------------------------------
    enriched: List[Dict[str, Any]] = []
    for project, repo_meta in all_projects:  # type: ignore[misc]
        content = parser.parse(project, repo_meta)
        enriched.append(content)
        log.info("Generated content for '%s'.", content.get("title", project["project_name"]))

    # ------------------------------------------------------------------
    # 4. Dry-run or LinkedIn autofill
    # ------------------------------------------------------------------
    if args.dry_run:
        log.info("DRY RUN — printing generated content:\n")
        print(json.dumps(enriched, indent=2, ensure_ascii=False))
    else:
        linkedin = LinkedInAutomation(
            email=config.LINKEDIN_EMAIL,
            password=config.LINKEDIN_PASSWORD,
        )
        try:
            linkedin.start()
            for content in enriched:
                linkedin.add_project(content)
                cache_key = f"{content['repo_name']}/{content['project_name']}"
                cache.mark_cached(cache_key)
                log.info("Cached: %s", cache_key)
        except Exception as exc:
            log.error("LinkedIn automation failed: %s", exc)
            raise
        finally:
            linkedin.stop()

    # If dry-run, still mark as cached so re-runs are idempotent
    if args.dry_run:
        for content in enriched:
            cache_key = f"{content['repo_name']}/{content['project_name']}"
            cache.mark_cached(cache_key)

    log.info("Done! Processed %d project(s).", len(enriched))


if __name__ == "__main__":
    main()
