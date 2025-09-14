from fastapi import FastAPI, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import time
from openai import AsyncOpenAI

BASE_DIR = Path(__file__).resolve().parent

# Create FastAPI app
app = FastAPI()

# Mount static folder (for CSS, JS, images)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# Set up templates folder
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# Initialize OpenAI client (it will read the API key from the environment)
client = AsyncOpenAI()

# Root endpoint → renders index.html
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


async def query_openai(prompt: str):
    """Queries the OpenAI API and returns a structured response."""
    start_time = time.time()
    try:
        completion = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
        )
        latency_ms = int((time.time() - start_time) * 1000)
        return {
            "provider": "OpenAI",
            "model": "GPT-3.5-Turbo",
            "latency_ms": latency_ms,
            "ok": True,
            "text": completion.choices[0].message.content,
        }
    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        return {
            "provider": "OpenAI",
            "model": "GPT-3.5-Turbo",
            "latency_ms": latency_ms,
            "ok": False,
            "text": f"Error: {e}",
        }

# Form handler for the /ask endpoint
@app.post("/ask")
async def handle_ask(prompt: str = Form(...)):
    openai_response = await query_openai(prompt)

    mock_responses = [
        openai_response,  # Use the real response here
        {"provider": "Google", "model": "Gemini", "latency_ms": 480, "ok": True, "text": f"Response for '{prompt}' from Gemini."},
        {"provider": "Anthropic", "model": "Claude", "latency_ms": 610, "ok": True, "text": f"Response for '{prompt}' from Claude."},
        {"provider": "Mistral", "model": "Mixtral", "latency_ms": 450, "ok": True, "text": f"Response for '{prompt}' from Mixtral."},
        {"provider": "Meta", "model": "Llama", "latency_ms": 720, "ok": False, "text": "Error: Model failed to respond."},
    ]
    return JSONResponse(content=mock_responses)


# Simple health check
@app.get("/healthz")
async def health_check():
    return {"status": "ok"}
