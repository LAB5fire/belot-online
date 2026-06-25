"""
HTTP + WebSocket routes for online 3-player Belot rooms.

  POST /api/rooms              -> create a room (returns code + private token)
  POST /api/rooms/{code}/join  -> join a room (returns seat + private token)
  WS   /ws/{code}?token=...    -> live game channel for one player
"""
from __future__ import annotations
import asyncio
from typing import Dict

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from ...rooms.room_manager import room_manager, Room

router = APIRouter()


class CreateRoomRequest(BaseModel):
    name: str


class JoinRoomRequest(BaseModel):
    name: str


@router.post("/api/rooms")
async def create_room(req: CreateRoomRequest):
    return room_manager.create_room(req.name)


@router.post("/api/rooms/{code}/join")
async def join_room(code: str, req: JoinRoomRequest):
    try:
        return room_manager.join_room(code.upper(), req.name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------------------- #
# WebSocket connection manager                                            #
# ---------------------------------------------------------------------- #

class ConnectionManager:
    """Tracks live sockets per room: code -> {seat -> WebSocket}."""

    def __init__(self) -> None:
        self.active: Dict[str, Dict[int, WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, code: str, seat: int, ws: WebSocket) -> None:
        async with self._lock:
            self.active.setdefault(code, {})[seat] = ws

    async def disconnect(self, code: str, seat: int) -> None:
        async with self._lock:
            seats = self.active.get(code)
            if seats and seats.get(seat) is not None:
                seats.pop(seat, None)
            if seats is not None and not seats:
                self.active.pop(code, None)

    async def broadcast(self, room: Room) -> None:
        seats = dict(self.active.get(room.code, {}))
        for seat, ws in seats.items():
            try:
                await ws.send_json(room_manager.state_for(room, seat))
            except Exception:
                # Drop broken sockets silently; disconnect handler cleans up.
                pass


manager = ConnectionManager()


@router.websocket("/ws/{code}")
async def game_socket(websocket: WebSocket, code: str):
    code = code.upper()
    token = websocket.query_params.get("token", "")

    room = room_manager.get_room(code)
    player = room.player_by_token(token) if room else None
    if room is None or player is None:
        await websocket.close(code=4404)
        return

    await websocket.accept()
    await manager.connect(code, player.seat, websocket)
    player.connected = True
    await manager.broadcast(room)

    try:
        while True:
            message = await websocket.receive_json()
            try:
                room_manager.apply_action(room, player, message)
            except ValueError as e:
                await websocket.send_json({"type": "error", "message": str(e)})
                continue
            await manager.broadcast(room)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        await manager.disconnect(code, player.seat)
        player.connected = False
        # Tell whoever is left that this player dropped.
        try:
            await manager.broadcast(room)
        except Exception:
            pass
        # Clean up rooms nobody is connected to anymore.
        if room.code not in manager.active and not any(
            p.connected for p in room.players.values()
        ):
            room_manager.remove_room(room.code)
