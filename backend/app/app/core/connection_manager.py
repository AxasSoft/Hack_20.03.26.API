from typing import List, Dict

import logging
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id):
        await websocket.accept()
        if user_id in self.active_connections:
            self.active_connections[user_id].append(websocket)
        else:
            self.active_connections[user_id] = [websocket]

    def disconnect(self, websocket: WebSocket):
        for user_id, ws_list in self.active_connections.items():
            if websocket in ws_list:
                self.active_connections[user_id].remove(websocket)

    async def send_personal_message(self, message: str, user_id):
        for websocket in self.active_connections.get(user_id,[]):
            await websocket.send_text(message)

    async def broadcast(self, message: str):
        for user_id, connection_list in self.active_connections.items():
            for connection in connection_list:
                await connection.send_text(message)
