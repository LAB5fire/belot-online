from __future__ import annotations
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class CardSchema(BaseModel):
    suit: str
    rank: str


class BidRequest(BaseModel):
    game_type: Optional[str] = None  # None = pass


class PlayCardRequest(BaseModel):
    card: CardSchema


class GameStateResponse(BaseModel):
    game_id: str
    phase: str
    round_number: int
    dealer: int
    current_player: Optional[int]
    cumulative_scores: Dict[str, int]
    bids: List[Dict[str, Any]]
    current_bid: Optional[str]
    available_bids: List[str]
    game_type: Optional[str]
    declaring_team: int
    hands: Dict[str, Any]  # player -> list of cards (or count for opponents)
    current_trick: List[Dict[str, Any]]
    trick_number: int
    tricks_won_count: Dict[str, int]
    declarations: Dict[str, Any]
    declaration_winners: Optional[int]
    last_round: Optional[Dict[str, Any]]

    model_config = {"from_attributes": True}


class CreateGameResponse(BaseModel):
    game_id: str
    message: str


class TrickResultResponse(BaseModel):
    winner: int
    winning_team: int
    trick_number: int
    game_state: GameStateResponse


class BotMoveResponse(BaseModel):
    player: int
    card: CardSchema
    trick_result: Optional[Dict[str, Any]] = None


class GameActionResponse(BaseModel):
    game_state: GameStateResponse
    bot_moves: List[BotMoveResponse] = Field(default_factory=list)
    trick_completed: Optional[Dict[str, Any]] = None
    phase_changed: bool = False
    message: str = ""


class GameSummaryResponse(BaseModel):
    game_id: str
    status: str
    created_at: str
    finished_at: Optional[str]
    winner_team: Optional[int]
    score_team0: int
    score_team1: int
    rounds_played: int
    has_analysis: bool
