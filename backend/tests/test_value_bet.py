"""Tests for the value bet detection service."""

import pytest
from app.services.value_bet import (
    odds_to_implied_probability,
    calculate_expected_value,
    is_value_bet,
    get_confidence_label,
    find_value_bets_for_player,
)


class TestOddsConversion:
    def test_even_odds(self):
        """Decimal odds of 2.0 = 50% implied prob."""
        assert abs(odds_to_implied_probability(2.0) - 0.5) < 0.001

    def test_favorite_odds(self):
        """Low odds = high implied probability."""
        assert odds_to_implied_probability(1.5) > 0.6
        assert odds_to_implied_probability(1.25) > 0.75

    def test_longshot_odds(self):
        """High odds = low implied probability."""
        assert odds_to_implied_probability(5.0) < 0.25
        assert odds_to_implied_probability(10.0) < 0.15

    def test_minimum_odds(self):
        """Odds <= 1 should return 1.0."""
        assert odds_to_implied_probability(0.5) == 1.0
        assert odds_to_implied_probability(1.0) == 1.0


class TestEVCalculation:
    def test_positive_ev(self):
        """Model says 60%, odds at 2.5 → +EV."""
        ev = calculate_expected_value(0.60, 2.5)
        # EV = 0.60 * (2.5-1) - 0.40 = 0.50
        assert abs(ev - 0.50) < 0.01

    def test_negative_ev(self):
        """Model says 40%, odds at 2.0 → -EV."""
        ev = calculate_expected_value(0.40, 2.0)
        # EV = 0.40 * (2.0-1) - 0.60 = -0.20
        assert ev < 0

    def test_break_even(self):
        """Model matches implied probability → EV ≈ 0."""
        ev = calculate_expected_value(0.50, 2.0)
        assert abs(ev) < 0.001

    def test_high_edge(self):
        """Model says 70%, odds at 2.0 → big +EV."""
        ev = calculate_expected_value(0.70, 2.0)
        # EV = 0.70 * 1.0 - 0.30 = 0.40
        assert abs(ev - 0.40) < 0.01


class TestIsValueBet:
    def test_above_threshold(self):
        assert is_value_bet(0.60, 2.0, threshold=0.05)
        # EV = 0.20 > 0.05

    def test_below_threshold(self):
        assert not is_value_bet(0.52, 2.0, threshold=0.05)
        # EV = 0.04 < 0.05

    def test_custom_threshold(self):
        assert is_value_bet(0.55, 2.0, threshold=0.02)
        # EV = 0.10 > 0.02


class TestConfidenceLabel:
    def test_high_ev_and_consistency(self):
        label = get_confidence_label(0.25, 0.85)
        assert label == "high"

    def test_medium_ev_high_consistency(self):
        label = get_confidence_label(0.08, 0.80)
        assert label == "medium"

    def test_low_ev_low_consistency(self):
        label = get_confidence_label(0.05, 0.30)
        assert label == "low"

    def test_high_ev_low_consistency(self):
        label = get_confidence_label(0.25, 0.30)
        assert label == "medium"


class TestFindValueBets:
    def test_finds_value(self):
        market_odds = {
            "Player Shots on Target - Over 0.5": 2.50,
        }
        shot_probs = {
            "prob_1_shot_ontarget": 0.60,
            "prob_2_plus_shot_ontarget": 0.25,
            "prob_x_total_shots": {"1": 0.75, "2": 0.40, "3": 0.15},
        }
        bets = find_value_bets_for_player(
            player_id=1,
            market_odds=market_odds,
            shot_probabilities=shot_probs,
            consistency_score=0.75,
        )
        assert len(bets) > 0
        for b in bets:
            assert b["expected_value"] >= 0.05
            assert b["player_id"] == 1
            assert "market" in b
            assert "confidence" in b

    def test_no_value(self):
        """When odds are too low, no value bet."""
        market_odds = {
            "Player Shots on Target - Over 0.5": 1.20,
        }
        shot_probs = {
            "prob_1_shot_ontarget": 0.60,
            "prob_2_plus_shot_ontarget": 0.25,
            "prob_x_total_shots": {"1": 0.75, "2": 0.40},
        }
        bets = find_value_bets_for_player(1, market_odds, shot_probs, 0.75)
        assert len(bets) == 0

    def test_empty_odds(self):
        """No market odds → no bets."""
        bets = find_value_bets_for_player(1, {}, {"prob_1_shot_ontarget": 0.5}, 0.5)
        assert len(bets) == 0

    def test_multiple_markets(self):
        """Should find value across multiple markets if they meet threshold."""
        market_odds = {
            "Player Shots on Target - Over 0.5": 2.20,
            "Player Shots on Target - Over 1.5": 4.00,
            "Player Total Shots - Over 1.5": 2.50,
        }
        shot_probs = {
            "prob_1_shot_ontarget": 0.55,
            "prob_2_plus_shot_ontarget": 0.30,
            "prob_x_total_shots": {"1": 0.70, "2": 0.35, "3": 0.10},
        }
        bets = find_value_bets_for_player(1, market_odds, shot_probs, 0.70)
        # At least one should have value given the numbers
        assert len(bets) >= 1
