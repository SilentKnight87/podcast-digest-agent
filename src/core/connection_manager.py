from fastapi import WebSocket
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Stores active connections: task_id -> list of WebSockets
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, task_id: str):
        """Accepts a new WebSocket connection and associates it with a task_id."""
        await websocket.accept()
        if task_id not in self.active_connections:
            self.active_connections[task_id] = []
        self.active_connections[task_id].append(websocket)
        logger.info(f"WebSocket {websocket.client} connected for task_id: {task_id}")

    def disconnect(self, websocket: WebSocket, task_id: str):
        """Removes a WebSocket connection upon disconnection."""
        if task_id in self.active_connections:
            if websocket in self.active_connections[task_id]:
                self.active_connections[task_id].remove(websocket)
                logger.info(f"WebSocket {websocket.client} disconnected for task_id: {task_id}")
                if not self.active_connections[task_id]: # Clean up task_id if no more connections
                    del self.active_connections[task_id]
                    logger.info(f"No more connections for task_id: {task_id}, removing from manager.")
            else:
                logger.warning(f"WebSocket {websocket.client} not found in task_id {task_id} during disconnect.")
        else:
            logger.warning(f"Task_id {task_id} not found in active_connections during disconnect for {websocket.client}.")

    async def broadcast_to_task(self, task_id: str, message_data: dict):
        """Broadcasts a JSON message to all WebSockets connected for a specific task_id."""
        if task_id in self.active_connections:
            disconnected_sockets: List[WebSocket] = []
            for connection in self.active_connections[task_id]:
                try:
                    await connection.send_json(message_data)
                except Exception as e: # Covers WebSocketDisconnect and other potential errors
                    logger.error(f"Error sending message to WebSocket {connection.client} for task {task_id}: {e}")
                    # Mark for disconnection if send fails, to avoid repeated errors
                    disconnected_sockets.append(connection)
            
            # Clean up sockets that failed to send (likely disconnected)
            for sock_to_remove in disconnected_sockets:
                self.disconnect(sock_to_remove, task_id)
        else:
            logger.debug(f"No active WebSocket connections for task_id {task_id} to broadcast to.")

# Global instance of ConnectionManager
# This can be imported and used by the task_manager or directly in API endpoints.
manager = ConnectionManager() 