from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import os

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return """
    <!DOCTYPE html>
    <html>
      <head>
        <title>FiveAI App</title>
        <link rel="stylesheet" href="/static/styles.css">
      </head>
      <body>
        <h1>🚀 FiveAI App is running on Cloud Run!</h1>
        <p>This app is served with FastAPI + Uvicorn.</p>
      </body>
    </html>
    """

# This allows local testing and Cloud Run deployment
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))  # Cloud Run injects PORT
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
