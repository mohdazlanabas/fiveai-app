import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

# static + templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# home
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# form target used by your index.html (multipart/FormData)
@app.post("/ask")
async def ask(prompt: str = Form(...)):
    # TODO: call your model backends; return shape your JS expects
    return [
        {"provider": "meta", "model": "llama-3.1", "latency_ms": 12, "ok": True, "text": "demo"},
    ]

# health probe
@app.get("/healthz")
def healthz():
    return {"ok": True}

# local run (Cloud Run uses Dockerfile CMD below)
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
