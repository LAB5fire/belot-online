"""
In-memory room manager for online 3-player Belot.

A room holds up to three human players (seats 0, 1, 2) identified by a private
token. The host (seat 0) starts the game once three players have joined. All
game state lives here in memory — there is no database dependency, which keeps
online deployment simple. (If the server restarts, in-progress rooms are lost.)
"""
from __future__ import annotations
import secrets
import string
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..game_engine.game import BelotGame, GamePhase
from ..game_engine.card import Card, Suit, Rank, GameType

MAX_PLAYERS = 3
CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no easily-confused chars


@dataclass
class Player:
    seat: int
    name: str
    token: str
    connected: bool = False


@dataclass
class Room:
    code: str
    players: Dict[int, Player] = field(default_factory=dict)
    game: Optional[BelotGame] = None
    status: str = "lobby"  # lobby | playing | finished
    host_seat: int = 0

    def player_by_token(self, token: str) -> Optional[Player]:
        for p in self.players.values():
            if p.token == token:
                return p
        return None

    def is_full(self) -> bool:
        return len(self.players) >= MAX_PLAYERS

    def next_seat(self) -> Optional[int]:
        for s in range(MAX_PLAYERS):
            if s not in self.players:
                return s
        return None

    def public_players(self) -> List[dict]:
        return [
            {"seat": p.seat, "name": p.name, "connected": p.connected}
            for p in sorted(self.players.values(), key=lambda x: x.seat)
        ]


class RoomManager:
    def __init__(self) -> None:
        self.rooms: Dict[str, Room] = {}

    # ------------------------------------------------------------------ #
    # Room lifecycle                                                       #
    # ------------------------------------------------------------------ #

    def _new_code(self) -> str:
        while True:
            code = "".join(secrets.choice(CODE_ALPHABET) for _ in range(4))
            if code not in self.rooms:
                return code

    def create_room(self, name: str) -> dict:
        code = self._new_code()
        token = secrets.token_urlsafe(16)
        room = Room(code=code)
        room.players[0] = Player(seat=0, name=_clean_name(name), token=token)
        self.rooms[code] = room
        return {"code": code, "token": token, "seat": 0}

    def join_room(self, code: str, name: str) -> dict:
        room = self.get_room(code)
        if room is None:
            raise ValueError("Room not found")
        if room.status != "lobby":
            raise ValueError("Game already started")
        seat = room.next_seat()
        if seat is None:
            raise ValueError("Room is full")
        token = secrets.token_urlsafe(16)
        room.players[seat] = Player(seat=seat, name=_clean_name(name), token=token)
        return {"code": code, "token": token, "seat": seat}

    def get_room(self, code: str) -> Optional[Room]:
        return self.rooms.get((code or "").upper())

    def remove_room(self, code: str) -> None:
        self.rooms.pop(code, None)

    # ------------------------------------------------------------------ #
    # Game actions (all validated against the acting player's seat)        #
    # ------------------------------------------------------------------ #

    def start_game(self, room: Room, player: Player) -> None:
        if player.seat != room.host_seat:
            raise ValueError("Only the host can start the game")
        if len(room.players) < MAX_PLAYERS:
            raise ValueError("Need 3 players to start")
        if room.status != "lobby":
            raise ValueError("Game already started")
        room.game = BelotGame()
        room.status = "playing"

    def apply_action(self, room: Room, player: Player, message: dict) -> None:
        action = message.get("action")

        if action == "start":
            self.start_game(room, player)
            return

        game = room.game
        if game is None:
            raise ValueError("Game has not started")

        if action == "bid":
            if game.phase != GamePhase.BIDDING:
                raise ValueError("Not in bidding phase")
            if game.current_player != player.seat:
                raise ValueError("Not your turn to bid")
            gt_raw = message.get("game_type")
            gt = GameType(gt_raw) if gt_raw else None
            game.place_bid(player.seat, gt)
            # Bidding may have finished — reveal declarations and move to play.
            if game.phase == GamePhase.DECLARATIONS:
                game.reveal_declarations()

        elif action == "play":
            if game.phase != GamePhase.PLAYING:
                raise ValueError("Not in playing phase")
            if game.current_player != player.seat:
                raise ValueError("Not your turn to play")
            card_raw = message.get("card") or {}
            try:
                card = Card(Suit(card_raw["suit"]), Rank(card_raw["rank"]))
            except (KeyError, ValueError):
                raise ValueError("Invalid card")
            game.play_card(player.seat, card)

        else:
            raise ValueError(f"Unknown action: {action}")

        if game.phase == GamePhase.FINISHED:
            room.status = "finished"

    # ------------------------------------------------------------------ #
    # State serialization for clients                                      #
    # ------------------------------------------------------------------ #

    def state_for(self, room: Room, seat: int) -> dict:
        return {
            "type": "state",
            "room": {
                "code": room.code,
                "status": room.status,
                "host_seat": room.host_seat,
                "your_seat": seat,
                "players": room.public_players(),
                "max_players": MAX_PLAYERS,
            },
            "game": room.game.to_dict(viewer=seat) if room.game else None,
        }


def _clean_name(name: str) -> str:
    name = (name or "").strip()[:20]
    return name or "Player"


# Module-level singleton used by the API routes.
room_manager = RoomManager()
