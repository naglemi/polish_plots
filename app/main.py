# Main FastAPI application

from fastapi import FastAPI, WebSocket, Request, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
import os
from pathlib import Path

# Determine the base directory of the main.py script
BASE_DIR = Path(__file__).resolve().parent

app = FastAPI()

# Mount static files (CSS, JS) - relative to this script's directory
app.mount("/static", StaticFiles(directory=BASE_DIR.parent / "static"), name="static")

# Use Jinja2Templates to serve the HTML file - relative to this script's directory
templates = Jinja2Templates(directory=BASE_DIR.parent / "static")

# Connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# HTTP endpoint to serve the chat page
@app.get("/", response_class=HTMLResponse)
async def get_chat_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # For now, just broadcast messages received from any client
            # We'll add sender info and agent logic later
            await manager.broadcast(data) # Broadcast the raw JSON string
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        # Optionally broadcast a disconnect message
        # await manager.broadcast(json.dumps({"sender": "System", "text": "A user disconnected"}))
    except Exception as e:
        print(f"WebSocket Error: {e}")
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    # Run on localhost, port 8081 for example, distinct from Roo's 8000
    uvicorn.run(app, host="0.0.0.0", port=8081)
