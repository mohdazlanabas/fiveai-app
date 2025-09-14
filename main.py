import os
import time
import asyncio
from typing import Dict, Any
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx
from dotenv import load_dotenv

# ---------- Config & Boot ----------

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
APP_URL = os.getenv("APP_URL", "http://localhost:8000")
if not OPENROUTER_API_KEY:
    raise RuntimeError("Missing OPENROUTER_API_KEY in .env")

# Cheaper / free-tier friendlier variants
TARGET_MODELS = [
    {"provider": "OpenAI (ChatGPT)",  "model": "openai/gpt-4o-mini"},
    {"provider": "Google (Gemini)",   "model": "google/gemini-2.5-pro"},
    {"provider": "Anthropic (Claude)","model": "anthropic/claude-3.5-haiku"},
    {"provider": "DeepSeek",          "model": "deepseek/deepseek-chat"},
    {"provider": "Meta (Llama)",      "model": "meta-llama/llama-3.1-8b-instruct"},
]

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "HTTP-Referer": APP_URL,    # recommended by OpenRouter
    "X-Title": "AI Five-Check", # optional label
}

# Default token budgets (You can tweak per model here)
DEFAULT_MAX_TOKENS = 512
MIN_MAX_TOKENS = 128
PER_MODEL_MAX = {
    "openai/gpt-4o-mini": 384,
    "google/gemini-1.5-flash": 384,
    "anthropic/claude-3.5-haiku": 320,
    "deepseek/deepseek-chat": 512,
    "meta-llama/llama-3.1-8b-instruct": 512,
}

# ---------- App ----------

app = FastAPI()

# Static & templates
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# ---------- Helpers ----------

def choose_budget(prompt: str, model_id: str) -> int:
    """Estimate a safe output token budget, clamped by per-model caps."""
    # very rough token estimate: ~4 chars/token
    approx_input_tokens = max(1, len(prompt) // 4)
    base = min(DEFAULT_MAX_TOKENS, max(256, 1024 - approx_input_tokens))
    cap = PER_MODEL_MAX.get(model_id, DEFAULT_MAX_TOKENS)
    return min(base, cap)

async def call_once(prompt: str, model_id: str, max_toks: int) -> tuple[httpx.Response, int]:
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": max_toks,
    }
    t0 = time.perf_counter()
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(OPENROUTER_URL, headers=HEADERS, json=payload)
    latency_ms = int((time.perf_counter() - t0) * 1000)
    return resp, latency_ms

async def call_model(prompt: str, model_id: str) -> Dict[str, Any]:
    """Call one model with retries for HTTP 402 (credit/token budget)."""
    max_tokens = choose_budget(prompt, model_id)

    # retry loop for 402 only
    while True:
        resp, latency_ms = await call_once(prompt, model_id, max_tokens)
        if resp.status_code != 402:
            break
        # halve and retry until floor
        max_tokens //= 2
        if max_tokens < MIN_MAX_TOKENS:
            # can't go lower; return helpful message
            return {
                "model": model_id,
                "ok": False,
                "text": ("Insufficient credits for this model at current limits. "
                         "Try a shorter question, or switch to a cheaper variant, "
                         "or add credits in OpenRouter."),
                "latency_ms": latency_ms,
            }

    if resp.status_code >= 400:
        # Show trimmed error body for the card
        return {
            "model": model_id,
            "ok": False,
            "text": f"HTTP {resp.status_code}: {resp.text[:400]}",
            "latency_ms": latency_ms,
        }

    data = resp.json()
    text = (
        data.get("choices", [{}])[0]
            .get("message", {})
            .get("content")
    )
    if not text:
        text = str(data)[:800]

    return {"model": model_id, "ok": True, "text": text, "latency_ms": latency_ms}

# ---------- Routes ----------

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/ask")
async def ask(prompt: str = Form(...)):
    if not prompt.strip():
        raise HTTPException(status_code=400, detail="Empty prompt")
    tasks = [call_model(prompt, m["model"]) for m in TARGET_MODELS]
    results = await asyncio.gather(*tasks)
    # attach provider labels for UI
    pretty = []
    for meta, res in zip(TARGET_MODELS, results):
        res["provider"] = meta["provider"]
        pretty.append(res)
    return JSONResponse(pretty)

