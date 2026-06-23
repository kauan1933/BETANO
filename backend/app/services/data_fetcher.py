"""
Data fetcher service - fetches matches, lineups, stats from external APIs.
Uses API-Football (free tier), Football-Data.org, and web scraping as fallback.
"""

import logging
from datetime import date, timedelta
from typing import Optional
import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings

logger = logging.getLogger(__name__)

# Major leagues to track
TARGET_LEAGUES = [
    {"name": "Premier League", "country": "England", "api_id": 39},
    {"name": "La Liga", "country": "Spain", "api_id": 140},
    {"name": "Serie A", "country": "Italy", "api_id": 135},
    {"name": "Bundesliga", "country": "Germany", "api_id": 78},
    {"name": "Ligue 1", "country": "France", "api_id": 61},
    {"name": "Brasileirão", "country": "Brazil", "api_id": 71},
    {"name": "Argentine League", "country": "Argentina", "api_id": 128},
    {"name": "MLS", "country": "USA", "api_id": 253},
    {"name": "Eredivisie", "country": "Netherlands", "api_id": 88},
    {"name": "Primeira Liga", "country": "Portugal", "api_id": 94},
    {"name": "World Cup", "country": "International", "api_id": 1},
    {"name": "Champions League", "country": "Europe", "api_id": 2},
    {"name": "Europa League", "country": "Europe", "api_id": 3},
    {"name": "Copa America", "country": "South America", "api_id": 9},
    {"name": "Copa do Brasil", "country": "Brazil", "api_id": 73},
    {"name": "Série B", "country": "Brazil", "api_id": 72},
    {"name": "Liga Portugal", "country": "Portugal", "api_id": 94},
    {"name": "Championship", "country": "England", "api_id": 40},
    {"name": "Liga MX", "country": "Mexico", "api_id": 262},
    {"name": "J-League", "country": "Japan", "api_id": 98},
]


class DataFetcher:
    BASE_URL = "https://v3.football.api-sports.io"

    def __init__(self):
        self.api_key = settings.API_FOOTBALL_KEY
        self.headers = {"x-apisports-key": self.api_key} if self.api_key else {}

    async def is_available(self) -> bool:
        return bool(self.api_key)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _get(self, endpoint: str, params: dict) -> dict:
        if not self.api_key:
            return {"results": 0, "response": []}
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{self.BASE_URL}/{endpoint}",
                headers=self.headers,
                params=params,
            )
            resp.raise_for_status()
            return resp.json()

    async def get_today_fixtures(self) -> list[dict]:
        """Get today's fixtures for all target leagues."""
        today = date.today().isoformat()
        league_ids = [str(l["api_id"]) for l in TARGET_LEAGUES]

        data = await self._get("fixtures", {
            "date": today,
            "league": ",".join(league_ids),
            "season": "2024",  # current season
        })
        return data.get("response", [])

    async def get_fixtures_by_date(self, dt: date) -> list[dict]:
        league_ids = [str(l["api_id"]) for l in TARGET_LEAGUES]
        data = await self._get("fixtures", {
            "date": dt.isoformat(),
            "league": ",".join(league_ids),
            "season": "2024",
        })
        return data.get("response", [])

    async def get_player_stats(self, fixture_id: int) -> list[dict]:
        """Get player statistics for a given fixture."""
        data = await self._get("fixtures/players", {"fixture": fixture_id})
        return data.get("response", [])

    async def get_player_last_games(self, player_id: int, team_id: int, limit: int = 10) -> list[dict]:
        """Get last N games for a player."""
        data = await self._get("players", {
            "id": player_id,
            "season": "2024",
        })
        # Extract last N fixtures from response
        players = data.get("response", [])
        if not players:
            return []
        # The API returns statistics grouped by league
        stats = players[0].get("statistics", [])
        # Filter by team and get last matches
        team_stats = [s for s in stats if s["team"]["id"] == team_id]
        return team_stats[:limit] if team_stats else stats[:limit]

    async def get_lineups(self, fixture_id: int) -> list[dict]:
        """Get probable lineups for a fixture."""
        data = await self._get("fixtures/lineups", {"fixture": fixture_id})
        return data.get("response", [])

    async def get_injuries(self, fixture_id: int) -> list[dict]:
        """Get injury/suspension info for a fixture."""
        data = await self._get("injuries", {"fixture": fixture_id})
        return data.get("response", [])

    async def get_odds(self, fixture_id: int) -> list[dict]:
        """Get betting odds for a fixture."""
        data = await self._get("odds", {"fixture": fixture_id})
        return data.get("response", [])

    # --- Fallback: web scraping ---
    async def scrape_lineups(self, match_url: str) -> dict:
        """Fallback: scrape expected lineups from a football news site."""
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(match_url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                })
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "lxml")
                # Basic extraction logic - adapt per source
                lineup_data = {"home": [], "away": []}
                # ... would parse specific site structure
                return lineup_data
        except Exception as e:
            logger.warning(f"Scraping failed for {match_url}: {e}")
            return {"home": [], "away": []}
