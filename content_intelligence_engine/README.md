# Autonomous Content Intelligence Agent

An AI-powered Content Research & Strategy Engine built with FastAPI and flexible LLM integration (Local or Cloud).

This system researches a niche, analyzes competitive content, detects saturation and opportunity gaps, and generates:

- A structured intelligence breakdown
- A clean, human-readable executive strategy report
- A practical weekly content execution plan

It supports:
- Local LLMs via Ollama
- OpenAI API
- Anthropic Claude API

---

# What This Project Does

Given:

- A topic
- A publishing platform
- A target audience
- A business goal

The engine will:

1. Research trending content in the niche
2. Extract and summarize real web pages
3. Analyze keyword patterns
4. Detect content saturation
5. Identify opportunity gaps
6. Assess competitive intensity
7. Generate a differentiated content strategy (2-pass refinement)
8. Convert output into a clean executive report

The system can run fully locally.

---

# Project Structure

content_intelligence_engine/
│
├── api/
│ └── app.py # FastAPI backend
│
├── core/
│ ├── ollama_client.py # LLM routing layer
│ ├── research_engine.py
│ ├── intelligence_engine.py
│ ├── strategy_engine.py
│ ├── report_engine.py # Human-readable report generator
│ ├── embedding_engine.py # Optional (disabled by default)
│ └── pipeline.py # Main orchestrator
│
├── templates/
│ └── index.html # UI
│
├── cache/ # Auto-created research cache
├── requirements.txt
└── README.md



---

# System Requirements

Minimum:
- Python 3.10+
- 8 GB RAM

Recommended:
- 16 GB RAM
- GPU (4GB+ VRAM) for local models

---

# Installation

## 1. Clone Repository

git clone https://github.com/Vaiksy/ai-agents.git

cd ai-agents/content_intelligence_engine


---

## 2. Create Virtual Environment

### Windows

python -m venv .venv
.venv\Scripts\activate


### macOS / Linux

python3 -m venv .venv
source .venv/bin/activate

---

## 3. Install Dependencies

pip install -r requirements.txt


---

# LLM Configuration

This project supports three providers:

- Ollama (local)
- OpenAI
- Claude (Anthropic)

The provider is selected using environment variables.

---

# Option 1 — Local LLM via Ollama (Default)

## Install Ollama

Download:
https://ollama.com/download

Start Ollama:

ollama serve


Pull required model: ollama pull qwen2.5-coder:7b


Verify: ollama list


Set environment variables:

### Windows (PowerShell)

$env:LLM_PROVIDER="ollama"
$env:LLM_MODEL="qwen2.5-coder:7b"


### macOS / Linux

export LLM_PROVIDER="ollama"
export LLM_MODEL="qwen2.5-coder:7b"


---

# Option 2 — OpenAI API

Install SDK:


Set environment variables:

### Windows

$env:OPENAI_API_KEY="your_api_key"
$env:LLM_PROVIDER="openai"
$env:LLM_MODEL="gpt-4o-mini"


### macOS / Linux
export OPENAI_API_KEY="your_api_key"
export LLM_PROVIDER="openai"
export LLM_MODEL="gpt-4o-mini"


---

# Option 3 — Claude API

Install SDK:

pip install anthropic

### Windows

Set environment variables: $env:ANTHROPIC_API_KEY="your_api_key"
$env:LLM_PROVIDER="claude"
$env:LLM_MODEL="claude-3-5-sonnet-20241022"




### macOS / Linux

export ANTHROPIC_API_KEY="your_api_key"
export LLM_PROVIDER="claude"
export LLM_MODEL="claude-3-5-sonnet-20241022"


---

# Running the Server

Ensure:
- Environment variables are set
- Ollama is running (if using local model)

Start FastAPI:

uvicorn api.app:app --reload --host 127.0.0.1 --port 8000


Open in browser: http://127.0.0.1:8000


---

# API Usage

## Run Analysis

curl -X POST http://127.0.0.1:8000/analyze

-H "Content-Type: application/json"
-d '{
"niche": "AI tools for founders",
"platform": "LinkedIn",
"audience": "Early-stage startup founders",
"goal": "Generate inbound consulting leads"
}'




The response includes:

- human_report (clean executive output)
- data (structured technical breakdown)

---

# Embeddings

Embeddings are disabled by default.

To enable semantic gap detection using Ollama: ollama pull nomic-embed-text



Then enable embeddings inside: core/embedding_engine.py



---

# Performance Notes

- First execution may take several minutes depending on hardware.
- Strategy generation uses multiple LLM calls.
- Performance improves with:
  - GPU acceleration
  - Reduced research URL count
  - Caching enabled

---

# Security & Privacy

Local Mode:
- Fully offline
- No cloud dependency

API Mode:
- Data sent to selected provider (OpenAI / Anthropic)

No telemetry included.

---

# Roadmap

- Parallel research execution
- Improved scraping robustness
- Streaming progress updates
- PDF export
- Docker deployment
- SaaS deployment version

---

# License

MIT License


