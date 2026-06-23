"""
Admin panel API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from app.core.database import get_db
from app.core.redis import redis_client as global_redis
from app.models.value_bet import ValueBet, BetStatus
from app.models.match import Match, MatchStatus
from app.models.player import Player
from app.models.player_form import PlayerForm
from app.tasks.refresh import (
    refresh_today_matches,
    refresh_player_stats,
    refresh_odds,
    calculate_all_probabilities,
    detect_value_bets,
)
from app.seed import seed_database
from app.models.base import Base
from app.core.database import engine

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.get("/dashboard")
async def get_admin_dashboard(db: AsyncSession = Depends(get_db)) -> dict:
    """Get admin dashboard metrics."""
    today = date.today()

    # Today's matches
    matches_count = await db.execute(
        select(func.count(Match.id)).where(Match.match_date == today)
    )
    live_count = await db.execute(
        select(func.count(Match.id)).where(
            Match.match_date == today,
            Match.status == MatchStatus.LIVE,
        )
    )

    # Tracked players
    player_count = await db.execute(select(func.count(Player.id)))
    players_with_form = await db.execute(
        select(func.count(PlayerForm.id)).where(PlayerForm.games_analyzed >= 3)
    )

    # Value bets
    active_bets = await db.execute(
        select(func.count(ValueBet.id)).where(ValueBet.status == BetStatus.ACTIVE)
    )
    avg_ev = await db.execute(
        select(func.avg(ValueBet.expected_value)).where(
            ValueBet.status == BetStatus.ACTIVE,
        )
    )

    # Last refresh times
    last_refresh = {}
    if global_redis:
        for key in ["matches", "odds", "valuebets"]:
            val = await global_redis.get(f"last_refresh:{key}")
            if val:
                last_refresh[key] = val

    return {
        "today_matches": matches_count.scalar() or 0,
        "live_matches": live_count.scalar() or 0,
        "total_players": player_count.scalar() or 0,
        "players_with_form": players_with_form.scalar() or 0,
        "active_value_bets": active_bets.scalar() or 0,
        "average_ev": round(float(avg_ev.scalar() or 0), 4),
        "last_refresh": last_refresh,
        "tracked_leagues": [
            "Premier League", "La Liga", "Serie A", "Bundesliga",
            "Ligue 1", "Brasileirão", "Argentine League", "MLS",
            "Eredivisie", "Primeira Liga",
        ],
    }


@router.post("/seed")
async def run_seed():
    """Drop all tables, recreate, and populate with mock data for testing."""
    try:
        await seed_database()
        return {"message": "Database seeded successfully"}
    except Exception as e:
        raise HTTPException(500, f"Seed failed: {str(e)}")

@router.post("/refresh")
async def force_refresh(
    target: str = "all",
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Force a data refresh for a specific target or all targets."""
    targets = {
        "matches": refresh_today_matches,
        "players": refresh_player_stats,
        "odds": refresh_odds,
        "probabilities": calculate_all_probabilities,
        "valuebets": detect_value_bets,
    }

    if target == "all":
        for name, task in targets.items():
            await task()
        return {"message": "All data refreshed", "targets": list(targets.keys())}

    if target not in targets:
        raise HTTPException(400, f"Unknown target: {target}. Options: {list(targets.keys())}")

    await targets[target]()
    return {"message": f"Refreshed: {target}"}
