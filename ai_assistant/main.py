"""
Main entry point for the Local Windows AI Assistant.
Runs a CLI loop:  User Input → LLM → Validate → Execute → Output
"""

from __future__ import annotations

import json
import sys
import textwrap
from typing import Any

from config import ALLOWED_ACTIONS, ALLOWED_ROOTS, LLM_PROVIDER
from executor import Executor
from llm_interface import LLMInterface
from validator import ValidationError, Validator

# ========================
# ANSI colour helpers
# ========================
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def banner() -> None:
    print(
        f"""{CYAN}{BOLD}
╔══════════════════════════════════════════════════════════════╗
║         🤖  LOCAL WINDOWS AI ASSISTANT  🤖                  ║
║                                                              ║
║   Speak naturally — I'll turn it into safe OS commands.      ║
║   Type 'quit' or 'exit' to leave.   Type 'help' for info.   ║
╚══════════════════════════════════════════════════════════════╝{RESET}
"""
    )
    print(f"  {DIM}LLM provider : {LLM_PROVIDER}{RESET}")
    print(f"  {DIM}Allowed dirs : {', '.join(ALLOWED_ROOTS)}{RESET}")
    print()


def show_help() -> None:
    print(
        f"""{YELLOW}
  ── Example commands ──────────────────────────────────────
  • "Open my Documents folder"
  • "List everything in D:\\Workspace"
  • "Search for .pdf files in Documents"
  • "Create a folder called Projects in D:\\Workspace"
  • "Delete test.txt from D:\\Workspace"
  • "Open Notepad"
  • "Close Chrome"
  • "Change wallpaper to D:\\Workspace\\bg.jpg"
  • "Copy report.docx to D:\\Workspace\\archive"
  ──────────────────────────────────────────────────────────{RESET}
"""
    )


def ask_confirmation(command: dict[str, Any]) -> bool:
    """Prompt user for confirmation on destructive actions."""
    action = command["action"]
    params = command.get("parameters", {})
    print(f"\n  {RED}{BOLD}⚠  CONFIRMATION REQUIRED{RESET}")
    print(f"  {YELLOW}Action : {action}{RESET}")
    for k, v in params.items():
        print(f"  {YELLOW}{k:12s}: {v}{RESET}")
    answer = input(f"\n  {BOLD}Proceed? (y/N): {RESET}").strip().lower()
    return answer in ("y", "yes")


def pretty_result(result: dict[str, Any]) -> None:
    """Print the execution result in a readable way."""
    status = result.get("status", "unknown")

    colour = GREEN if status == "success" else (
        YELLOW if status in ("info", "clarify") else RED
    )

    print(f"\n  {colour}{BOLD}[{status.upper()}]{RESET}")

    if "message" in result:
        print(f"  {colour}{result['message']}{RESET}")
    if "reason" in result:
        print(f"  {colour}{result['reason']}{RESET}")
    if "data" in result:
        data = result["data"]
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    name = item.get("name", "")
                    kind = item.get("type", "")
                    size = item.get("size", "")
                    icon = "📁" if kind == "DIR" else "📄"
                    print(f"    {icon}  {name:40s}  {kind:4s}  {size}")
                else:
                    print(f"    {item}")
        else:
            print(f"  {data}")
    if "matches" in result:
        matches = result["matches"]
        print(f"  Found {len(matches)} match(es):")
        for m in matches[:30]:
            print(f"    📄 {m}")
        if len(matches) > 30:
            print(f"    … and {len(matches) - 30} more")
    print()


# ========================
# MAIN LOOP
# ========================

def main() -> None:
    banner()

    try:
        llm = LLMInterface()
    except EnvironmentError as exc:
        print(f"\n  {RED}{BOLD}ERROR:{RESET} {exc}")
        sys.exit(1)

    validator = Validator()
    executor = Executor()

    while True:
        try:
            user_input = input(f"{CYAN}{BOLD}  You ▸ {RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{DIM}  Goodbye!{RESET}\n")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print(f"\n{DIM}  Goodbye!{RESET}\n")
            break
        if user_input.lower() in ("help", "?"):
            show_help()
            continue

        # 1 ─ LLM: natural language → JSON
        print(f"\n  {DIM}⏳ Thinking …{RESET}")
        try:
            raw_json = llm.process(user_input)
        except Exception as exc:
            print(f"  {RED}LLM error: {exc}{RESET}\n")
            continue

        print(f"  {DIM}📦 LLM response:{RESET}")
        try:
            print(
                f"  {DIM}{json.dumps(json.loads(raw_json), indent=2)}{RESET}"
            )
        except Exception:
            print(f"  {DIM}{raw_json}{RESET}")

        # 2 ─ Parse + Validate
        try:
            command = validator.parse_json(raw_json)
            command = validator.validate(command)
        except ValidationError as exc:
            print(f"  {RED}Validation failed: {exc}{RESET}\n")
            continue

        # 3 ─ Confirmation gate
        if command.get("requires_confirmation", False):
            if not ask_confirmation(command):
                print(f"  {YELLOW}Cancelled by user.{RESET}\n")
                continue

        # 4 ─ Execute
        result = executor.execute(command)

        # 5 ─ Display
        pretty_result(result)


if __name__ == "__main__":
    main()
