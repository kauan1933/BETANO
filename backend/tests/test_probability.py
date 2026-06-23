"""Tests for the probability calculation engine."""

import pytest
from app.services.probability import (
    poisson_probability,
    poisson_sf,
    calculate_weighted_average,
    calculate_consistency_score,
    calculate_shot_probabilities,
    get_player_form_weighted_stats,
)


class TestPoisson:
    def test_poisson_basics(self):
        """Basic Poisson properties."""
        assert poisson_probability(0, 0) == 1.0
        assert poisson_probability(1, 0) == 0.0
        # P(X=0) for lambda=1.5 = e^-1.5 ≈ 0.223
        assert 0.20 < poisson_probability(0, 1.5) < 0.25
        # P(X=1) for lambda=1.5 = 1.5 * e^-1.5 ≈ 0.335
        assert 0.30 < poisson_probability(1, 1.5) < 0.37

    def test_poisson_sum_approx_one(self):
        """Sum of probabilities for k=0..10 should be ~1."""
        lam = 2.5
        total = sum(poisson_probability(k, lam) for k in range(0, 20))
        assert abs(total - 1.0) < 0.001

    def test_poisson_sf(self):
        """Survival function: P(X >= 1) should be 1 - P(X = 0)."""
        lam = 1.8
        p0 = poisson_probability(0, lam)
        assert abs(poisson_sf(1, lam) - (1 - p0)) < 0.0001

    def test_poisson_sf_zero_rate(self):
        """With lambda=0, P(X >= 1) = 0."""
        assert poisson_sf(1, 0) == 0.0
        assert poisson_sf(0, 0) == 1.0


class TestWeightedAverage:
    def test_empty_games(self):
        assert calculate_weighted_average([]) == 0.0

    def test_with_baseline(self):
        result = calculate_weighted_average([], baseline_avg=2.0)
        assert result == 2.0

    def test_basic_weighted(self):
        games = [
            {"minutes_played": 90, "value": 4},
            {"minutes_played": 90, "value": 2},
        ]
        result = calculate_weighted_average(
            games,
            weight_last_n=1.0,
            weight_mid_n=0.0,
            weight_baseline=0.0,
        )
        # Per-90: [4.0, 2.0] → avg = 3.0
        assert abs(result - 3.0) < 0.01

    def test_with_insufficient_minutes(self):
        games = [
            {"minutes_played": 10, "value": 1},
            {"minutes_played": 90, "value": 3},
        ]
        result = calculate_weighted_average(
            games,
            weight_last_n=1.0,
            weight_mid_n=0.0,
            weight_baseline=0.0,
        )
        # First game: < 15 min → 0.0
        # Second: 3 per 90
        # avg = 1.5
        assert abs(result - 1.5) < 0.01


class TestConsistency:
    def test_perfect_consistency(self):
        games = [
            {"minutes_played": 90, "total_shots": 4},
            {"minutes_played": 90, "total_shots": 4},
            {"minutes_played": 90, "total_shots": 4},
            {"minutes_played": 90, "total_shots": 4},
        ]
        score = calculate_consistency_score(games)
        assert score > 0.9

    def test_high_variance_low_consistency(self):
        games = [
            {"minutes_played": 90, "total_shots": 0},
            {"minutes_played": 90, "total_shots": 8},
            {"minutes_played": 90, "total_shots": 1},
            {"minutes_played": 90, "total_shots": 7},
        ]
        score = calculate_consistency_score(games)
        assert score < 0.5

    def test_insufficient_games(self):
        assert calculate_consistency_score([]) == 0.0
        assert calculate_consistency_score([{"minutes_played": 90, "total_shots": 3}]) == 0.0


class TestShotProbabilities:
    def test_high_volume_player(self):
        """A player averaging 2.5 SOT per 90 should have high probabilities."""
        probs = calculate_shot_probabilities(
            avg_shots_per90=5.0,
            avg_sot_per90=2.5,
        )
        assert probs["prob_1_shot_ontarget"] > 0.8
        assert probs["prob_2_plus_shot_ontarget"] > 0.5

    def test_low_volume_player(self):
        """A player with very few shots should have low probabilities."""
        probs = calculate_shot_probabilities(
            avg_shots_per90=0.5,
            avg_sot_per90=0.2,
        )
        assert probs["prob_1_shot_ontarget"] < 0.3
        assert probs["prob_2_plus_shot_ontarget"] < 0.05

    def test_defense_factor_reduces_probs(self):
        base = calculate_shot_probabilities(avg_shots_per90=4.0, avg_sot_per90=2.0)
        reduced = calculate_shot_probabilities(
            avg_shots_per90=4.0,
            avg_sot_per90=2.0,
            opponent_defense_factor=0.7,
        )
        assert reduced["prob_1_shot_ontarget"] < base["prob_1_shot_ontarget"]

    def test_total_shots_output(self):
        probs = calculate_shot_probabilities(avg_shots_per90=4.0, avg_sot_per90=2.0)
        assert "prob_x_total_shots" in probs
        assert "1" in probs["prob_x_total_shots"]
        assert "5" in probs["prob_x_total_shots"]
        # More shots should have lower probability
        assert probs["prob_x_total_shots"]["1"] > probs["prob_x_total_shots"]["3"]


class TestFormWeightedStats:
    def test_empty_stats(self):
        result = get_player_form_weighted_stats([])
        assert result["avg_total_shots"] == 0.0
        assert result["games_analyzed"] == 0

    def test_happy_path(self):
        stats = [
            {"minutes_played": 90, "total_shots": 4, "shots_on_target": 2},
            {"minutes_played": 90, "total_shots": 3, "shots_on_target": 1},
            {"minutes_played": 85, "total_shots": 5, "shots_on_target": 3},
        ]
        result = get_player_form_weighted_stats(stats)
        assert result["games_analyzed"] == 3
        assert result["avg_total_shots"] > 0
        assert result["avg_shots_on_target"] > 0
        assert result["consistency_score"] >= 0
