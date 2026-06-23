"""Tests for the data fetcher service."""

import pytest
from app.services.data_fetcher import DataFetcher, TARGET_LEAGUES


class TestDataFetcher:
    def test_target_leagues(self):
        """Should track major football leagues."""
        assert len(TARGET_LEAGUES) >= 5
        league_names = [l["name"] for l in TARGET_LEAGUES]
        assert "Premier League" in league_names
        assert "La Liga" in league_names
        assert "Brasileirão" in league_names

    def test_league_ids_are_integers(self):
        for league in TARGET_LEAGUES:
            assert isinstance(league["api_id"], int)

    def test_fetcher_initialization(self):
        fetcher = DataFetcher()
        assert fetcher.BASE_URL == "https://v3.football.api-sports.io"

    def test_fetcher_no_api_key(self):
        """Without API key, fetcher returns empty results."""
        fetcher = DataFetcher()
        assert fetcher.api_key is None
