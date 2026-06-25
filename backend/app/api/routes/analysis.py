from __future__ import annotations
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...services.game_service import get_game
from ...services.analysis_service import run_analysis_and_store, get_analysis
from ..schemas.analysis_schemas import GameAnalysisResponse, AnalysisStatusResponse

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/{game_id}/status", response_model=AnalysisStatusResponse)
async def get_analysis_status(game_id: str, db: AsyncSession = Depends(get_db)):
    result = await get_analysis(game_id, db)
    if result is None:
        return AnalysisStatusResponse(game_id=game_id, status="not_found")
    return AnalysisStatusResponse(
        game_id=game_id,
        status="complete",
        overall_score=result["overall_score"],
    )


@router.get("/{game_id}", response_model=GameAnalysisResponse)
async def get_game_analysis(game_id: str, db: AsyncSession = Depends(get_db)):
    result = await get_analysis(game_id, db)
    if result is None:
        raise HTTPException(status_code=404, detail="Analysis not found for this game")
    return result


@router.post("/{game_id}/trigger")
async def trigger_analysis(
    game_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger analysis for a finished game."""
    game = get_game(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found in active sessions")

    # Check if analysis already exists
    existing = await get_analysis(game_id, db)
    if existing is not None:
        return {"message": "Analysis already exists", "game_id": game_id}

    background_tasks.add_task(run_analysis_and_store, game, db)
    return {"message": "Analysis started", "game_id": game_id}
