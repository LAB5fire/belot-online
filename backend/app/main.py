from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import get_settings
from .api.routes import room_router

settings = get_settings()


app = FastAPI(
    title="Belot Online",
    description="Online 3-player Bulgarian Belot",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(room_router)


@app.get("/")
async def root():
    return {"message": "Belot Online API", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok"}
