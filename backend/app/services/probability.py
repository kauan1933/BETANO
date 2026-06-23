"""
Probability calculation engine for shot-related markets.

Uses Poisson distribution based on historical player data,
adjusted for form recency weighting and opponent context.
"""

import math
import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


def poisson_probability(k: int, lam: float) -> float:
    """P(X = k) for Poisson(lambda)."""
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return (lam ** k) * math.exp(-lam) / math.factorial(k)


def poisson_cdf(k: int, lam: float) -> float:
    """P(X <= k) for Poisson(lambda)."""
    return sum(poisson_probability(i, lam) for i in range(k + 1))


def poisson_sf(k: int, lam: float) -> float:
    """P(X >= k) for Poisson(lambda)."""
    return 1 - poisson_cdf(k - 1, lam)


def calculate_weighted_average(
    recent_games: list[dict],
    weight_last_n: float = 0.50,
    weight_mid_n: float = 0.30,
    weight_baseline: float = 0.20,
    baseline_avg: Optional[float] = None,
) -> float:
    """
    Calculate weighted average of a stat across recent games.
    Last 5 games = 50%, Games 6-10 = 30%, Season baseline = 20%.
    """
    if not recent_games:
        return baseline_avg or 0.0

    n = len(recent_games)

    # Per-90 normalization
    per90_values = []
    for g in recent_games:
        mins = g.get("minutes_played", 0) or 0
        val = g.get("value", 0) or 0
        # Use per-90 rate if sufficient minutes
        if mins >= 15:
            per90_values.append((val / mins) * 90)
        else:
            per90_values.append(0.0)

    if not per90_values:
        return baseline_avg or 0.0

    # Split into last 5 and games 6-10
    last5 = per90_values[:5]
    mid = per90_values[5:10] if n > 5 else []

    avg_last5 = sum(last5) / len(last5) if last5 else 0.0
    avg_mid = sum(mid) / len(mid) if mid else 0.0
    avg_all = sum(per90_values) / len(per90_values)

    weighted = (avg_last5 * weight_last_n +
                avg_mid * weight_mid_n +
                (baseline_avg or avg_all) * weight_baseline)

    return weighted


def calculate_consistency_score(recent_games: list[dict]) -> float:
    """
    Calculate how consistently a player shoots.
    1.0 = shoots every game, 0.0 = never shoots.
    Based on coefficient of variation (lower CV = more consistent).
    """
    if not recent_games or len(recent_games) < 3:
        return 0.0

    per90 = []
    for g in recent_games:
        mins = g.get("minutes_played", 0) or 0
        shots = g.get("total_shots", 0) or 0
        if mins >= 15:
            per90.append((shots / mins) * 90)

    if len(per90) < 3:
        return 0.0

    mean = sum(per90) / len(per90)
    if mean == 0:
        return 0.0

    variance = sum((x - mean) ** 2 for x in per90) / len(per90)
    std_dev = math.sqrt(variance)
    cv = std_dev / mean  # coefficient of variation

    # Lower CV = more consistent. Score: 1.0 - min(cv, 1.5) / 1.5
    consistency = max(0.0, 1.0 - min(cv, 1.5) / 1.5)
    return round(consistency, 3)


def calculate_shot_probabilities(
    avg_shots_per90: float,
    avg_sot_per90: float,
    opponent_defense_factor: float = 1.0,
    home_advantage: float = 1.0,
) -> dict:
    """
    Calculate probabilities for shot-related markets.

    Returns:
        prob_1_shot_ontarget: P(>= 1 shot on target)
        prob_2_plus_shot_ontarget: P(>= 2 shots on target)
        prob_x_total_shots: P(>= X total shots) for X in {1, 2, 3, 4, 5}
    """
    adjusted_sot = avg_sot_per90 * opponent_defense_factor * home_advantage
    adjusted_total = avg_shots_per90 * opponent_defense_factor * home_advantage

    return {
        "prob_1_shot_ontarget": round(poisson_sf(1, adjusted_sot), 4),
        "prob_2_plus_shot_ontarget": round(poisson_sf(2, adjusted_sot), 4),
        "prob_x_total_shots": {
            str(k): round(poisson_sf(k, adjusted_total), 4)
            for k in range(1, 6)
        },
    }


def get_player_form_weighted_stats(
    match_stats: list[dict],
    baseline_avg_total: Optional[float] = None,
    baseline_avg_sot: Optional[float] = None,
) -> dict:
    """
    Process raw match stats into weighted averages for a player.
    Each stat dict should have: minutes_played, total_shots, shots_on_target.
    """
    if not match_stats:
        return {
            "avg_total_shots": baseline_avg_total or 0.0,
            "avg_shots_on_target": baseline_avg_sot or 0.0,
            "consistency_score": 0.0,
            "games_analyzed": 0,
        }

    # Extract shot values per game
    shot_games = [
        {"minutes_played": s.get("minutes_played", 0),
         "value": s.get("total_shots", 0)}
        for s in match_stats
    ]
    sot_games = [
        {"minutes_played": s.get("minutes_played", 0),
         "value": s.get("shots_on_target", 0)}
        for s in match_stats
    ]

    avg_total = calculate_weighted_average(
        shot_games, baseline_avg=baseline_avg_total
    )
    avg_sot = calculate_weighted_average(
        sot_games, baseline_avg=baseline_avg_sot
    )
    consistency = calculate_consistency_score(match_stats)

    return {
        "avg_total_shots": round(avg_total, 3),
        "avg_shots_on_target": round(avg_sot, 3),
        "consistency_score": round(consistency, 3),
        "games_analyzed": len(match_stats),
    }
