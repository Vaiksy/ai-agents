# Autonomous Content Intelligence Agent

A FastAPI-based research and strategy tool that analyzes a content niche, maps competitive saturation, identifies opportunity gaps, and generates actionable content plans — powered by a local or cloud LLM of your choice.

---

## Table of Contents

- [Key Features](#key-features)
- [What It Does](#what-it-does)
- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Clone the Repository](#clone-the-repository)
  - [Virtual Environment Setup](#virtual-environment-setup)
  - [Dependency Installation](#dependency-installation)
- [LLM Provider Setup](#llm-provider-setup)
  - [Option A: Ollama (Local)](#option-a-ollama-local)
  - [Option B: OpenAI API](#option-b-openai-api)
  - [Option C: Anthropic Claude API](#option-c-anthropic-claude-api)
- [Environment Variables](#environment-variables)
- [Running the Server](#running-the-server)
- [Using the UI](#using-the-ui)
- [API Usage](#api-usage)
- [Response Structure](#response-structure)
- [LLM Provider Routing](#llm-provider-routing)
- [Optional: Embeddings](#optional-embeddings)
- [Performance Notes](#performance-notes)
- [Common Errors and Fixes](#common-errors-and-fixes)
- [Security & Privacy Notes](#security--privacy-notes)
- [Roadmap](#roadmap)
- [License](#license)

---

## Key Features

- **Niche Research Engine** — Scrapes DuckDuckGo and Bing to gather live content signals for any topic
- **Competitive Analysis** — Identifies existing content patterns, dominant angles, and common formats in a niche
- **Saturation Detection** — Scores keyword and topic saturation to surface over-crowded vs. under-served areas
- **Gap Analysis** — Pinpoints opportunity gaps where audience demand exists but content supply is weak
- **Strategic Content Planning** — Uses a two-pass LLM pipeline to generate a prioritized, actionable content strategy
- **Dual Output Format** — Returns both a human-readable English report and a structured JSON payload
- **Multi-Provider LLM Support** — Works with local models via Ollama, OpenAI, or Anthropic Claude
- **Browser-based UI** — Simple Jinja-templated interface; no frontend build step required
- **Response Caching** — Caches research results to avoid redundant scraping during iteration

---

## What It Does

You provide a content niche (e.g., *"budget travel in Southeast Asia"* or *"home espresso for beginners"*). The agent then:

1. **Researches** the niche by scraping search results and collecting signals about what content already exists
2. **Analyzes** keyword frequency, topic clustering, and content format distribution to measure saturation
3. **Detects gaps** — topics with meaningful search interest but sparse, low-quality, or outdated coverage
4. **Generates a strategy** using a two-pass LLM approach: a first pass that structures the opportunity landscape, and a second pass that produces specific, prioritized content recommendations
5. **Outputs a report** in plain English alongside a machine-readable JSON object, so results can be read directly or consumed by downstream tooling

The entire pipeline runs on a single API call and is accessible from the included web UI or via `curl`.

---

## Architecture Overview

```
Browser / curl
      │
      ▼
┌─────────────┐
│  FastAPI     │  ← api/app.py
│  (HTTP layer)│
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  Pipeline       │  ← core/pipeline.py
│  (orchestrator) │
└──┬──────────┬───┘
   │          │
   ▼          ▼
┌──────────┐  ┌──────────────────┐
│ Research │  │  Intelligence    │
│ Engine   │  │  Engine          │
│          │  │  (saturation,    │
│ DuckDuck │  │   gap analysis,  │
│ Go/Bing  │  │   keyword rank)  │
└──────────┘  └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │  Strategy Engine │
              │  (2-pass LLM     │
              │   generation)    │
              └────────┬─────────┘
                       │
              ┌────────▼─────────┐
              │  Report Engine   │
              │  (human-readable │
              │   formatting)    │
              └────────┬─────────┘
                       │
              ┌────────▼─────────┐
              │  LLM Router      │
              │  Ollama /        │
              │  OpenAI /        │
              │  Anthropic       │
              └──────────────────┘
```

The pipeline is fully synchronous by default. The research engine writes results to a local cache directory to speed up repeated runs on the same niche.

---

## Project Structure

```
content_intelligence_engine/
├── api/
│   └── app.py                  # FastAPI app, route definitions
├── core/
│   ├── pipeline.py             # Top-level orchestrator; calls all engines in sequence
│   ├── research_engine.py      # Web scraping via DuckDuckGo / Bing
│   ├── intelligence_engine.py  # Keyword analysis, saturation scoring, gap detection
│   ├── strategy_engine.py      # Two-pass LLM strategy generation
│   ├── report_engine.py        # Formats strategy output into a human-readable report
│   ├── embedding_engine.py     # Optional semantic embedding support (disabled by default)
│   └── ollama_client.py        # Ollama API client wrapper
├── templates/
│   └── index.html              # Jinja2 UI template
├── cache/                      # Local cache for research results
├── requirements.txt
└── README.md
```

---

## Installation

### Prerequisites

| Requirement | Version |
|-------------|---------|
| Python | 3.10 or higher |
| pip | Latest recommended |
| Git | Any recent version |
| Ollama *(optional)* | Latest — only if using local models |

### Clone the Repository

```bash
git clone 
cd content-intelligence-agent/content_intelligence_engine
```

### Virtual Environment Setup

**Linux / macOS**

```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (Command Prompt)**

```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**Windows (PowerShell)**

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

You should see `(venv)` prefixed in your terminal prompt once the environment is active.

### Dependency Installation

```bash
pip install -r requirements.txt
```

---

## LLM Provider Setup

The agent supports three LLM backends. Configure one before running.

### Option A: Ollama (Local)

Ollama lets you run models entirely on your own hardware — no API key required.

1. Install Ollama from [https://ollama.com](https://ollama.com)

2. Pull the default model used by this project:

```bash
ollama pull qwen2.5-coder:7b
```

3. Confirm Ollama is running:

```bash
ollama list
# Should show qwen2.5-coder:7b in the output
```

Ollama exposes a local REST API at `http://localhost:11434` by default. No additional configuration is needed if you use the default host and model.

> **Note:** `qwen2.5-coder:7b` requires approximately 5–6 GB of RAM. If your hardware is constrained, consider a smaller model and update `LLM_MODEL` accordingly.

### Option B: OpenAI API

1. Obtain an API key from [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)

2. Set the following environment variables (see [Environment Variables](#environment-variables)):

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4o
```

### Option C: Anthropic Claude API

1. Obtain an API key from [https://console.anthropic.com](https://console.anthropic.com)

2. Set the following environment variables:

```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
LLM_MODEL=claude-3-5-sonnet-20241022
```

---

## Environment Variables

Create a `.env` file in the `content_intelligence_engine/` directory. The application reads this file at startup.

```env
# ── LLM Provider ──────────────────────────────────────────
# Options: ollama | openai | anthropic
LLM_PROVIDER=ollama

# Model name to use. Must match the provider.
# Ollama default: qwen2.5-coder:7b
# OpenAI example: gpt-4o
# Anthropic example: claude-3-5-sonnet-20241022
LLM_MODEL=qwen2.5-coder:7b

# ── API Keys (only required for the chosen provider) ──────
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# ── Ollama Host (only if not running on default) ──────────
OLLAMA_HOST=http://localhost:11434

# ── Embeddings (disabled by default) ─────────────────────
ENABLE_EMBEDDINGS=false

# ── Application ───────────────────────────────────────────
# Port for the FastAPI server
APP_PORT=8000
```

> **Never commit your `.env` file to version control.** A `.gitignore` entry for `.env` is strongly recommended.

---

## Running the Server

With your virtual environment active and `.env` configured:

```bash
uvicorn api.app:app --reload --port 8000
```

The server will be available at `http://localhost:8000`.

The `--reload` flag enables hot-reloading during development. Remove it for production use.

To bind to a different port, update `APP_PORT` in `.env` or pass `--port` directly:

```bash
uvicorn api.app:app --port 8080
```

---

## Using the UI

Open your browser and navigate to:

```
http://localhost:8000
```

The UI presents a single input form. Enter a content niche — be specific for better results (e.g., `"beginner Python tutorials for data science"` rather than just `"Python"`).

Submit the form to run the full pipeline. Results are displayed on the same page once the pipeline completes, including both the human-readable report and optionally the raw JSON.

Processing time depends on your LLM provider and hardware. Local Ollama runs on consumer hardware typically complete in 30–90 seconds for a standard niche.

---

## API Usage

The pipeline is also accessible directly via REST API.

### Analyze a Niche

**Endpoint:** `POST /analyze`

**Request:**

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"niche": "budget home recording studio setup"}'
```

**With optional parameters:**

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "niche": "budget home recording studio setup",
    "max_results": 20,
    "use_cache": true
  }'
```

---

## Response Structure

The API returns a JSON object with two top-level keys:

```json
{
  "human_report": "...",
  "data": { ... }
}
```

### `human_report`

A plain-English string containing the full strategy report. This is intended to be read directly — no parsing required. It covers the saturation assessment, identified gaps, and prioritized content recommendations.

### `data`

A structured JSON object containing the raw analysis output. Approximate shape:

```json
{
  "niche": "budget home recording studio setup",
  "research": {
    "sources_scraped": 18,
    "keywords_extracted": ["audio interface", "condenser mic", "DAW", "..."],
    "top_domains": ["..."]
  },
  "intelligence": {
    "saturation_score": 0.63,
    "saturated_topics": ["..."],
    "gap_topics": ["..."],
    "keyword_frequency": { "audio interface": 14, "...": 0 }
  },
  "strategy": {
    "pass_one": "...",
    "pass_two": "...",
    "recommendations": [
      {
        "title": "...",
        "angle": "...",
        "priority": "high",
        "rationale": "..."
      }
    ]
  }
}
```

The `data` object is suitable for downstream automation, storage, or further processing. The `human_report` is suitable for display or export.

---

## LLM Provider Routing

The routing logic lives in the pipeline and is controlled entirely by the `LLM_PROVIDER` environment variable. At startup, the application reads this value and initializes the appropriate client:

- `ollama` → uses `core/ollama_client.py`, which communicates with the local Ollama HTTP API
- `openai` → uses the `openai` Python SDK with `OPENAI_API_KEY`
- `anthropic` → uses the `anthropic` Python SDK with `ANTHROPIC_API_KEY`

All three providers are called through the same internal interface. The strategy engine issues two sequential prompts (two-pass generation) through whichever client is active — the first pass structures the opportunity landscape from the intelligence data, and the second pass uses that structure to produce specific, prioritized content recommendations.

Switching providers requires only a change to `.env` — no code changes.

---

## Optional: Embeddings

Semantic embedding support is implemented in `core/embedding_engine.py` but is **disabled by default** to keep the setup lightweight and avoid requiring a separate embedding model or service.

Embeddings can be used to cluster scraped content semantically and improve gap detection accuracy, particularly on large or ambiguous niches.

To enable:

1. Set `ENABLE_EMBEDDINGS=true` in `.env`
2. Ensure your chosen embedding backend is available and configured (refer to inline documentation in `embedding_engine.py` for supported backends)

When disabled, the intelligence engine falls back to keyword-frequency-based analysis only.

---

## Performance Notes

- **Local Ollama (qwen2.5-coder:7b):** Typical end-to-end time is 30–90 seconds on a machine with 16 GB RAM. GPU acceleration via CUDA or Metal significantly reduces this.
- **OpenAI / Anthropic:** End-to-end time is primarily network-bound and typically completes in 10–25 seconds depending on API latency and response length.
- **Caching:** Research results are cached in the `cache/` directory. Re-running the same niche with `use_cache: true` skips the scraping phase and runs only the intelligence and strategy engines, reducing time to a few seconds for subsequent iterations.
- **Scraping rate limits:** DuckDuckGo and Bing may throttle or block requests under high volume. The research engine includes basic delays, but extended use may require proxies or rate-limit handling.

---

## Common Errors and Fixes

**`ConnectionRefusedError` or `httpx.ConnectError` when using Ollama**

Ollama is not running, or is running on a non-default port.

```bash
# Start Ollama
ollama serve

# Verify
curl http://localhost:11434
```

If you changed the port, update `OLLAMA_HOST` in `.env`.

---

**`model not found` error from Ollama**

The model has not been pulled locally.

```bash
ollama pull qwen2.5-coder:7b
```

---

**`AuthenticationError` from OpenAI or Anthropic**

Your API key is missing, invalid, or has insufficient permissions. Check that `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` is set correctly in `.env` and that the key is active in your provider dashboard.

---

**Empty or very short `human_report`**

This usually means the LLM returned an incomplete response due to a short `max_tokens` setting or a context length overflow. Try reducing `max_results` in your request to limit how much scraped text is passed to the model.

---

**`ModuleNotFoundError` on startup**

The virtual environment is either not activated or dependencies were not installed.

```bash
source venv/bin/activate       # Linux/macOS
pip install -r requirements.txt
```

---

**Scraping returns 0 results**

DuckDuckGo or Bing may be blocking the request. This can happen when running from a cloud IP or after repeated rapid requests. Try:
- Adding a delay between runs
- Checking your network/proxy configuration
- Testing the scraper manually with a simple query

---

## Security & Privacy Notes

- **API keys** are loaded from environment variables and never logged or included in API responses. Do not hardcode them in source files.
- **Scraping** sends HTTP requests from your machine (or server) to DuckDuckGo and Bing. Your IP address is visible to those services. If running in a shared or production environment, be aware of the terms of service of those platforms.
- **Local Ollama** keeps all LLM inference on your own hardware. No query data leaves your network when using this provider.
- **OpenAI and Anthropic** providers send niche queries and scraped content excerpts to their respective APIs. Review each provider's data usage and privacy policies if handling sensitive topics.
- **The `cache/` directory** stores raw scraped content. Do not commit it to version control. Add `cache/` to `.gitignore`.
- There is no authentication on the FastAPI server by default. Do not expose port 8000 to the public internet without adding an authentication layer.

---

## Roadmap

- [ ] Async pipeline execution for faster end-to-end response
- [ ] Content brief generation (per-article outlines from strategy recommendations)
- [ ] Export to Markdown and JSON file formats from the UI
- [ ] Support for additional search backends (Google via SerpAPI, custom RSS feeds)
- [ ] Scheduled recurring analysis with diff reporting (detect niche changes over time)
- [ ] Multi-niche comparison mode
- [ ] API authentication middleware
- [ ] Docker Compose setup for one-command deployment

Contributions and issue reports are welcome. See the [contributing guidelines](CONTRIBUTING.md) if available, or open an issue to discuss a proposed change before submitting a pull request.

---

## License

This project is licensed under the [MIT License](LICENSE).

---

> Built with FastAPI, Ollama, and a healthy skepticism of content that exists purely to exist.
