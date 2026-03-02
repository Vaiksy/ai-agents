"""
linkedin_automation.py — Playwright-based LinkedIn project autofill.

Opens a non-headless Chromium browser, logs in, navigates to the profile,
and fills the "Add project" form. **Never clicks Save** — the user must
confirm manually.
"""

from __future__ import annotations

import random
import time
from typing import Any, Dict

from playwright.sync_api import Page, sync_playwright, Browser, BrowserContext

from logger import get_logger

log = get_logger("linkedin")


def _random_delay(low: float = 1.0, high: float = 3.0) -> None:
    """Sleep for a random duration to mimic human behaviour."""
    delay = random.uniform(low, high)
    log.debug("Waiting %.1fs …", delay)
    time.sleep(delay)


def _human_type(page: Page, selector: str, text: str) -> None:
    """Type text character-by-character with random inter-key delays."""
    page.click(selector)
    _random_delay(0.3, 0.6)
    for ch in text:
        page.keyboard.type(ch, delay=random.randint(30, 120))
    _random_delay(0.3, 0.5)


class LinkedInAutomation:
    """Automate LinkedIn project-section filling via Playwright."""

    PROFILE_URL = "https://www.linkedin.com/in/me/"
    LOGIN_URL = "https://www.linkedin.com/login"

    def __init__(self, email: str, password: str) -> None:
        self._email = email
        self._password = password
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Launch browser and log into LinkedIn."""
        log.info("Launching Chromium (non-headless) …")
        pw = sync_playwright().start()
        self._browser = pw.chromium.launch(headless=False, slow_mo=50)
        self._context = self._browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        self._page = self._context.new_page()
        self._login()

    def stop(self) -> None:
        """Close the browser (called after the user has finished)."""
        if self._browser:
            log.info("Closing browser …")
            self._browser.close()

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------

    def _login(self) -> None:
        """Log into LinkedIn using email/password from config."""
        page = self._page
        assert page is not None

        log.info("Navigating to LinkedIn login …")
        page.goto(self.LOGIN_URL, wait_until="networkidle")
        _random_delay(1.5, 2.5)

        _human_type(page, "#username", self._email)
        _human_type(page, "#password", self._password)
        _random_delay(0.5, 1.0)

        page.click('button[type="submit"]')
        log.info("Submitted login form — waiting for redirect …")
        page.wait_for_url("**/feed/**", timeout=60000)
        log.info("Login successful.")
        _random_delay(2.0, 3.0)

    # ------------------------------------------------------------------
    # Project autofill
    # ------------------------------------------------------------------

    def add_project(self, content: Dict[str, Any]) -> None:
        """
        Navigate to profile and fill the Add Project form.

        The method **stops before clicking Save**.

        Args:
            content: Dict with keys ``title``, ``summary``, ``bullets``,
                ``skills``, ``github_url``.
        """
        page = self._page
        assert page is not None

        title = content.get("title", "")
        description = self._build_description(content)
        skills = content.get("skills", [])
        project_url = content.get("github_url", "")

        # 1 — Navigate to profile
        log.info("Navigating to profile …")
        page.goto(self.PROFILE_URL, wait_until="networkidle")
        _random_delay(2.0, 3.0)

        # 2 — Click "Add profile section"
        log.info("Looking for 'Add profile section' button …")
        add_section_btn = page.locator("button:has-text('Add profile section')").first
        add_section_btn.click()
        _random_delay(1.5, 2.5)

        # 3 — Click "Add projects" in the dropdown
        log.info("Selecting 'Add project' …")
        # LinkedIn's dropdown may show "Projects" or "Add project"
        project_option = page.locator(
            "button:has-text('Add project'), "
            "div[role='button']:has-text('Add project'), "
            "li:has-text('Projects'), "
            "span:has-text('Add project')"
        ).first
        project_option.click()
        _random_delay(2.0, 3.0)

        # 4 — Fill the form fields
        log.info("Filling project form …")

        # Title
        title_input = page.locator(
            "input[aria-label*='roject name'], "
            "input[placeholder*='roject name'], "
            "input[id*='project-name']"
        ).first
        if title_input.is_visible():
            title_input.click()
            title_input.fill("")
            _human_type_into_element(page, title_input, title)
            _random_delay(0.8, 1.5)

        # Description
        desc_input = page.locator(
            "textarea[aria-label*='escription'], "
            "div[aria-label*='escription'][contenteditable='true'], "
            "textarea[id*='description']"
        ).first
        if desc_input.is_visible():
            desc_input.click()
            desc_input.fill("")
            _human_type_into_element(page, desc_input, description)
            _random_delay(0.8, 1.5)

        # Project URL / associated link
        url_input = page.locator(
            "input[aria-label*='roject URL'], "
            "input[placeholder*='URL'], "
            "input[id*='project-url']"
        ).first
        if url_input.is_visible():
            url_input.click()
            url_input.fill("")
            _human_type_into_element(page, url_input, project_url)
            _random_delay(0.8, 1.5)

        # Skills (if there's a skills input)
        skills_input = page.locator(
            "input[aria-label*='kills'], "
            "input[placeholder*='kill']"
        ).first
        if skills_input.is_visible():
            for skill in skills[:10]:
                skills_input.click()
                skills_input.fill("")
                _human_type_into_element(page, skills_input, skill)
                _random_delay(0.5, 1.0)
                # Try to select the first suggestion
                suggestion = page.locator(
                    "div[role='option']:first-child, "
                    "li[role='option']:first-child"
                ).first
                if suggestion.is_visible(timeout=2000):
                    suggestion.click()
                    _random_delay(0.5, 0.8)
                else:
                    page.keyboard.press("Enter")
                    _random_delay(0.3, 0.5)

        # 5 — STOP — do NOT click Save
        log.info("=" * 60)
        log.info("FORM FILLED — Please review and click Save manually.")
        log.info("=" * 60)
        log.info("Title:       %s", title)
        log.info("Skills:      %s", ", ".join(skills))
        log.info("URL:         %s", project_url)
        log.info("Description: %s…", description[:80])

        # Keep browser open for manual review
        input("\n⏸  Press ENTER in the terminal after you have saved (or cancelled) …\n")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_description(content: Dict[str, Any]) -> str:
        """Combine summary and bullets into a LinkedIn description."""
        parts = [content.get("summary", "")]
        for bullet in content.get("bullets", []):
            parts.append(f"• {bullet}")
        return "\n\n".join(parts)


def _human_type_into_element(page: Page, locator: Any, text: str) -> None:
    """Type text character-by-character into a located element."""
    locator.click()
    for ch in text:
        page.keyboard.type(ch, delay=random.randint(25, 100))
    _random_delay(0.2, 0.4)
