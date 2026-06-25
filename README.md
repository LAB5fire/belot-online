# Belot Online (3 Players)

A full-stack web app for playing **3-player Bulgarian Belot** online with
friends. One person creates a room, shares a 4-letter code, and three humans
play live in their browsers — synchronized in real time over WebSockets. No
bots, no database.

> Previously this was a single-player game against AI bots. That AI code is kept
> on disk under `backend/app/ai/` (and `analyzer/`, `services/game_service.py`,
> etc.) but is **no longer wired into the app**. See "Set aside" below.

## Quick Start (local)

No database required.

```bash
# Backend (port 8000)
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
#   …or from the repo root:  docker compose up --build

# Frontend (port 3000) — second terminal
cd frontend
npm install
npm run dev
```

Open **three** browser windows/profiles at http://localhost:3000:
one **Create Room**, two **Join** with the code, host clicks **Start**.

- **Frontend**: http://localhost:3000
- **Backend API / docs**: http://localhost:8000 · http://localhost:8000/docs

## Deploy online

A `render.yaml` blueprint deploys the backend (FastAPI + WebSockets) and the
frontend (static site) to [Render](https://render.com) and wires them together.
See **[DEPLOY.md](DEPLOY.md)** for the walkthrough (and Railway/Fly.io notes).

## The 3-player variant

- **24-card deck** — ranks **9, 10, J, Q, K, A** (the 7s and 8s are removed).
  Since 7/8 are worth 0 points, all point totals match standard Belot.
- **3 players, every player for themselves** (no teams).
- **Deal 3-2-(bid)-3**: five cards each, bidding on the five-card hand, then the
  final three cards → 8 cards each, all 24 dealt (no talon).
- **8 tricks per round**, 3 cards per trick.
- **Bidding**: ♣ < ♦ < ♥ < ♠ < No Trump < All Trump. The bid winner sets the
  trump/game type.
- **Scoring (pure individual)**: each player banks their own card points + own
  declarations + own belot each round; +10 for the last trick; a valat bonus for
  taking all 8 tricks. **First player to 151 wins.** The scoring rules are
  isolated in `backend/app/game_engine/scoring.py` and
  `declarations.py` for easy house-rule tweaks.

### Card values

| Situation | J | 9 | A | 10 | K | Q |
|-----------|---|---|---|----|---|---|
| Trump / All Trump | 20 | 14 | 11 | 10 | 4 | 3 |
| Non-trump / No Trump | 2 | 0 | 11 | 10 | 4 | 3 |

## Architecture

```
belot-analyzer/
├── render.yaml              # Render blueprint (backend + frontend)
├── DEPLOY.md                # Deployment guide
├── docker-compose.yml       # Local backend container
├── backend/
│   └── app/
│       ├── game_engine/     # 3-player rules (deck, rules, scoring, game state)
│       ├── rooms/           # RoomManager: codes, seats, tokens (in-memory)
│       ├── api/routes/room.py  # POST /api/rooms, /join, WS /ws/{code}
│       ├── core/config.py   # CORS settings
│       └── ai/, analyzer/, services/, models/, repositories/  # set aside
└── frontend/
    └── src/
        ├── pages/           # HomePage, LobbyPage, GamePage
        ├── components/      # table, hands, bidding, scoreboard…
        ├── store/           # Zustand + WebSocket client
        ├── api/             # room HTTP + ws url helpers
        └── types/
```

## API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/rooms` | Create a room → `{code, token, seat}` |
| POST | `/api/rooms/{code}/join` | Join a room → `{code, token, seat}` |
| WS | `/ws/{code}?token=…` | Live game channel (state broadcasts + actions) |
| GET | `/health` | Health check |

**WebSocket messages** — client → server: `{action: "start" | "bid" | "play",
…}`. Server → all clients: `{type: "state", room, game}` (each client receives a
per-seat view that hides other players' cards); errors go to the sender as
`{type: "error", message}`.

## Tests

```bash
cd backend
pip install -r requirements.txt
pytest -q          # 3-player engine + room manager + HTTP endpoints
```

## Set aside (kept, not deleted)

Per design, the former AI/analysis stack remains on disk but is **not imported**
by the running app, so there is no dependency on it or on a database:

- `backend/app/ai/` (bots, Monte Carlo, heuristics)
- `backend/app/analyzer/`, `backend/app/services/`, `backend/app/repositories/`,
  `backend/app/models/`, `backend/app/core/database.py`
- the old `game`/`analysis`/`stats` routes and their schemas

To re-enable any of it, re-add the relevant router in
`backend/app/api/routes/__init__.py`.

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `CORS_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | Allowed frontend origin(s). Comma-separated; bare hostnames and `*` accepted. |
| `VITE_API_BASE` | _(empty → dev proxy)_ | Frontend build-time backend URL/host for production. |
