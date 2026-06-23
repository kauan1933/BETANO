"""
Value Bet detection service.
Compares model-calculated probabilities with market odds to find EV+ opportunities.
"""

import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

SHOT_MARKETS = [
    "Player Shots on Target",
    "Player Shots on Target - Over 0.5",
    "Player Shots on Target - Over 1.5",
    "Player Total Shots",
    "Player Total Shots - Over 0.5",
    "Player Total Shots - Over 1.5",
    "Player Total Shots - Over 2.5",
]


def odds_to_implied_probability(decimal_odds: float) -> float:
    """Convert decimal odds to implied probability."""
    if decimal_odds <= 1:
        return 1.0
    return 1.0 / decimal_odds


def calculate_expected_value(
    model_probability: float,
    decimal_odds: float,
) -> float:
    """
    Calculate Expected Value.
    EV = (model_prob * payout if win) - (1 - model_prob)
    """
    implied = odds_to_implied_probability(decimal_odds)
    ev = (model_probability * (decimal_odds - 1)) - (1 - model_probability)
    return round(ev, 4)


def is_value_bet(
    model_probability: float,
    decimal_odds: float,
    threshold: float = 0.05,
) -> bool:
    """Check if a bet has positive expected value above threshold."""
    ev = calculate_expected_value(model_probability, decimal_odds)
    return ev >= threshold


def get_confidence_label(ev: float, consistency_score: float) -> str:
    """Classify bet confidence based on EV and consistency."""
    score = 0
    if ev >= 0.20:
        score += 3
    elif ev >= 0.10:
        score += 2
    elif ev >= 0.05:
        score += 1

    if consistency_score >= 0.7:
        score += 2
    elif consistency_score >= 0.5:
        score += 1

    if score >= 4:
        return "high"
    elif score >= 2:
        return "medium"
    return "low"


def find_value_bets_for_player(
    player_id: int,
    market_odds: dict[str, float],
    shot_probabilities: dict,
    consistency_score: float,
) -> list[dict]:
    """
    Find all value bets for a player across shot markets.

    market_odds: dict mapping market description -> decimal odds
    shot_probabilities: dict from calculate_shot_probabilities()
    """
    results = []

    # Map our probabilities to market names
    prob_mapping = {
        "Player Shots on Target - Over 0.5": shot_probabilities.get("prob_1_shot_ontarget", 0),
        "Player Shots on Target - Over 1.5": shot_probabilities.get("prob_2_plus_shot_ontarget", 0),
        "Player Shots on Target": shot_probabilities.get("prob_1_shot_ontarget", 0),
    }

    # Total shots markets
    total_shots_probs = shot_probabilities.get("prob_x_total_shots", {})
    for k_str, prob in total_shots_probs.items():
        k = int(k_str)
        if k == 1:
            prob_mapping["Player Total Shots - Over 0.5"] = prob
            prob_mapping["Player Total Shots"] = prob
        elif k == 2:
            prob_mapping["Player Total Shots - Over 1.5"] = prob
        elif k == 3:
            prob_mapping["Player Total Shots - Over 2.5"] = prob

    for market_name, model_prob in prob_mapping.items():
        if market_name not in market_odds:
            continue

        decimal_odds = market_odds[market_name]
        ev = calculate_expected_value(model_prob, decimal_odds)

        if ev >= settings.EV_THRESHOLD:
            results.append({
                "player_id": player_id,
                "market": market_name,
                "calc_probability": round(model_prob, 4),
                "market_odds": decimal_odds,
                "implied_probability": round(1.0 / decimal_odds, 4),
                "expected_value": round(ev, 4),
                "confidence": get_confidence_label(ev, consistency_score),
            })

    return results
