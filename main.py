import os, time, asyncio
from typing import Any, Dict, List
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

MODELS = [
    # model_id,                   pretty provider, pretty model
    ("openai/gpt-4o-mini",        "OpenAI",        "GPT-4o-Mini"),
    ("anthropic/claude-3.5-sonnet","Anthropic",     "Claude-3.5-Sonnet"),
    ("google/gemini-1.5-flash",    "Google",        "Gemini-1.5-Flash"),
    ("deepseek/deepseek-chat",     "Deepseek",      "Deepseek-Chat"),
    ("meta-llama/llama-3.1-8b-instruct","Meta",    "Llama-3.1-8B"),
]

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

async def call_model(client: httpx.AsyncClient, model_id: str, provider: str, label: str, prompt: str) -> Dict[str, Any]:
    start = time.perf_counter()
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://ai-fivecheck",    # optional but recommended by OpenRouter
            "X-Title": "AI Five-Check",
        }
        payload = {
            "model": model_id,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 256,
            "temperature": 0.7,
        }
        r = await client.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
        latency_ms = int((time.perf_counter() - start) * 1000)
        if r.status_code != 200:
            return {"provider": provider, "model": label, "latency_ms": latency_ms, "ok": False, "text": f"HTTP {r.status_code}: {r.text[:400]}"}
        data = r.json()
        text = (data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")) or ""
        return {"provider": provider, "model": label, "latency_ms": latency_ms, "ok": True, "text": text.strip()}
    except Exception as e:
        latency_ms = int((time.perf_counter() - start) * 1000)
        return {"provider": provider, "model": label, "latency_ms": latency_ms, "ok": False, "text": f"Error: {e}"}

@app.post("/ask")
async def ask(prompt: str = Form(...)):
    if not OPENROUTER_API_KEY:
        # Surface a clear error card in the UI if the key is missing
        return JSONResponse([
            {"provider": "Config", "model": "Env", "latency_ms": 0, "ok": False, "text": "OPENROUTER_API_KEY is not set in the service environment."}
        ], status_code=200)

    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(*[
            call_model(client, m[0], m[1], m[2], prompt) for m in MODELS
        ])
    return results

@app.get("/healthz")
def healthz():
    return {"ok": True}
