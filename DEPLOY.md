# Deploying Belot Online

The app is two pieces:

- **Backend** — FastAPI + WebSockets (`backend/`). Holds all game state **in
  memory** (no database).
- **Frontend** — React/Vite static site (`frontend/`).

The included `render.yaml` deploys both to [Render](https://render.com) on the
free plan and wires them together automatically.

> **Note on the free plan:** free Render services sleep after ~15 minutes of
> inactivity and restart on the next request. Because rooms live in memory, a
> restart ends any game in progress. That's fine for casual play; for always-on
> hosting, upgrade the **backend** to a paid instance.

---

## Option A — Render Blueprint (recommended)

1. **Push this repo to GitHub** (or GitLab/Bitbucket).
   ```bash
   git init && git add . && git commit -m "Belot online"
   git branch -M main
   git remote add origin https://github.com/<you>/<repo>.git
   git push -u origin main
   ```
2. In the Render dashboard: **New + → Blueprint**, pick the repo. Render reads
   `render.yaml` and proposes two services: `belot-backend` and
   `belot-frontend`.
3. Click **Apply**. Render builds both. The blueprint already links them:
   - the frontend build receives `VITE_API_BASE` = the backend's host,
   - the backend's `CORS_ORIGINS` receives the frontend's host.
4. When both are **Live**, open the **belot-frontend** URL
   (`https://belot-frontend.onrender.com`). Create a room, share the 4-letter
   code with two friends, and play.

That's it — no manual environment variables.

---

## Option B — Railway / Fly.io / any host

The same two processes work anywhere:

**Backend**
- Build: `pip install -r backend/requirements.txt`
- Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT` (run from `backend/`)
- Must allow **WebSocket** connections (Railway and Fly.io do by default).
- Set env `CORS_ORIGINS` to your frontend URL (comma-separated if several),
  e.g. `CORS_ORIGINS=https://your-frontend.example.com`. A bare host like
  `your-frontend.example.com` is also accepted (promoted to `https://`).

**Frontend**
- Build: `cd frontend && npm install && npm run build` → output in `frontend/dist`
- Serve `dist/` as a static site with an SPA fallback to `index.html`.
- Set build-time env `VITE_API_BASE` to the backend URL/host, e.g.
  `VITE_API_BASE=https://your-backend.example.com`.

---

## Local development

No database required.

```bash
# Backend (port 8000)
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# …or: docker compose up --build  (runs the backend container)

# Frontend (port 3000) — in a second terminal
cd frontend
npm install
npm run dev
```

Open three browser windows/profiles at `http://localhost:3000`: one **Create
Room**, two **Join** with the code, host **Start**. Vite proxies `/api` and
`/ws` to the backend, so no env vars are needed locally.
