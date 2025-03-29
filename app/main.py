import socketio
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import datetime

# --- Configuration ---
templates = Jinja2Templates(directory="templates")

# --- Data Store (Simple in-memory list) ---
messages_store = []

# --- Pydantic Models ---
class MessageBase(BaseModel):
    sender: str
    text: str

class MessageIn(MessageBase):
    pass

class MessageOut(MessageBase):
    timestamp: datetime.datetime

# --- FastAPI App ---
app = FastAPI(title="AGNTCY Chat API")
app.mount("/static", StaticFiles(directory="../static"), name="static") # Mount static files

# --- Socket.IO Server ---
# async_mode='asgi' is important for FastAPI integration
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
# Wrap FastAPI app with Socket.IO middleware
asgi_app = socketio.ASGIApp(sio, app)

# --- Socket.IO Event Handlers ---
@sio.event
async def connect(sid, environ):
    print(f'Client connected: {sid}')
    # Optionally send existing messages to newly connected client
    # You might want to send the whole history or just the last N messages
    if messages_store:
        # Send only the last 50 messages, for example
        recent_messages = messages_store[-50:]
        for msg_data in recent_messages:
             await sio.emit('chat_message', msg_data, room=sid)

@sio.event
async def disconnect(sid):
    print(f'Client disconnected: {sid}')

@sio.event
async def chat_message(sid, data):
    """Handles messages received via WebSocket from clients (browsers)."""
    print(f'Message from {sid}: {data}')
    # Assume data is just the message text from the browser client for now
    # We might enhance this later to include sender info from the browser session
    message_data = {
        "sender": f"User_{sid[:4]}", # Simple anonymous user ID for now
        "text": data,
        "timestamp": datetime.datetime.now()
    }
    messages_store.append(message_data)
    # Limit stored messages (optional)
    if len(messages_store) > 100:
        messages_store.pop(0)

    # Broadcast the message to all connected clients, including the sender
    # Use sio.emit for broadcasting to all
    await sio.emit('chat_message', message_data)


# --- FastAPI HTTP Endpoints ---
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serves the main chat HTML page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/send", response_model=MessageOut)
async def send_message_api(message: MessageIn):
    """API endpoint for agents (or other services) to send messages."""
    print(f'API Message from {message.sender}: {message.text}')
    message_data = {
        "sender": message.sender,
        "text": message.text,
        "timestamp": datetime.datetime.now().isoformat() # Use ISO format for JSON
    }
    messages_store.append(message_data)
    # Limit stored messages (optional)
    if len(messages_store) > 100:
        messages_store.pop(0)

    # Broadcast via Socket.IO to update web clients
    await sio.emit('chat_message', message_data)
    # Convert datetime back for Pydantic model if needed, or adjust model
    message_data["timestamp"] = datetime.datetime.fromisoformat(message_data["timestamp"])
    return message_data # Return the processed message including timestamp

@app.get("/messages", response_model=list[MessageOut])
async def get_messages_api():
    """API endpoint for agents to retrieve all messages."""
    # Ensure timestamps are datetime objects for the response model
    response_data = []
    for msg in messages_store:
        # Ensure timestamp is datetime object before adding
        if isinstance(msg.get("timestamp"), str):
            msg_copy = msg.copy()
            msg_copy["timestamp"] = datetime.datetime.fromisoformat(msg["timestamp"])
            response_data.append(msg_copy)
        else:
             response_data.append(msg)
    return response_data

# --- Run (for local testing) ---
if __name__ == '__main__':
    # Note: Run with the ASGI app wrapper, not the raw FastAPI app
    # Reload=True is useful for development
    uvicorn.run("main:asgi_app", host='0.0.0.0', port=8081, reload=True)
