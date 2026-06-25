from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...game_engine.card import Card, Suit, Rank
from ...game_engine.game import GamePhase
from ...services.game_service import (
    create_game, get_game, human_bid, human_play_card, get_game_state, remove_game
)
from ...services.analysis_service import run_analysis_and_store
from ...repositories.game_repository import save_game, save_moves, get_game_list
from ..schemas.game_schemas import (
    BidRequest, PlayCardRequest, CreateGameResponse,
    GameActionResponse, GameSummaryResponse,
)

router = APIRouter(prefix="/games", tags=["games"])


@router.post("", response_model=CreateGameResponse)
async def create_new_game(db: AsyncSession = Depends(get_db)):
    game = create_game()
    await save_game(game, db)
    return CreateGameResponse(game_id=game.game_id, message="Game created")


@router.get("", response_model=list[GameSummaryResponse])
async def list_games(db: AsyncSession = Depends(get_db)):
    return await get_game_list(db, limit=20)


@router.get("/{game_id}")
async def get_game_endpoint(game_id: str):
    game = get_game(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return game.to_dict(viewer=0)


@router.post("/{game_id}/bid")
async def place_bid(
    game_id: str,
    request: BidRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    game = get_game(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    try:
        result = human_bid(game_id, request.game_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    await save_game(game, db)

    # Auto-start playing phase if declarations happened
    if game.phase == GamePhase.PLAYING:
        result["phase_changed"] = True

    return result


@router.post("/{game_id}/play")
async def play_card(
    game_id: str,
    request: PlayCardRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    game = get_game(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    try:
        card = Card(Suit(request.card.suit), Rank(request.card.rank))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid card: {e}")

    try:
        result = human_play_card(game_id, card)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    await save_game(game, db)
    await save_moves(game, db)

    # If game finished, run analysis in background
    if game.phase == GamePhase.FINISHED:
        background_tasks.add_task(run_analysis_and_store, game, db)

    return result


@router.delete("/{game_id}")
async def abandon_game(game_id: str, db: AsyncSession = Depends(get_db)):
    game = get_game(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    remove_game(game_id)
    return {"message": "Game abandoned"}
