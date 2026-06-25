"""Tests for the room manager and HTTP room endpoints."""
import random

import pytest

from app.rooms.room_manager import RoomManager
from app.game_engine.game import GamePhase


def make_full_room(rm: RoomManager):
    a = rm.create_room("Alice")
    b = rm.join_room(a["code"], "Bob")
    c = rm.join_room(a["code"], "Cara")
    room = rm.get_room(a["code"])
    players = {p.seat: p for p in room.players.values()}
    return room, players, (a, b, c)


class TestLobby:
    def test_create_and_join_assigns_seats(self):
        rm = RoomManager()
        room, players, (a, b, c) = make_full_room(rm)
        assert a["seat"] == 0 and b["seat"] == 1 and c["seat"] == 2
        assert len(room.players) == 3

    def test_room_full_rejected(self):
        rm = RoomManager()
        room, _, (a, _, _) = make_full_room(rm)
        with pytest.raises(ValueError, match="full"):
            rm.join_room(a["code"], "Dan")

    def test_join_unknown_room(self):
        rm = RoomManager()
        with pytest.raises(ValueError, match="not found"):
            rm.join_room("ZZZZ", "Nobody")

    def test_only_host_starts_and_needs_three(self):
        rm = RoomManager()
        a = rm.create_room("Alice")
        rm.join_room(a["code"], "Bob")
        room = rm.get_room(a["code"])
        host = room.players[0]
        bob = room.players[1]
        # Not enough players yet.
        with pytest.raises(ValueError, match="3 players"):
            rm.start_game(room, host)
        rm.join_room(a["code"], "Cara")
        # Non-host cannot start.
        with pytest.raises(ValueError, match="host"):
            rm.apply_action(room, bob, {"action": "start"})
        rm.apply_action(room, host, {"action": "start"})
        assert room.status == "playing" and room.game is not None


class TestActions:
    def test_wrong_turn_rejected(self):
        rm = RoomManager()
        room, players, _ = make_full_room(rm)
        rm.apply_action(room, players[0], {"action": "start"})
        g = room.game
        wrong = (g.current_player + 1) % 3
        with pytest.raises(ValueError, match="turn"):
            rm.apply_action(room, players[wrong], {"action": "bid", "game_type": None})

    def test_full_game_via_actions(self):
        rm = RoomManager()
        room, players, _ = make_full_room(rm)
        rm.apply_action(room, players[0], {"action": "start"})
        random.seed(5)
        guard = 0
        while room.status != "finished":
            guard += 1
            assert guard < 6000
            g = room.game
            p = g.current_player
            if g.phase == GamePhase.BIDDING:
                if g.current_bid is None and random.random() < 0.7:
                    gt = random.choice(g.available_bids).value
                    rm.apply_action(room, players[p], {"action": "bid", "game_type": gt})
                else:
                    rm.apply_action(room, players[p], {"action": "bid", "game_type": None})
            elif g.phase == GamePhase.PLAYING:
                card = random.choice(g.get_legal_moves(p)).to_dict()
                rm.apply_action(room, players[p], {"action": "play", "card": card})
            else:
                break
        assert room.status == "finished"
        assert room.game.to_dict()["winner"] is not None

    def test_state_for_sets_your_seat(self):
        rm = RoomManager()
        room, players, _ = make_full_room(rm)
        st = rm.state_for(room, 1)
        assert st["type"] == "state"
        assert st["room"]["your_seat"] == 1
        assert st["room"]["status"] == "lobby"
        assert st["game"] is None


class TestHttp:
    def test_create_and_join_endpoints(self, client):
        r = client.post("/api/rooms", json={"name": "Alice"})
        assert r.status_code == 200
        data = r.json()
        assert "code" in data and "token" in data and data["seat"] == 0

        j = client.post(f"/api/rooms/{data['code']}/join", json={"name": "Bob"})
        assert j.status_code == 200
        assert j.json()["seat"] == 1

    def test_join_missing_room_returns_400(self, client):
        r = client.post("/api/rooms/ZZZZ/join", json={"name": "Bob"})
        assert r.status_code == 400

    def test_health(self, client):
        assert client.get("/health").json() == {"status": "ok"}
