"""
Analysis service: runs post-game analysis and stores results.
"""
from __future__ import annotations
import asyncio
from typing import Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..game_engine.game import BelotGame, GamePhase
from ..analyzer.analyzer import analyze_game, GameAnalysis
from ..models.db_models import Game as GameModel, GameMove, GameAnalysis as GameAnalysisModel, PlayerStats
from ..core.config import get_settings

settings = get_settings()


async def run_analysis_and_store(
    game: BelotGame,
    db: AsyncSession,
) -> GameAnalysis:
    """Run analysis in executor (CPU bound) and persist to DB."""
    loop = asyncio.get_event_loop()
    analysis = await loop.run_in_executor(
        None,
        lambda: analyze_game(game, num_simulations=settings.analysis_simulations),
    )
    await _store_analysis(analysis, db)
    await _update_player_stats(analysis, game, db)
    return analysis


async def _store_analysis(analysis: GameAnalysis, db: AsyncSession) -> None:
    move_details = []
    for ma in analysis.move_analyses:
        move_details.append({
            "round_number": ma.move_record.round_number,
            "trick_number": ma.move_record.trick_number,
            "player": ma.move_record.player,
            "played_card": ma.move_record.card.to_dict(),
            "best_card": ma.best_card.to_dict(),
            "played_value": round(ma.played_value, 4),
            "best_value": round(ma.best_value, 4),
            "move_score": round(ma.score, 2),
            "is_mistake": ma.is_mistake,
            "mistake_severity": ma.mistake_severity,
            "explanation": ma.explanation,
            "alternative_explanation": ma.alternative_explanation,
            "legal_moves": [c.to_dict() for c in ma.move_record.legal_moves],
            "move_values": {k: round(v, 4) for k, v in ma.move_values.items()},
        })

    db_analysis = GameAnalysisModel(
        game_id=analysis.game_id,
        overall_score=analysis.overall_score,
        total_moves=analysis.total_moves,
        mistake_count=analysis.mistake_count,
        minor_mistakes=analysis.minor_mistakes,
        moderate_mistakes=analysis.moderate_mistakes,
        major_mistakes=analysis.major_mistakes,
        strengths=analysis.strengths,
        weaknesses=analysis.weaknesses,
        recommendations=analysis.recommendations,
        move_details=move_details,
    )
    db.add(db_analysis)
    await db.flush()


async def _update_player_stats(
    analysis: GameAnalysis, game: BelotGame, db: AsyncSession
) -> None:
    result = await db.execute(select(PlayerStats).limit(1))
    stats = result.scalar_one_or_none()

    if stats is None:
        stats = PlayerStats(
            games_played=0,
            games_won=0,
            avg_score=0.0,
            total_mistakes=0,
            best_score=0.0,
            worst_score=100.0,
        )
        db.add(stats)

    winner_team = game.cumulative_scores.get(0, 0) > game.cumulative_scores.get(1, 0)
    n = stats.games_played

    stats.games_played = n + 1
    if winner_team:
        stats.games_won += 1
    stats.total_mistakes += analysis.mistake_count
    stats.avg_score = (stats.avg_score * n + analysis.overall_score) / (n + 1)
    stats.best_score = max(stats.best_score, analysis.overall_score)
    stats.worst_score = min(stats.worst_score, analysis.overall_score)

    await db.flush()


async def get_analysis(game_id: str, db: AsyncSession) -> Optional[Dict[str, Any]]:
    result = await db.execute(
        select(GameAnalysisModel).where(GameAnalysisModel.game_id == game_id)
    )
    db_analysis = result.scalar_one_or_none()
    if db_analysis is None:
        return None

    return {
        "game_id": game_id,
        "overall_score": db_analysis.overall_score,
        "total_moves": db_analysis.total_moves,
        "mistake_count": db_analysis.mistake_count,
        "minor_mistakes": db_analysis.minor_mistakes,
        "moderate_mistakes": db_analysis.moderate_mistakes,
        "major_mistakes": db_analysis.major_mistakes,
        "strengths": db_analysis.strengths or [],
        "weaknesses": db_analysis.weaknesses or [],
        "recommendations": db_analysis.recommendations or [],
        "move_analyses": db_analysis.move_details or [],
        "status": "complete",
    }


async def get_player_stats(db: AsyncSession) -> Dict[str, Any]:
    result = await db.execute(select(PlayerStats).limit(1))
    stats = result.scalar_one_or_none()
    if stats is None:
        return {
            "games_played": 0,
            "games_won": 0,
            "win_rate": 0.0,
            "avg_score": 0.0,
            "best_score": 0.0,
            "worst_score": 0.0,
            "total_mistakes": 0,
        }
    win_rate = (stats.games_won / stats.games_played * 100) if stats.games_played > 0 else 0.0
    return {
        "games_played": stats.games_played,
        "games_won": stats.games_won,
        "win_rate": round(win_rate, 1),
        "avg_score": round(stats.avg_score, 1),
        "best_score": round(stats.best_score, 1),
        "worst_score": round(stats.worst_score, 1),
        "total_mistakes": stats.total_mistakes,
    }
