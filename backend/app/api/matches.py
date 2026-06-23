"""
API endpoints for match data.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.orm import aliased
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.match import Match, MatchStatus
from app.models.league import League
from app.models.team import Team
from app.models.expected_lineup import ExpectedLineup
from app.models.player import Player

router = APIRouter(prefix="/api/v1/matches", tags=["matches"])

HomeTeam = aliased(Team, name="home_team")
AwayTeam = aliased(Team, name="away_team")


@router.get("/today")
async def get_today_matches(
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Get all matches scheduled for today."""
    result = await db.execute(
        select(Match, League, HomeTeam, AwayTeam)
        .join(League, League.id == Match.league_id)
        .join(HomeTeam, HomeTeam.id == Match.home_team_id)
        .join(AwayTeam, AwayTeam.id == Match.away_team_id)
        .where(Match.match_date == func.current_date())
        .order_by(Match.id)
    )
    rows = result.all()

    return [
        {
            "id": match.id,
            "league_name": league.name if league else "",
            "home_team": home_team.name if home_team else "",
            "away_team": away_team.name if away_team else "",
            "match_date": match.match_date.isoformat(),
            "status": match.status.value if match.status else "scheduled",
            "home_score": match.home_score,
            "away_score": match.away_score,
        }
        for match, league, home_team, away_team in rows
    ]


@router.get("/{match_id}")
async def get_match_detail(
    match_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get match detail with expected lineups."""
    match = await db.get(Match, match_id)
    if not match:
        from fastapi import HTTPException
        raise HTTPException(404, "Match not found")

    league = await db.get(League, match.league_id)
    home_team = await db.get(Team, match.home_team_id)
    away_team = await db.get(Team, match.away_team_id)

    # Get lineups
    lineup_result = await db.execute(
        select(ExpectedLineup, Player).join(
            Player, Player.id == ExpectedLineup.player_id
        ).where(
            ExpectedLineup.match_id == match_id,
        )
    )
    lineup_rows = lineup_result.all()

    home_lineup = []
    away_lineup = []
    for el, player in lineup_rows:
        lp = {
            "player_id": player.id,
            "player_name": player.name,
            "position": player.position,
            "is_probable": el.is_probable,
            "is_injured": el.is_injured,
            "is_suspended": el.is_suspended,
        }
        if el.team_id == match.home_team_id:
            home_lineup.append(lp)
        else:
            away_lineup.append(lp)

    return {
        "id": match.id,
        "league_name": league.name if league else "",
        "home_team": home_team.name if home_team else "",
        "away_team": away_team.name if away_team else "",
        "match_date": match.match_date.isoformat(),
        "status": match.status.value if match.status else "scheduled",
        "home_score": match.home_score,
        "away_score": match.away_score,
        "home_lineup": home_lineup,
        "away_lineup": away_lineup,
    }
