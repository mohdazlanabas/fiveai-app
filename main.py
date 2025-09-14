from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

# Create FastAPI app
app = FastAPI()

# Mount static folder (for CSS, JS, images)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up templates folder
templates = Jinja2Templates(directory="templates")


# Root endpoint → renders index.html
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# Example form handler (if your index.html has a form)
@app.post("/submit", response_class=HTMLResponse)
async def handle_form(request: Request, user_input: str = Form(...)):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "message": f"You submitted: {user_input}"}
    )


# Simple health check
@app.get("/healthz")
async def health_check():
    return {"status": "ok"}
