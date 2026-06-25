"""SQLAlchemy ORM models for Belot Analyzer."""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    String, Integer, Float, Boolean, DateTime, ForeignKey, JSON, Text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from ..core.database import Base


class Game(Base):
    __tablename__ = "games"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active, finished, abandoned
    game_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    winner_team: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    score_team0: Mapped[int] = mapped_column(Integer, default=0)
    score_team1: Mapped[int] = mapped_column(Integer, default=0)
    rounds_played: Mapped[int] = mapped_column(Integer, default=0)
    game_state: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    moves: Mapped[list["GameMove"]] = relationship(back_populates="game", cascade="all, delete-orphan")
    analysis: Mapped[Optional["GameAnalysis"]] = relationship(back_populates="game", uselist=False, cascade="all, delete-orphan")


class GameMove(Base):
    __tablename__ = "game_moves"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    game_id: Mapped[str] = mapped_column(String(36), ForeignKey("games.id", ondelete="CASCADE"))
    round_number: Mapped[int] = mapped_column(Integer)
    trick_number: Mapped[int] = mapped_column(Integer)
    player: Mapped[int] = mapped_column(Integer)
    card_suit: Mapped[str] = mapped_column(String(10))
    card_rank: Mapped[str] = mapped_column(String(5))
    legal_moves: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    trick_state: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    game: Mapped["Game"] = relationship(back_populates="moves")


class GameAnalysis(Base):
    __tablename__ = "game_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    game_id: Mapped[str] = mapped_column(String(36), ForeignKey("games.id", ondelete="CASCADE"), unique=True)
    overall_score: Mapped[float] = mapped_column(Float)
    total_moves: Mapped[int] = mapped_column(Integer)
    mistake_count: Mapped[int] = mapped_column(Integer)
    minor_mistakes: Mapped[int] = mapped_column(Integer, default=0)
    moderate_mistakes: Mapped[int] = mapped_column(Integer, default=0)
    major_mistakes: Mapped[int] = mapped_column(Integer, default=0)
    strengths: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    weaknesses: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    recommendations: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    move_details: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    game: Mapped["Game"] = relationship(back_populates="analysis")


class PlayerStats(Base):
    __tablename__ = "player_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    games_played: Mapped[int] = mapped_column(Integer, default=0)
    games_won: Mapped[int] = mapped_column(Integer, default=0)
    avg_score: Mapped[float] = mapped_column(Float, default=0.0)
    total_mistakes: Mapped[int] = mapped_column(Integer, default=0)
    best_score: Mapped[float] = mapped_column(Float, default=0.0)
    worst_score: Mapped[float] = mapped_column(Float, default=100.0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
