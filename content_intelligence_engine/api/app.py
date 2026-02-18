"""
FastAPI Backend – v5.2 (Production Ready)

Human-first API with comprehensive error handling.
Returns structured responses with English reports.
"""

import sys
import os
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from typing import Optional

from core.pipeline import run_pipeline
from core.report_engine import generate_human_report
from core.ollama_client import check_ollama_available


app = FastAPI(
    title="Content Intelligence Engine",
    description="AI-Powered Content Strategy Generator",
    version="5.2.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Templates
templates = Jinja2Templates(directory="templates")


class AnalyzeRequest(BaseModel):
    """Request body for content analysis."""
    niche: str = Field(..., min_length=2, max_length=200,
                       description="Content topic")
    platform: str = Field(..., min_length=2, max_length=50,
                          description="Publishing platform")
    audience: str = Field(..., min_length=2, max_length=300,
                          description="Target audience")
    goal: str = Field(..., min_length=2, max_length=300,
                      description="Business objective")


class AnalyzeResponse(BaseModel):
    """Standardized API response."""
    success: bool
    human_report: Optional[str] = None
    data: Optional[dict] = None
    error: Optional[str] = None
    error_type: Optional[str] = None


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch all unhandled exceptions."""
    print("\n" + "="*70)
    print("UNHANDLED EXCEPTION")
    print("="*70)
    print(f"Type: {type(exc).__name__}")
    print(f"Message: {str(exc)}")
    traceback.print_exc()
    print("="*70 + "\n")
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "human_report": None,
            "data": None,
            "error": str(exc),
            "error_type": type(exc).__name__
        }
    )


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve main input page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
def health():
    """Health check with Ollama status."""
    ollama_ok = check_ollama_available()
    
    return {
        "status": "healthy",
        "ollama_connected": ollama_ok,
        "model": "qwen2.5-coder:7b",
        "embeddings_enabled": False,
        "version": "5.2.0"
    }


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    """
    Run full content intelligence pipeline.
    
    Returns human-readable report + technical data.
    """
    print("\n" + "="*70)
    print("ANALYZE REQUEST")
    print("="*70)
    print(f"Topic: {request.niche}")
    print(f"Platform: {request.platform}")
    print(f"Audience: {request.audience}")
    print(f"Goal: {request.goal}")
    print("="*70 + "\n")
    
    try:
        # Check Ollama first
        if not check_ollama_available():
            return AnalyzeResponse(
                success=False,
                human_report=None,
                data=None,
                error="Ollama is not running or qwen2.5-coder:7b is not installed. "
                      "Please start Ollama with: ollama serve",
                error_type="ConnectionError"
            )
        
        # Run pipeline
        result = run_pipeline(
            niche=request.niche,
            platform=request.platform,
            audience=request.audience,
            goal=request.goal,
        )
        
        # Generate human report
        try:
            human_report = generate_human_report(result)
        except Exception as report_err:
            print(f"Report generation failed: {report_err}")
            human_report = """Report generation encountered an issue. 
Please see the technical data below for complete analysis results."""
        
        print("\n" + "="*70)
        print("PIPELINE COMPLETED")
        print("="*70)
        print(f"Elapsed: {result.get('meta', {}).get('elapsed_seconds', '?')}s")
        print(f"Research samples: {result.get('meta', {}).get('research_count', '?')}")
        print("="*70 + "\n")
        
        return AnalyzeResponse(
            success=True,
            human_report=human_report,
            data=result,
            error=None,
            error_type=None
        )
    
    except ConnectionError as exc:
        print(f"\nCONNECTION ERROR: {exc}\n")
        return AnalyzeResponse(
            success=False,
            human_report=None,
            data=None,
            error=str(exc),
            error_type="ConnectionError"
        )
    
    except ValueError as exc:
        print(f"\nVALIDATION ERROR: {exc}\n")
        return AnalyzeResponse(
            success=False,
            human_report=None,
            data=None,
            error=str(exc),
            error_type="ValidationError"
        )
    
    except RuntimeError as exc:
        print(f"\nRUNTIME ERROR: {exc}\n")
        traceback.print_exc()
        return AnalyzeResponse(
            success=False,
            human_report=None,
            data=None,
            error=str(exc),
            error_type="RuntimeError"
        )
    
    except Exception as exc:
        print(f"\nUNEXPECTED ERROR: {exc}\n")
        traceback.print_exc()
        return AnalyzeResponse(
            success=False,
            human_report=None,
            data=None,
            error=f"An unexpected error occurred: {str(exc)}",
            error_type=type(exc).__name__
        )


@app.on_event("startup")
async def startup_event():
    """Verify system on startup."""
    print("\n" + "="*70)
    print("CONTENT INTELLIGENCE ENGINE v5.2")
    print("="*70)
    
    # Check Ollama
    if check_ollama_available():
        print("✓ Ollama connected (qwen2.5-coder:7b)")
    else:
        print("✗ Ollama not available")
        print("  Start with: ollama serve")
        print("  Install model: ollama pull qwen2.5-coder:7b")
    
    print("\n✓ Server ready at http://127.0.0.1:8000")
    print("✓ API endpoint: POST /api/analyze")
    print("="*70 + "\n")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
