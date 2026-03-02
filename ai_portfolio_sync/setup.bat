@echo off
title AI Portfolio Sync — Setup
echo.
echo ============================================================
echo   AI Portfolio Sync — Interactive Setup
echo ============================================================
echo.

REM ── Check Python ──────────────────────────────────────────
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo         Install Python 3.11+ from https://python.org
    pause
    exit /b 1
)
echo [OK] Python found.

REM ── Check Node (needed for Playwright) ────────────────────
node --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [WARNING] Node.js not found — Playwright install may fail.
    echo           Install from https://nodejs.org if needed.
)

REM ── Install dependencies ──────────────────────────────────
echo.
echo Installing Python dependencies ...
pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo [ERROR] pip install failed.
    pause
    exit /b 1
)
echo [OK] Dependencies installed.

REM ── Install Playwright browser ────────────────────────────
echo.
echo Installing Playwright Chromium browser ...
python -m playwright install chromium
echo [OK] Chromium installed.

REM ── Collect credentials ───────────────────────────────────
echo.
echo ============================================================
echo   Configure your .env file
echo ============================================================
echo.

set /p GH_TOKEN="#"
set /p GH_USER="#"
set /p LI_EMAIL="Enter your LinkedIn email: "
set /p LI_PASS="Enter your LinkedIn password: "
echo.
set /p USE_CLOUD="Use cloud LLM instead of Ollama? (yes/no) [no]: "
if /i "%USE_CLOUD%"=="" set USE_CLOUD=no

if /i "%USE_CLOUD%"=="yes" (
    set CLOUD_FLAG=true
    set /p CLOUD_KEY="Enter your Cloud API key: "
    set /p CLOUD_MODEL="Enter cloud model name [gpt-4o-mini]: "
    if "%CLOUD_MODEL%"=="" set CLOUD_MODEL=gpt-4o-mini
    set /p CLOUD_URL="Enter cloud base URL [https://api.openai.com/v1]: "
    if "%CLOUD_URL%"=="" set CLOUD_URL=https://api.openai.com/v1
) else (
    set CLOUD_FLAG=false
    set CLOUD_KEY=
    set CLOUD_MODEL=gpt-4o-mini
    set CLOUD_URL=https://api.openai.com/v1
)

REM ── Write .env ────────────────────────────────────────────
echo.
echo Writing .env file ...
(
    echo # AI Portfolio Sync — Generated Configuration
    echo.
    echo # GitHub
    echo GITHUB_TOKEN=%GH_TOKEN%
    echo GITHUB_USERNAME=%GH_USER%
    echo.
    echo # LinkedIn
    echo LINKEDIN_EMAIL=%LI_EMAIL%
    echo LINKEDIN_PASSWORD=%LI_PASS%
    echo.
    echo # AI Provider
    echo USE_CLOUD=%CLOUD_FLAG%
    echo OLLAMA_MODEL=qwen2.5-coder:7b
    echo OLLAMA_BASE_URL=http://localhost:11434
    echo.
    echo # Cloud (optional)
    echo CLOUD_API_KEY=%CLOUD_KEY%
    echo CLOUD_MODEL=%CLOUD_MODEL%
    echo CLOUD_BASE_URL=%CLOUD_URL%
) > .env
echo [OK] .env created.

REM ── Verify Ollama (if using local) ────────────────────────
if /i "%CLOUD_FLAG%"=="false" (
    echo.
    echo Checking if Ollama is running ...
    curl -s http://localhost:11434/api/tags >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo [WARNING] Ollama does not appear to be running.
        echo           Start it with:  ollama serve
        echo           Make sure qwen2.5-coder:7b is pulled.
    ) else (
        echo [OK] Ollama is running.
    )
)

REM ── Done ──────────────────────────────────────────────────
echo.
echo ============================================================
echo   Setup complete! You can now run:
echo.
echo     python main.py --dry-run --debug   (preview mode)
echo     python main.py                     (full mode)
echo     python main.py --repo REPO_NAME    (single repo)
echo ============================================================
echo.
pause
