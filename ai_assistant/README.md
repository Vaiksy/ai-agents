# 🤖 Local Windows AI Assistant

> **Talk to your PC in plain English — and watch it execute safe OS commands.**

A lightweight, privacy-first CLI assistant that translates natural-language instructions into validated, sandboxed Windows operations. Powered by **Google Gemini** or **OpenAI GPT**, all commands are security-checked before execution so your system stays safe.

---

## 📑 Table of Contents

- [How It Works](#-how-it-works)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#%EF%B8%8F-configuration)
- [Running the Assistant](#-running-the-assistant)
- [Supported Actions & Example Commands](#-supported-actions--example-commands)
- [Security Model](#-security-model)
- [Logging](#-logging)
- [Troubleshooting](#-troubleshooting)
- [License](#-license)

---

## 🧠 How It Works

The assistant follows a strict **5-step pipeline** for every user request:

```
User Input (English) → LLM (JSON) → Validate → Confirm → Execute
```

| Step | What Happens |
|------|-------------|
| **1. User Input** | You type a natural-language instruction (e.g. *"Open my Documents folder"*). |
| **2. LLM Translation** | The instruction is sent to **Gemini** or **OpenAI**. The LLM returns a structured **JSON command** — never free text. |
| **3. Validation** | The `Validator` checks: Is the action allowed? Are all paths inside permitted directories? Is the JSON well-formed? |
| **4. Confirmation** | Destructive actions (delete, move) trigger an interactive **Y/N confirmation prompt** before anything runs. |
| **5. Execution** | The `Executor` dispatches the command to the correct OS handler and returns a human-readable result. |

If any step fails — bad JSON, disallowed path, unknown action — the pipeline **short-circuits** with a clear error message and nothing is touched on disk.

---

## 🏗 Architecture

```
┌──────────────┐
│   User CLI   │   You type natural language
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ LLMInterface │   Sends prompt to Gemini / OpenAI
│              │   Returns structured JSON
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Validator   │   Checks action allow-list
│              │   Validates all paths against sandbox
│              │   Enforces confirmation on destructive ops
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Executor    │   Dispatches to OS-level handlers
│              │   Returns status + message / data
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  CLI Output  │   Pretty-printed, colour-coded results
└──────────────┘
```

### JSON Command Schema

Every LLM response follows this contract:

```json
{
  "action": "<action_name>",
  "parameters": {
    "path": "full_path_if_applicable",
    "additional_parameter": "value_if_needed"
  },
  "requires_confirmation": false
}
```

---

## 📂 Project Structure

```
ai_assistant/
├── main.py             # CLI entry point & main REPL loop
├── config.py           # All configuration: allowed dirs, actions, LLM settings, system prompt
├── llm_interface.py    # Gemini / OpenAI API wrapper
├── validator.py        # Security checks: path sandboxing, action allow-list, confirmation enforcement
├── executor.py         # OS-level command handlers (open, delete, copy, wallpaper, etc.)
├── requirements.txt    # Python dependencies
├── logs/               # Auto-created runtime logs (one file per day)
└── README.md           # This file
```

| Module | Responsibility |
|--------|---------------|
| `main.py` | Runs the interactive CLI loop, wires all components together, handles colours & UX |
| `config.py` | Single source of truth for allowed directories, allowed actions, LLM provider/model, and the system prompt sent to the LLM |
| `llm_interface.py` | Thin wrapper around **Google GenAI SDK** and **OpenAI SDK** — sends the user's message along with the system prompt and returns raw JSON |
| `validator.py` | Parses LLM JSON, validates structure, checks every path against the allowed-root sandbox, blocks dangerous system directories, forces confirmation on destructive actions |
| `executor.py` | Contains one handler per action (e.g. `_do_open_folder`, `_do_delete_file`). Uses `os`, `shutil`, `subprocess`, and `ctypes` to perform real OS operations |

---

## ✅ Prerequisites

- **OS:** Windows 10 / 11
- **Python:** 3.10 or higher
- **API Key:** At least one of:
  - Google Gemini API key (`GEMINI_API_KEY`)
  - OpenAI API key (`OPENAI_API_KEY`)

---

## 📦 Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd ai_assistant
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

The `requirements.txt` includes:

| Package | Purpose |
|---------|---------|
| `google-genai` | Google Gemini SDK |
| `openai` | OpenAI SDK |
| `python-dotenv` | Load `.env` files for API keys |
| `fastapi` / `uvicorn` | Optional — for future REST API extension |

---

## ⚙️ Configuration

### Environment Variables

Set your API key(s) before running:

```powershell
# PowerShell
$env:GEMINI_API_KEY = "your_gemini_api_key_here"

# Or for OpenAI
$env:OPENAI_API_KEY = "your_openai_api_key_here"
$env:LLM_PROVIDER   = "openai"
```

```cmd
:: CMD
set GEMINI_API_KEY=your_gemini_api_key_here

:: Or for OpenAI
set OPENAI_API_KEY=your_openai_api_key_here
set LLM_PROVIDER=openai
```

> **Tip:** You can also create a `.env` file in the project root and use `python-dotenv` to auto-load them.

### Key Config Options (in `config.py`)

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `"gemini"` | LLM backend — `"gemini"` or `"openai"` |
| `GEMINI_MODEL` | `"gemini-2.0-flash"` | Gemini model to use |
| `OPENAI_MODEL` | `"gpt-4o-mini"` | OpenAI model to use |
| `ALLOWED_ROOTS` | `D:\Workspace`, `C:\Users\vaiks\Documents` | Directories the assistant is allowed to access |
| `ALLOWED_ACTIONS` | 11 actions (see below) | Whitelist of permitted OS operations |
| `DESTRUCTIVE_ACTIONS` | `delete_file`, `move_file` | Actions that require explicit user confirmation |

### Customising Allowed Directories

Edit the `ALLOWED_ROOTS` list in `config.py`:

```python
ALLOWED_ROOTS: list[str] = [
    r"D:\Workspace",
    r"C:\Users\vaiks\Documents",
    r"E:\Projects",          # ← add your own
]
```

---

## 🚀 Running the Assistant

```bash
python main.py
```

You'll see:

```
╔══════════════════════════════════════════════════════════════╗
║         🤖  LOCAL WINDOWS AI ASSISTANT  🤖                  ║
║                                                              ║
║   Speak naturally — I'll turn it into safe OS commands.      ║
║   Type 'quit' or 'exit' to leave.   Type 'help' for info.   ║
╚══════════════════════════════════════════════════════════════╝

  LLM provider : gemini
  Allowed dirs : D:\Workspace, C:\Users\vaiks\Documents

  You ▸ _
```

### CLI Commands

| Input | Action |
|-------|--------|
| Any natural language | Processed by the LLM pipeline |
| `help` or `?` | Show example commands |
| `quit`, `exit`, or `q` | Exit the assistant |
| `Ctrl+C` | Exit immediately |

---

## 🎯 Supported Actions & Example Commands

### 📁 File & Folder Operations

| Action | What it does | Example prompt |
|--------|-------------|----------------|
| `open_folder` | Opens a folder in Windows Explorer | *"Open my Documents folder"* |
| `open_file` | Opens a file with its default app | *"Open report.pdf in Documents"* |
| `list_directory` | Lists all files and folders in a directory | *"List everything in D:\Workspace"* |
| `search_file` | Searches for files by name/pattern | *"Search for .pdf files in Documents"* |
| `create_folder` | Creates a new directory | *"Create a folder called Projects in D:\Workspace"* |
| `delete_file` | Deletes a file or folder (**requires confirmation**) | *"Delete test.txt from D:\Workspace"* |
| `move_file` | Moves a file to a new location (**requires confirmation**) | *"Move notes.txt to D:\Workspace\archive"* |
| `copy_file` | Copies a file or folder | *"Copy report.docx to D:\Workspace\archive"* |

### 💻 Application Control

| Action | What it does | Example prompt |
|--------|-------------|----------------|
| `open_application` | Launches an app by name | *"Open Notepad"* |
| `close_application` | Force-closes a running app | *"Close Chrome"* |

**Supported app aliases:** `notepad`, `calculator` / `calc`, `paint`, `cmd`, `powershell`, `explorer`, `chrome`, `firefox`, `edge`, `code` / `vscode`, `word`, `excel`, `spotify`, `terminal`

### 🖼️ System

| Action | What it does | Example prompt |
|--------|-------------|----------------|
| `change_wallpaper` | Sets the desktop wallpaper to an image file | *"Change wallpaper to D:\Workspace\bg.jpg"* |

---

## 🔒 Security Model

The assistant enforces **multiple layers of security** so it can never harm your system:

### 1. Path Sandboxing
- Every path in a command is **resolved** and checked against `ALLOWED_ROOTS`.
- Paths must fall under one of the explicitly allowed directories.
- Path traversal attacks (e.g. `..\..\Windows`) are defeated by resolving paths before comparison.

### 2. Dangerous Path Blocklist
Even if a clever path somehow passes the root check, an additional blocklist catches:
- `C:\Windows`, `System32`, `Program Files`, `Program Files (x86)`
- `ProgramData`, `AppData`, `$Recycle.Bin`, `Boot`

### 3. Action Allow-List
Only the 11 predefined actions are permitted. The LLM cannot invent new actions — any unknown action is rejected.

### 4. Destructive Action Confirmation
`delete_file` and `move_file` always require an explicit **Y/N prompt**, regardless of what the LLM returns.

### 5. JSON-Only LLM Output
The LLM is instructed to return **only valid JSON** (`response_mime_type="application/json"` for Gemini, `response_format={"type": "json_object"}` for OpenAI). If parsing fails, the command is rejected.

### 6. Clarify / Deny Passthrough
If the LLM itself is unsure, it returns a `"clarify"` or `"denied"` action — these are displayed to the user without executing anything.

---

## 📝 Logging

All executed commands are logged to the `logs/` directory, one file per day:

```
logs/assistant_20260227.log
```

Log format:
```
2026-02-27 21:30:00 | INFO | EXEC  action=open_folder  params={'path': 'D:\\Workspace'}
2026-02-27 21:30:00 | INFO | OK    action=open_folder  result={'status': 'success', ...}
```

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| `GEMINI_API_KEY is not set` | Set the environment variable: `set GEMINI_API_KEY=your_key` |
| `OPENAI_API_KEY is not set` | Set the environment variable: `set OPENAI_API_KEY=your_key` |
| `Unsupported LLM_PROVIDER` | Set `LLM_PROVIDER` to `gemini` or `openai` |
| `Invalid JSON from LLM` | Occasionally the LLM may hallucinate bad JSON — retry your command |
| `Access denied — path is outside allowed directories` | Edit `ALLOWED_ROOTS` in `config.py` to add the directory |
| `Action 'xyz' is not allowed` | Only the 11 predefined actions are supported |
| `ModuleNotFoundError: google.genai` | Run `pip install google-genai` |
| `ModuleNotFoundError: openai` | Run `pip install openai` |

---

## 🛠 How We Built It

### Design Philosophy
We designed this assistant with **security-first** thinking. Instead of giving an LLM direct shell access, we created a strict pipeline where:

1. **The LLM only produces data** (JSON) — it never touches the OS directly.
2. **A validator acts as a firewall** — parsing, sandboxing, and rejecting anything suspicious.
3. **The executor is a dumb dispatcher** — it only knows how to run pre-approved operations.

### Tech Stack
- **Python 3.10+** — core language
- **Google GenAI SDK** / **OpenAI SDK** — LLM integration
- **ctypes** — Windows API calls (e.g. wallpaper)
- **subprocess** — app launching and process management
- **shutil** / **os** / **pathlib** — file system operations

### Build Process
1. Defined the **JSON command schema** and the list of allowed actions.
2. Crafted a detailed **system prompt** (in `config.py`) that constrains the LLM to output only valid JSON commands.
3. Built the **Validator** with path resolution, root-checking, dangerous-path blocklist, and confirmation enforcement.
4. Built the **Executor** with one handler per action, each performing the minimal OS call needed.
5. Wired everything together in `main.py` with a colourful REPL and error handling.

---

## 📄 License

This project is for personal / educational use. Feel free to modify and extend it for your own needs.

---

<div align="center">

**Built with ❤️ on Windows · Powered by Gemini & OpenAI**

</div>
