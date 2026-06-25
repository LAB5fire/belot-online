"""Database repository for game persistence."""
from __future__ import annotations
import json
from typing import List, Optional
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from ..models.db_models import Game as GameModel, GameMove, GameAnalysis as GameAnalysisModel
from ..game_engine.game import BelotGame, GamePhase


async def save_game(game: BelotGame, db: AsyncSession) -> GameModel:
    result = await db.execute(select(GameModel).where(GameModel.id == game.game_id))
    db_game = result.scalar_one_or_none()

    status = "active"
    if game.phase == GamePhase.FINISHED:
        status = "finished"

    winner = None
    if status == "finished":
        s0 = game.cumulative_scores.get(0, 0)
        s1 = game.cumulative_scores.get(1, 0)
        winner = 0 if s0 > s1 else 1

    if db_game is None:
        db_game = GameModel(
            id=game.game_id,
            status=status,
            game_type=game.game_type.value if game.game_type else None,
            winner_team=winner,
            score_team0=game.cumulative_scores.get(0, 0),
            score_team1=game.cumulative_scores.get(1, 0),
            rounds_played=game.round_number,
        )
        db.add(db_game)
    else:
        db_game.status = status
        db_game.game_type = game.game_type.value if game.game_type else None
        db_game.winner_team = winner
        db_game.score_team0 = game.cumulative_scores.get(0, 0)
        db_game.score_team1 = game.cumulative_scores.get(1, 0)
        db_game.rounds_played = game.round_number
        if status == "finished":
            db_game.finished_at = datetime.now(timezone.utc)

    await db.flush()
    return db_game


async def save_moves(game: BelotGame, db: AsyncSession) -> None:
    """Persist all moves from the game."""
    existing = await db.execute(
        select(GameMove.id).where(GameMove.game_id == game.game_id)
    )
    existing_count = len(existing.scalars().all())

    new_moves = game.move_history[existing_count:]
    for m in new_moves:
        db_move = GameMove(
            game_id=game.game_id,
            round_number=m.round_number,
            trick_number=m.trick_number,
            player=m.player,
            card_suit=m.card.suit.value,
            card_rank=m.card.rank.value,
            legal_moves=[c.to_dict() for c in m.legal_moves],
            trick_state=[
                {"player": p, "card": c.to_dict()} for p, c in m.trick_before
            ],
        )
        db.add(db_move)

    await db.flush()


async def get_game_list(db: AsyncSession, limit: int = 20) -> List[dict]:
    result = await db.execute(
        select(
            GameModel.id,
            GameModel.status,
            GameModel.created_at,
            GameModel.finished_at,
            GameModel.winner_team,
            GameModel.score_team0,
            GameModel.score_team1,
            GameModel.rounds_played,
        )
        .order_by(desc(GameModel.created_at))
        .limit(limit)
    )
    rows = result.all()
    games = []
    for row in rows:
        has_analysis = await db.execute(
            select(GameAnalysisModel.id).where(GameAnalysisModel.game_id == row[0])
        )
        games.append({
            "game_id": row[0],
            "status": row[1],
            "created_at": row[2].isoformat() if row[2] else "",
            "finished_at": row[3].isoformat() if row[3] else None,
            "winner_team": row[4],
            "score_team0": row[5] or 0,
            "score_team1": row[6] or 0,
            "rounds_played": row[7] or 0,
            "has_analysis": has_analysis.scalar() is not None,
        })
    return games
