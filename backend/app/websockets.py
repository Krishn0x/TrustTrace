from fastapi import WebSocket, WebSocketDisconnect
import json
import logging
import datetime
from typing import List

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast_event(self, event_type: str, data: dict):
        event = {
            "type": event_type,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "data": data
        }
        message = json.dumps(event)
        
        # Create a list of connections to remove if sending fails
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                dead_connections.append(connection)
                
        for connection in dead_connections:
            self.disconnect(connection)

manager = ConnectionManager()
