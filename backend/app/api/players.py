"""
API endpoints for player data.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.orm import aliased
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import redis_client as global_redis
from app.models.player import Player
from app.models.player_form import PlayerForm
from app.models.team import Team
from app.models.league import League
from app.models.expected_lineup import ExpectedLineup
from app.models.match import Match, MatchStatus

HomeTeam = aliased(Team, name="home_team")
AwayTeam = aliased(Team, name="away_team")

router = APIRouter(prefix="/api/v1/players", tags=["players"])


@router.get("/today")
async def get_today_players(
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Get all probable players for today's matches with shot probabilities."""
    # Try cache first
    if global_redis:
        cached = await global_redis.get("api:players:today")
        if cached:
            import json
            return json.loads(cached)

    result = await db.execute(
        select(
            Match, ExpectedLineup, Player, PlayerForm, Team, League, HomeTeam, AwayTeam
        ).join(
            ExpectedLineup, ExpectedLineup.match_id == Match.id
        ).join(
            Player, Player.id == ExpectedLineup.player_id
        ).join(
            PlayerForm, PlayerForm.player_id == Player.id, isouter=True
        ).join(
            Team, Team.id == Player.team_id
        ).join(
            League, League.id == Match.league_id
        ).join(
            HomeTeam, HomeTeam.id == Match.home_team_id
        ).join(
            AwayTeam, AwayTeam.id == Match.away_team_id
        ).where(
            Match.match_date == func.current_date(),
            ExpectedLineup.is_probable == True,
            ExpectedLineup.is_injured == False,
            ExpectedLineup.is_suspended == False,
        )
    )
    rows = result.all()

    players_data = []
    for match, lineup, player, form, team, league, home_team, away_team in rows:
        if not form:
            continue

        opponent = away_team.name if team.id == match.home_team_id else home_team.name

        from app.services.probability import calculate_shot_probabilities
        probs = calculate_shot_probabilities(
            avg_shots_per90=form.avg_total_shots,
            avg_sot_per90=form.avg_shots_on_target,
        )

        players_data.append({
            "match_id": match.id,
            "match": f"{team.name} vs {opponent}",
            "league": league.name,
            "match_date": match.match_date.isoformat(),
            "player": {
                "id": player.id,
                "name": player.name,
                "team_name": team.name,
                "position": player.position,
                "photo_url": player.photo_url,
                "form": {
                    "avg_total_shots": form.avg_total_shots,
                    "avg_shots_on_target": form.avg_shots_on_target,
                    "consistency_score": form.consistency_score,
                    "games_analyzed": form.games_analyzed,
                },
            },
            "prob_1_shot_ot": probs["prob_1_shot_ontarget"],
            "prob_2_plus_shot_ot": probs["prob_2_plus_shot_ontarget"],
            "prob_x_total_shots": probs["prob_x_total_shots"],
        })

    # Cache for 2 minutes
    if global_redis and players_data:
        import json
        await global_redis.setex("api:players:today", 120, json.dumps(players_data, default=str))

    return players_data


@router.get("/top-shooters")
async def get_top_shooters(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Get top shooters ranking sorted by shots on target."""
    result = await db.execute(
        select(
            Player, PlayerForm, Team, League
        ).join(
            PlayerForm, PlayerForm.player_id == Player.id
        ).join(
            Team, Team.id == Player.team_id
        ).join(
            League, League.id == Team.league_id
        ).where(
            PlayerForm.games_analyzed >= 3,
            PlayerForm.avg_shots_on_target > 0,
        ).order_by(
            PlayerForm.avg_shots_on_target.desc()
        ).limit(limit)
    )
    rows = result.all()

    from app.services.probability import calculate_shot_probabilities
    return [
        {
            "player_id": player.id,
            "player_name": player.name,
            "team_name": team.name,
            "league_name": league.name,
            "position": player.position,
            "avg_total_shots": form.avg_total_shots,
            "avg_shots_on_target": form.avg_shots_on_target,
            "consistency_score": form.consistency_score,
            "prob_1_shot_ontarget": calculate_shot_probabilities(
                form.avg_total_shots, form.avg_shots_on_target
            )["prob_1_shot_ontarget"],
            "prob_2_plus_shots_ontarget": calculate_shot_probabilities(
                form.avg_total_shots, form.avg_shots_on_target
            )["prob_2_plus_shot_ontarget"],
        }
        for player, form, team, league in rows
    ]


@router.get("/{player_id}")
async def get_player_detail(
    player_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get detailed player info with recent form and history."""
    player = await db.get(Player, player_id)
    if not player:
        from fastapi import HTTPException
        raise HTTPException(404, "Player not found")

    form = await db.execute(
        select(PlayerForm).where(PlayerForm.player_id == player_id)
    )
    form = form.scalar_one_or_none()

    team = await db.get(Team, player.team_id)

    # Get recent match stats
    from app.models.player_match_stats import PlayerMatchStats
    stats_result = await db.execute(
        select(PlayerMatchStats).where(
            PlayerMatchStats.player_id == player_id,
        ).order_by(PlayerMatchStats.id.desc()).limit(10)
    )
    recent_stats = stats_result.scalars().all()

    from app.schemas.match import MatchResponse
    return {
        "player": {
            "id": player.id,
            "name": player.name,
            "team_name": team.name if team else None,
            "position": player.position,
            "nationality": player.nationality,
            "photo_url": player.photo_url,
        },
        "form": {
            "avg_total_shots": form.avg_total_shots if form else 0,
            "avg_shots_on_target": form.avg_shots_on_target if form else 0,
            "consistency_score": form.consistency_score if form else 0,
            "games_analyzed": form.games_analyzed if form else 0,
        } if form else None,
        "recent_stats": [
            {
                "minutes_played": s.minutes_played,
                "total_shots": s.total_shots,
                "shots_on_target": s.shots_on_target,
                "goals": s.goals,
            }
            for s in recent_stats
        ],
    }
