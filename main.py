from fastapi import FastAPI, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Create FastAPI app
app = FastAPI()

# Mount static folder (for CSS, JS, images)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# Set up templates folder
templates = Jinja2Templates(directory=BASE_DIR / "templates")


# Root endpoint → renders index.html
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# Form handler for the /ask endpoint
@app.post("/ask")
async def handle_ask(prompt: str = Form(...)):
    """
    This endpoint receives a prompt and should eventually query
    the five GPT models. For now, it returns mock data.
    """
    # This is where you would add the logic to call the AI models.
    # For now, we'll return some fake data that matches the frontend's expectations.
    mock_responses = [
        {"provider": "OpenAI", "model": "GPT-4", "latency_ms": 543, "ok": True, "text": f"Response for '{prompt}' from GPT-4."},
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
