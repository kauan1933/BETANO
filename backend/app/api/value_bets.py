"""
API endpoints for value bets.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import redis_client as global_redis
from app.models.value_bet import ValueBet, BetStatus
from app.models.match import Match
from app.models.player import Player
from app.models.team import Team
from app.models.league import League

router = APIRouter(prefix="/api/v1/value-bets", tags=["value-bets"])


@router.get("/shots")
async def get_shot_value_bets(
    limit: int = Query(50, ge=1, le=200),
    min_ev: float = Query(0.05, ge=0.0),
    confidence: str = Query(None, regex="^(low|medium|high)$"),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Get all value bets for shot-related markets, sorted by EV descending."""
    # Try cache
    if global_redis:
        import json
        cached = await global_redis.get("api:valuebets:shots")
        if cached:
            return json.loads(cached)

    query = select(
        ValueBet, Match, Player, Team, League
    ).join(
        Match, Match.id == ValueBet.match_id
    ).join(
        Player, Player.id == ValueBet.player_id
    ).join(
        Team, Team.id == Player.team_id
    ).join(
        League, League.id == Match.league_id
    ).where(
        ValueBet.status == BetStatus.ACTIVE,
        ValueBet.expected_value >= min_ev,
    ).order_by(
        ValueBet.expected_value.desc()
    ).limit(limit)

    result = await db.execute(query)
    rows = result.all()

    bets_data = [
        {
            "id": vb.id,
            "match": f"{team.name}",
            "player_name": player.name,
            "team_name": team.name,
            "league_name": league.name,
            "market": vb.market,
            "calc_probability": vb.calc_probability,
            "market_odds": vb.market_odds,
            "implied_probability": vb.implied_probability,
            "expected_value": vb.expected_value,
            "confidence": vb.confidence,
            "created_at": vb.created_at.isoformat() if vb.created_at else None,
        }
        for vb, match, player, team, league in rows
    ]

    # Cache for 1 minute
    if global_redis and bets_data:
        import json
        await global_redis.setex("api:valuebets:shots", 60, json.dumps(bets_data, default=str))

    return bets_data


@router.get("/stats")
async def get_value_bet_stats(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get aggregate statistics about value bets."""
    total = await db.execute(
        select(func.count(ValueBet.id)).where(ValueBet.status == BetStatus.ACTIVE)
    )
    total = total.scalar() or 0

    avg_ev = await db.execute(
        select(func.avg(ValueBet.expected_value)).where(ValueBet.status == BetStatus.ACTIVE)
    )
    avg_ev = round(float(avg_ev.scalar() or 0), 4)

    high_conf = await db.execute(
        select(func.count(ValueBet.id)).where(
            ValueBet.status == BetStatus.ACTIVE,
            ValueBet.confidence == "high",
        )
    )

    return {
        "total_active": total,
        "average_ev": avg_ev,
        "high_confidence": high_conf.scalar() or 0,
    }
