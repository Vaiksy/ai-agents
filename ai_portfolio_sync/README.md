# AI Portfolio Sync

> **Automatically detect GitHub projects and populate your LinkedIn profile — powered by local AI.**

AI Portfolio Sync scans your GitHub repositories, detects independent projects and sub-projects, generates polished LinkedIn-optimised descriptions using a local LLM (Ollama), and autofills LinkedIn's "Add Project" form via Playwright — pausing before Save so you stay in control.

---

## Why This Exists

Keeping your LinkedIn profile in sync with your GitHub work is tedious and easy to forget. This tool eliminates the grunt work:

- **Discovers** new repos and sub-projects automatically.
- **Generates** recruiter-quality titles, summaries, and skill tags.
- **Fills** LinkedIn's project form — you just click Save.
- **Runs 100 % offline** with Ollama (no API key required).
- **Optionally** connects to any OpenAI-compatible cloud LLM.

---

## Features

| Capability | Details |
|---|---|
| 🔍 Repo scanning | Fetches all public repos via GitHub REST API |
| 📂 Sub-project detection | Finds projects inside mono-repos by marker files |
| 🤖 AI content generation | Titles, 3–5 impact bullets, summary, 5–10 skills |
| 🧠 Dual LLM support | Ollama (local, free) **or** OpenAI-compatible cloud |
| 🖥️ LinkedIn autofill | Non-headless Playwright with human-like typing |
| ⏸️ Manual confirmation | Stops before Save — you review first |
| 💾 Duplicate prevention | Local JSON cache with atomic writes |
| 🛡️ Corruption recovery | Cache auto-resets on JSON parse failure |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                          CLI (main.py)                       │
│   --repo <name>   --dry-run   --debug                        │
└──────────┬───────────────────────────────────┬───────────────┘
           │                                   │
           ▼                                   ▼
┌─────────────────────┐             ┌─────────────────────────┐
│  GitHubService      │             │  CacheManager           │
│  (github_service.py)│             │  (cache_manager.py)     │
│  REST API v3        │             │  data/project_cache.json│
└────────┬────────────┘             └─────────────────────────┘
         │
         ▼
┌─────────────────────┐
│  ProjectDetector    │
│  (project_detector) │
│  Marker-file scan   │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐      ┌────────────────────────────────┐
│  ProjectParser      │─────►│  AIProvider (abstract)         │
│  (project_parser)   │      │  ├─ OllamaProvider (local)     │
└────────┬────────────┘      │  └─ CloudProvider  (optional)  │
         │                   └────────────────────────────────┘
         ▼
┌─────────────────────┐
│  LinkedInAutomation │
│  (linkedin_auto…)   │
│  Playwright fill    │
│  ⏸ STOPS before Save│
└─────────────────────┘
```

---

## Tech Stack

- **Python 3.11+**
- **Playwright** — browser automation
- **Requests** — GitHub REST API
- **Ollama** — local LLM inference (default)
- **OpenAI SDK** — cloud LLM (optional)
- **python-dotenv** — environment configuration

---

## Setup Instructions

### 1. Clone & install

```bash
git clone https://github.com/<you>/ai-portfolio-sync.git
cd ai-portfolio-sync
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
python -m playwright install chromium
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Ollama setup (free, local)

```bash
# Install Ollama — https://ollama.com/download
ollama pull qwen2.5-coder:7b   # download the model
ollama serve              # starts on http://localhost:11434
```

Verify it's running:

```bash
curl http://localhost:11434/api/tags
```

### 4. (Optional) Cloud setup

Set these in `.env`:

```ini
USE_CLOUD=true
CLOUD_API_KEY=sk-...
CLOUD_MODEL=gpt-4o-mini
```

Any OpenAI-compatible endpoint works — just change `CLOUD_BASE_URL`.

---

## CLI Usage

```bash
# Scan all repos, generate content, and open LinkedIn
python main.py

# Process a single repository
python main.py --repo my-awesome-project

# Preview generated content without touching LinkedIn
python main.py --dry-run

# Verbose logging
python main.py --debug

# Combine flags
python main.py --repo my-repo --dry-run --debug
```

---

## Example Workflow

```
1. python main.py --dry-run
   → Fetches 12 repos
   → Detects 18 projects
   → Skips 5 (cached)
   → Generates LinkedIn content for 13 new projects
   → Prints JSON output

2. python main.py --repo portfolio-site
   → Opens Chromium → logs into LinkedIn
   → Navigates to profile → opens Add Project form
   → Fills title, description, skills, URL
   → ⏸ STOPS — you review and click Save

3. python main.py
   → Processes all remaining un-cached projects one by one
```

---

## Safety Disclaimer

> **⚠️ Use this tool responsibly.**
>
> - LinkedIn may flag automated activity. Use reasonable delays and avoid bulk runs.
> - The tool **never clicks Save** — you always confirm manually.
> - Store credentials securely; never commit `.env` to version control.
> - This project is for educational and personal productivity use only.
> - The author is not responsible for any account restrictions.

---

## Future Roadmap

- [ ] GitHub Actions integration for scheduled syncing
- [ ] Support private repositories
- [ ] Resume / portfolio website generation
- [ ] Multi-profile support (LinkedIn + personal site)
- [ ] Interactive TUI with Rich / Textual
- [ ] Webhook-driven sync on push events
- [ ] Export to Notion / Google Docs
- [ ] Unit and integration test suite

---

## License

MIT — see [LICENSE](LICENSE) for details.
