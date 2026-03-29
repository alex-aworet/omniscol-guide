#!/usr/bin/env python3
"""
FastAPI server for Omniscol application
Serves static files and provides API endpoints
"""
from fastapi import FastAPI, Request, HTTPException, WebSocket
from fastapi.responses import JSONResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import socketio
import os
import json
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("omniscol")

# Initialize Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=False,  # Disable Socket.IO logging
    engineio_logger=False,  # Disable Engine.IO logging
    ping_interval=25,  # Send ping every 25 seconds
    ping_timeout=60  # Wait 60 seconds for pong before disconnecting
)

# Initialize FastAPI app
app = FastAPI(
    title="Omniscol API",
    description="API for Omniscol school management system",
    version="1.0.0"
)

# Wrap FastAPI app with Socket.IO
socket_app = socketio.ASGIApp(sio, app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get base directory
BASE_DIR = Path(__file__).resolve().parent


@app.middleware("http")
async def filter_logging(request: Request, call_next):
    """Filter out noisy log entries and handle Socket.IO WebSocket upgrades"""
    
    # Handle Socket.IO WebSocket upgrade requests
    if request.url.path.startswith('/socket.io'):
        # Check if it's a WebSocket upgrade request
        if request.headers.get("upgrade", "").lower() == "websocket":
            # Return 404 for Socket.IO WebSocket connections to prevent them
            return Response(
                status_code=404,
                content="WebSocket endpoint not available",
                headers={
                    "Connection": "close",
                }
            )
    
    response = await call_next(request)
    
    # Don't log socket.io, favicon, font requests, or CDN rum
    if not any(x in str(request.url.path) for x in ['/socket.io', '/public/images/favicon.png', '/public/fonts/fontawesome/', '/cdn-cgi/rum']):
        logger.info(f"{request.method} {request.url.path} - {response.status_code}")
    
    return response


# Socket.IO event handlers
@sio.event
async def connect(sid, environ):
    """Handle Socket.IO client connection - keep it alive"""
    logger.info(f"Socket.IO client connected: {sid}")
    # Don't disconnect - let the connection stay open for the frontend


@sio.event
async def disconnect(sid):
    """Handle Socket.IO client disconnection"""
    logger.warning(f"Socket.IO client disconnected: {sid} - This should not happen frequently")


@sio.event
async def message(sid, data):
    """Handle Socket.IO messages - ignore them"""
    pass


# Catch-all for any other Socket.IO events
@sio.on('*')
async def catch_all(event, sid, data):
    """Catch-all handler for any Socket.IO events"""
    pass


@app.post("/cdn-cgi/rum")
async def cloudflare_rum():
    """Accept Cloudflare RUM requests silently"""
    return JSONResponse({"success": True})


@app.post("/api/guest/login")
async def guest_login(request: Request):
    """Mock login endpoint - returns pre-authenticated user"""
    return JSONResponse({
        "success": True,
        "user": {
            "id": "kristale-mayila",
            "login": "kristale.mayila",
            "name": {"first_name": "Kristale", "last_name": "Mayila"},
            "roles": ["admin"]
        }
    })


@app.get("/api/user/keep-alive")
async def keep_alive():
    """Keep-alive endpoint to maintain session"""
    return JSONResponse({"success": True, "alive": True})


@app.get("/api/user/ping")
async def ping():
    """Ping endpoint to check session status"""
    return JSONResponse({"success": True, "pong": True})


@app.get("/api/{path:path}")
async def api_get_handler(path: str):
    """Handle GET requests to API endpoints"""
    # Try to find corresponding .html file
    api_file = f"api/{path}"
    if not api_file.endswith('.html'):
        api_file = api_file.rstrip('/') + '.html'
    
    file_path = BASE_DIR / api_file
    
    if file_path.exists() and file_path.is_file():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Special handling for endpoints configuration to disable Socket.IO
            if 'guest/endpoints' in path:
                try:
                    data = json.loads(content)
                    # Disable collaboration/Socket.IO features to prevent connection attempts
                    if 'config' in data and isinstance(data['config'], dict):
                        data['config']['collab'] = False
                    content = json.dumps(data)
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Could not modify endpoints config: {e}")
            
            return Response(
                content=content,
                media_type="application/json; charset=utf-8"
            )
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    # Return mock responses based on endpoint type
    if '/admin/teachers' in path:
        return JSONResponse({"success": True, "teachers": []})
    elif '/admin/' in path:
        return JSONResponse({"success": True, "data": []})
    else:
        return JSONResponse({"success": True, "message": "Mock response - endpoint not found"})


@app.post("/api/{path:path}")
async def api_post_handler(path: str, request: Request):
    """Handle POST requests to API endpoints"""
    # Return mock responses for POST requests
    return JSONResponse({"success": True, "message": "Mock response"})


@app.get("/i18n/{path:path}")
async def i18n_handler(path: str):
    """Handle i18n requests - serve HTML files as JSON"""
    i18n_file = f"i18n/{path}"
    if not i18n_file.endswith('.html'):
        i18n_file = i18n_file.rstrip('/') + '.html'
    
    file_path = BASE_DIR / i18n_file
    
    if file_path.exists() and file_path.is_file():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return Response(
                content=content,
                media_type="application/json; charset=utf-8"
            )
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    raise HTTPException(status_code=404, detail="Translation file not found")


@app.get("/public/images/{path:path}")
async def missing_images(path: str):
    """Handle missing image files"""
    return Response(status_code=204)


@app.get("/public/fonts/{path:path}")
async def missing_fonts(path: str):
    """Handle missing font files"""
    return Response(status_code=204)


@app.get("/")
async def root():
    """Serve index.html at root"""
    index_path = BASE_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="Index file not found")


# Mount static files - this should be last to not override specific routes
# Mount webapp directory
if (BASE_DIR / "webapp").exists():
    app.mount("/webapp", StaticFiles(directory=str(BASE_DIR / "webapp")), name="webapp")

# Mount public directory
if (BASE_DIR / "public").exists():
    app.mount("/public", StaticFiles(directory=str(BASE_DIR / "public")), name="public")

# Mount app directory
if (BASE_DIR / "app").exists():
    app.mount("/app", StaticFiles(directory=str(BASE_DIR / "app")), name="app")

# Mount core directory
if (BASE_DIR / "core").exists():
    app.mount("/core", StaticFiles(directory=str(BASE_DIR / "core")), name="core")


if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Serveur FastAPI démarré")
    print(f"📁 Répertoire: {BASE_DIR}")
    print(f"🌐 Application: http://localhost:8001")
    print(f"📚 Documentation API: http://localhost:8001/docs")
    print(f"🔧 ReDoc: http://localhost:8001/redoc")
    print("\nAppuyez sur Ctrl+C pour arrêter le serveur\n")
    
    uvicorn.run(
        socket_app,  # Use socket_app instead of "main:app"
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
