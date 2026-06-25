"""
Game service: manages active game sessions and orchestrates bot moves.
"""
from __future__ import annotations
import asyncio
from typing import Dict, List, Optional, Tuple, Any

from ..game_engine.game import BelotGame, GamePhase
from ..game_engine.card import Card, GameType
from ..ai.bot import BelotBot
from ..core.config import get_settings

settings = get_settings()

# In-memory active games storage
_active_games: Dict[str, BelotGame] = {}
_game_bots: Dict[str, Dict[int, BelotBot]] = {}


def create_game() -> BelotGame:
    game = BelotGame()
    _active_games[game.game_id] = game

    bots = {
        1: BelotBot(1, difficulty=settings.bot_difficulty),
        2: BelotBot(2, difficulty=settings.bot_difficulty),
        3: BelotBot(3, difficulty=settings.bot_difficulty),
    }
    _game_bots[game.game_id] = bots

    # Auto-run bot bidding for the opening round
    _process_bot_bids(game, bots)

    return game


def get_game(game_id: str) -> Optional[BelotGame]:
    return _active_games.get(game_id)


def remove_game(game_id: str) -> None:
    _active_games.pop(game_id, None)
    _game_bots.pop(game_id, None)


def human_bid(game_id: str, game_type: Optional[str]) -> Dict[str, Any]:
    game = _get_game_or_raise(game_id)
    bots = _game_bots[game_id]

    gt = GameType(game_type) if game_type else None
    game.place_bid(BelotGame.HUMAN_PLAYER, gt)

    # Let bots bid until bidding ends or it's human's turn again
    if game.phase == GamePhase.BIDDING:
        _process_bot_bids(game, bots)

    response: Dict[str, Any] = {}

    # Reveal declarations if bidding just finished (bot bidding may already
    # have revealed them and advanced straight to the playing phase).
    if game.phase == GamePhase.DECLARATIONS:
        decl_result = game.reveal_declarations()
        response["declarations"] = decl_result
        response["phase_changed"] = True

    # Once the playing phase begins, the first leader may be a bot, so let the
    # bots play up to the human's turn.
    bot_moves: List[Dict[str, Any]] = []
    if game.phase == GamePhase.PLAYING:
        bot_moves = _process_bot_plays(game, bots)
        response["phase_changed"] = True
    response["bot_moves"] = bot_moves

    response["game_state"] = game.to_dict(viewer=BelotGame.HUMAN_PLAYER)
    return response


def human_play_card(game_id: str, card: Card) -> Dict[str, Any]:
    game = _get_game_or_raise(game_id)
    bots = _game_bots[game_id]

    if game.phase != GamePhase.PLAYING:
        raise ValueError("Game is not in playing phase")
    if game.current_player != BelotGame.HUMAN_PLAYER:
        raise ValueError("Not human player's turn")

    trick_result = game.play_card(BelotGame.HUMAN_PLAYER, card)

    # Tell all bots about the played card
    for bot in bots.values():
        bot.observe_card_played(card)

    bot_moves: List[Dict[str, Any]] = []

    if trick_result:
        # Trick is complete; check if bots lead next
        bot_moves_after = _process_bot_plays(game, bots)
        bot_moves.extend(bot_moves_after)
    else:
        # Trick continues; let bots play their turns
        bot_moves_in_trick = _process_bot_plays(game, bots)
        bot_moves.extend(bot_moves_in_trick)

    return {
        "game_state": game.to_dict(viewer=BelotGame.HUMAN_PLAYER),
        "bot_moves": bot_moves,
        "trick_completed": trick_result.to_dict() if trick_result else None,
    }


def get_game_state(game_id: str) -> Dict[str, Any]:
    game = _get_game_or_raise(game_id)
    return game.to_dict(viewer=BelotGame.HUMAN_PLAYER)


def _get_game_or_raise(game_id: str) -> BelotGame:
    game = _active_games.get(game_id)
    if game is None:
        raise ValueError(f"Game {game_id} not found")
    return game


def _process_bot_bids(game: BelotGame, bots: Dict[int, BelotBot]) -> None:
    """Let bots bid in sequence until bidding ends or human's turn."""
    max_iterations = 20
    iterations = 0

    while game.phase == GamePhase.BIDDING and game.current_player != BelotGame.HUMAN_PLAYER:
        current = game.current_player
        if current not in bots:
            break

        bot = bots[current]
        bid = bot.choose_bid(
            hand=game.hands[current],
            current_bid=game.current_bid,
            available_bids=game.available_bids,
        )
        game.place_bid(current, bid)

        # If declarations phase starts, reveal them
        if game.phase == GamePhase.DECLARATIONS:
            game.reveal_declarations()
            break

        iterations += 1
        if iterations >= max_iterations:
            break


def _process_bot_plays(game: BelotGame, bots: Dict[int, BelotBot]) -> List[Dict[str, Any]]:
    """Let bots act until it's the human's turn or the game/round ends.

    Handles bots leading the first trick, finishing a trick they win, and the
    transition into a brand-new round (re-running bot bidding and then driving
    the new round's opening bot plays).
    """
    bot_moves: List[Dict[str, Any]] = []
    max_iterations = 200
    iterations = 0

    while iterations < max_iterations:
        iterations += 1

        if game.phase == GamePhase.PLAYING and game.current_player != BelotGame.HUMAN_PLAYER:
            current = game.current_player
            if current not in bots:
                break

            bot = bots[current]
            hand_sizes = {p: len(game.hands[p]) for p in range(4)}
            tricks_won = {
                team: len(tricks) for team, tricks in game.tricks_won.items()
            }

            card = bot.choose_card(
                hand=game.hands[current],
                current_trick=game.current_trick,
                current_leader=game.current_leader,
                game_type=game.game_type,
                hand_sizes=hand_sizes,
                tricks_won=tricks_won,
                trick_number=game.current_trick_number,
            )

            trick_result = game.play_card(current, card)

            # Inform all bots of this play
            for other_bot in bots.values():
                other_bot.observe_card_played(card)

            bot_moves.append({
                "player": current,
                "card": card.to_dict(),
                "trick_result": trick_result.to_dict() if trick_result else None,
            })
            continue

        # A finished round rolls over into a new round of bidding.
        if game.phase == GamePhase.BIDDING and game.current_player != BelotGame.HUMAN_PLAYER:
            for bot in bots.values():
                bot.reset()
            _process_bot_bids(game, bots)
            # If bot bidding ran straight into the playing phase with a bot
            # leading, loop again to play out the new round's opening tricks.
            continue

        # Human's turn, or scoring/finished/declarations — nothing more for bots.
        break

    return bot_moves
