from __future__ import annotations
from typing import Optional, List, Dict
from pydantic import BaseModel


class MoveAnalysisSchema(BaseModel):
    round_number: int
    trick_number: int
    player: int
    played_card: Dict[str, str]
    best_card: Dict[str, str]
    played_value: float
    best_value: float
    move_score: float
    is_mistake: bool
    mistake_severity: str
    explanation: str
    alternative_explanation: str
    legal_moves: List[Dict[str, str]]
    move_values: Dict[str, float]


class GameAnalysisResponse(BaseModel):
    game_id: str
    overall_score: float
    total_moves: int
    mistake_count: int
    minor_mistakes: int
    moderate_mistakes: int
    major_mistakes: int
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    move_analyses: List[MoveAnalysisSchema]
    status: str = "complete"


class AnalysisStatusResponse(BaseModel):
    game_id: str
    status: str  # "pending", "processing", "complete", "not_found"
    overall_score: Optional[float] = None


class PlayerStatsResponse(BaseModel):
    games_played: int
    games_won: int
    win_rate: float
    avg_score: float
    best_score: float
    worst_score: float
    total_mistakes: int


class ScoreHistoryItem(BaseModel):
    game_id: str
    date: str
    overall_score: float
    winner_team: Optional[int]
    score_team0: int
    score_team1: int
