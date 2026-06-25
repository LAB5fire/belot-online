"""
Post-game analysis engine.
Replays all human moves and evaluates them against Monte Carlo alternatives.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from ..game_engine.card import Card, GameType
from ..game_engine.rules import get_legal_moves
from ..game_engine.game import MoveRecord, BelotGame
from ..ai.monte_carlo import evaluate_move


@dataclass
class MoveAnalysis:
    move_record: MoveRecord
    move_values: Dict[str, float]      # card repr -> expected value
    played_value: float
    best_value: float
    best_card: Card
    score: float                        # 0-100 for this move
    is_mistake: bool
    mistake_severity: str               # "none", "minor", "moderate", "major"
    explanation: str
    alternative_explanation: str


@dataclass
class GameAnalysis:
    game_id: str
    overall_score: float                # 0-100
    total_moves: int
    mistake_count: int
    minor_mistakes: int
    moderate_mistakes: int
    major_mistakes: int
    move_analyses: List[MoveAnalysis]
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]


_MISTAKE_THRESHOLD_MINOR = 0.05
_MISTAKE_THRESHOLD_MODERATE = 0.12
_MISTAKE_THRESHOLD_MAJOR = 0.25


def analyze_game(
    game: BelotGame,
    num_simulations: int = 500,
) -> GameAnalysis:
    """Analyze all human player moves in a completed game."""
    human_moves = [
        m for m in game.move_history
        if m.player == BelotGame.HUMAN_PLAYER
    ]

    move_analyses: List[MoveAnalysis] = []
    all_played: List[Card] = []

    # Reconstruct played card sequence per round
    round_played: Dict[int, List[Card]] = {}
    for m in game.move_history:
        rn = m.round_number
        if rn not in round_played:
            round_played[rn] = []
        round_played[rn].append(m.card)

    # Build played-cards-so-far per human move position
    played_up_to: Dict[int, List[Card]] = {}
    seen_idx = 0
    current_round = 1
    all_moves_ordered = sorted(game.move_history, key=lambda m: (m.round_number, m.trick_number, len(m.trick_before)))

    cumulative_played: List[Card] = []
    for m in all_moves_ordered:
        if m.player == BelotGame.HUMAN_PLAYER:
            played_up_to[id(m)] = list(cumulative_played)
        cumulative_played.append(m.card)

    for m in human_moves:
        played_before = played_up_to.get(id(m), [])

        # Estimate other players' hand sizes
        hand_sizes = _estimate_hand_sizes(m, game)

        # Evaluate all legal moves
        move_values = evaluate_move(
            player=m.player,
            card=m.card,
            hand=list(m.legal_moves),
            current_trick=list(m.trick_before),
            current_leader=_get_leader(m),
            game_type=_get_game_type(m, game),
            played_cards=played_before,
            hand_sizes=hand_sizes,
            tricks_won={0: 0, 1: 0},
            trick_number=m.trick_number,
            num_simulations=num_simulations,
        )

        played_card_repr = repr(m.card)
        played_value = move_values.get(m.card, 0.0)
        best_card = max(move_values, key=move_values.get)
        best_value = move_values[best_card]

        delta = best_value - played_value
        is_mistake = delta > _MISTAKE_THRESHOLD_MINOR

        if delta >= _MISTAKE_THRESHOLD_MAJOR:
            severity = "major"
        elif delta >= _MISTAKE_THRESHOLD_MODERATE:
            severity = "moderate"
        elif delta >= _MISTAKE_THRESHOLD_MINOR:
            severity = "minor"
        else:
            severity = "none"

        move_score = max(0.0, 100.0 * (1.0 - delta / 0.4))
        explanation = _generate_explanation(m, played_value, best_value, best_card, severity)
        alt_explanation = _generate_alternative(m.card, best_card, game_type=_get_game_type(m, game))

        ma = MoveAnalysis(
            move_record=m,
            move_values={repr(c): v for c, v in move_values.items()},
            played_value=played_value,
            best_value=best_value,
            best_card=best_card,
            score=move_score,
            is_mistake=is_mistake,
            mistake_severity=severity,
            explanation=explanation,
            alternative_explanation=alt_explanation,
        )
        move_analyses.append(ma)

    overall_score = _compute_overall_score(move_analyses)
    mistake_count = sum(1 for ma in move_analyses if ma.is_mistake)
    minor = sum(1 for ma in move_analyses if ma.mistake_severity == "minor")
    moderate = sum(1 for ma in move_analyses if ma.mistake_severity == "moderate")
    major = sum(1 for ma in move_analyses if ma.mistake_severity == "major")

    strengths, weaknesses, recs = _generate_feedback(move_analyses, overall_score)

    return GameAnalysis(
        game_id=game.game_id,
        overall_score=overall_score,
        total_moves=len(move_analyses),
        mistake_count=mistake_count,
        minor_mistakes=minor,
        moderate_mistakes=moderate,
        major_mistakes=major,
        move_analyses=move_analyses,
        strengths=strengths,
        weaknesses=weaknesses,
        recommendations=recs,
    )


def _estimate_hand_sizes(m: MoveRecord, game: BelotGame) -> Dict[int, int]:
    cards_played = (m.trick_number - 1) * 4 + len(m.trick_before)
    total_cards = 32
    remaining_per_player = (total_cards - cards_played) // 4
    sizes = {}
    for p in range(4):
        if p == m.player:
            sizes[p] = len(m.legal_moves)
        else:
            sizes[p] = max(0, remaining_per_player)
    return sizes


def _get_leader(m: MoveRecord) -> int:
    if m.trick_before:
        return m.trick_before[0][0]
    return m.player


def _get_game_type(m: MoveRecord, game: BelotGame) -> GameType:
    for rr in game.round_results:
        if rr.round_number == m.round_number:
            return rr.game_type
    # Current round
    return game.game_type or GameType.HEARTS


def _generate_explanation(
    m: MoveRecord,
    played_value: float,
    best_value: float,
    best_card: Card,
    severity: str,
) -> str:
    card_repr = repr(m.card)
    best_repr = repr(best_card)
    delta_pct = int((best_value - played_value) * 100)

    if severity == "none":
        return f"Playing {card_repr} was the optimal choice (expected win rate: {int(played_value*100)}%)."
    elif severity == "minor":
        return (
            f"Playing {card_repr} was slightly suboptimal. "
            f"{best_repr} would have been marginally better "
            f"(~{delta_pct}% improvement in expected win rate)."
        )
    elif severity == "moderate":
        return (
            f"Playing {card_repr} was a mistake. {best_repr} was a significantly better option, "
            f"improving expected win rate by ~{delta_pct}%."
        )
    else:
        return (
            f"Playing {card_repr} was a serious mistake. "
            f"{best_repr} would have dramatically improved your position "
            f"by ~{delta_pct}% in expected win rate."
        )


def _generate_alternative(
    played: Card, best: Card, game_type: GameType
) -> str:
    if played == best:
        return "No better alternative was found."

    reasons = []
    if best.is_trump(game_type) and not played.is_trump(game_type):
        reasons.append("playing trump establishes control")
    if best.get_value(game_type) > played.get_value(game_type):
        reasons.append(f"{repr(best)} carries more point value ({best.get_value(game_type)} vs {played.get_value(game_type)})")
    if best.get_trick_power(game_type) > played.get_trick_power(game_type):
        reasons.append(f"{repr(best)} is more likely to win the trick")

    if not reasons:
        return f"Consider playing {repr(best)} instead for better long-term position."
    return f"Consider playing {repr(best)} instead: {'; '.join(reasons)}."


def _compute_overall_score(analyses: List[MoveAnalysis]) -> float:
    if not analyses:
        return 50.0
    total = sum(ma.score for ma in analyses)
    return round(total / len(analyses), 1)


def _generate_feedback(
    analyses: List[MoveAnalysis], score: float
) -> Tuple[List[str], List[str], List[str]]:
    strengths: List[str] = []
    weaknesses: List[str] = []
    recs: List[str] = []

    good_moves = [ma for ma in analyses if not ma.is_mistake]
    bad_moves = [ma for ma in analyses if ma.is_mistake]

    # Analyze patterns in mistakes
    major_mistakes = [ma for ma in bad_moves if ma.mistake_severity == "major"]
    lead_mistakes = [ma for ma in bad_moves if not ma.move_record.trick_before]
    non_lead_mistakes = [ma for ma in bad_moves if ma.move_record.trick_before]

    if score >= 85:
        strengths.append("Excellent overall decision-making throughout the game.")
    elif score >= 70:
        strengths.append("Good card sense with mostly correct decisions.")

    if len(good_moves) > len(bad_moves):
        strengths.append(f"Made the optimal play {len(good_moves)} out of {len(analyses)} times.")

    if major_mistakes:
        weaknesses.append(f"Made {len(major_mistakes)} serious mistake(s) that significantly impacted the game.")
        recs.append("Review the major mistakes carefully — these had the biggest impact on the outcome.")

    if len(lead_mistakes) > 2:
        weaknesses.append("Struggled with lead selection, often choosing suboptimal opening cards.")
        recs.append("When leading, prefer aces in side suits or high trumps when you have 4+ trump cards.")

    if len(non_lead_mistakes) > 2:
        weaknesses.append("Had difficulty in following play, especially managing trump usage.")
        recs.append("Remember to track played cards and count remaining trumps to make better second/third-seat plays.")

    if score < 60:
        recs.append("Focus on the fundamental rule: only play trump when you cannot follow suit, and must use trump.")
        recs.append("When partner is winning the trick, play your highest-value card to maximize points collected.")

    if not recs:
        recs.append("Keep studying card combinations and practice tracking played cards.")

    return strengths, weaknesses, recs
