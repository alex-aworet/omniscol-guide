# app/main.py
import socketio
from fastapi import FastAPI

# Socket.IO server
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",  # allow frontend
)

# FastAPI app
app = FastAPI()

# Combine both
socket_app = socketio.ASGIApp(
    sio,
    other_asgi_app=app,
)

# Socket.IO events
@sio.event
async def connect(sid, environ):
    print("✅ Socket connected:", sid)

@sio.event
async def disconnect(sid):
    print("❌ Socket disconnected:", sid)
