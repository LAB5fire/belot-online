from __future__ import annotations
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from ...core.database import get_db
from ...services.analysis_service import get_player_stats
from ...models.db_models import Game as GameModel, GameAnalysis as GameAnalysisModel
from ..schemas.analysis_schemas import PlayerStatsResponse, ScoreHistoryItem

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/player", response_model=PlayerStatsResponse)
async def player_statistics(db: AsyncSession = Depends(get_db)):
    return await get_player_stats(db)


@router.get("/history", response_model=List[ScoreHistoryItem])
async def score_history(limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(
            GameModel.id,
            GameModel.created_at,
            GameModel.winner_team,
            GameModel.score_team0,
            GameModel.score_team1,
            GameAnalysisModel.overall_score,
        )
        .join(GameAnalysisModel, GameModel.id == GameAnalysisModel.game_id, isouter=True)
        .where(GameModel.status == "finished")
        .order_by(desc(GameModel.created_at))
        .limit(limit)
    )
    rows = result.all()
    return [
        ScoreHistoryItem(
            game_id=row[0],
            date=row[1].isoformat() if row[1] else "",
            overall_score=row[5] or 0.0,
            winner_team=row[2],
            score_team0=row[3] or 0,
            score_team1=row[4] or 0,
        )
        for row in rows
    ]
