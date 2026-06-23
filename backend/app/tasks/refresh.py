"""
Background refresh tasks for match data, player stats, odds.
Uses APScheduler triggers.
"""

import logging
from datetime import date, datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.core.redis import redis_client
from app.services.data_fetcher import DataFetcher, TARGET_LEAGUES
from app.services.probability import (
    calculate_shot_probabilities,
    get_player_form_weighted_stats,
)
from app.services.value_bet import (
    find_value_bets_for_player,
    odds_to_implied_probability,
)
from app.models.league import League
from app.models.team import Team
from app.models.player import Player
from app.models.match import Match, MatchStatus
from app.models.player_match_stats import PlayerMatchStats
from app.models.player_form import PlayerForm
from app.models.expected_lineup import ExpectedLineup
from app.models.odds import Odds
from app.models.value_bet import ValueBet, BetStatus

logger = logging.getLogger(__name__)
fetcher = DataFetcher()


async def refresh_today_matches():
    """Fetch today's matches and upsert leagues/teams/matches."""
    logger.info("Refreshing today's matches...")

    # Ensure all target leagues exist in the DB even if they have no fixtures today
    async with async_session_factory() as session:
        for target in TARGET_LEAGUES:
            existing = await session.execute(
                select(League).where(League.external_id == str(target["api_id"]))
            )
            if not existing.scalar_one_or_none():
                league = League(
                    name=target["name"],
                    country=target["country"],
                    external_id=str(target["api_id"]),
                    is_active=True,
                )
                session.add(league)
                await session.flush()
                logger.info(f"Auto-created league: {target['name']} (id={target['api_id']})")
        await session.commit()

    fixtures = await fetcher.get_today_fixtures()
    if not fixtures:
        logger.info("No fixtures found for today.")
        return

    async with async_session_factory() as session:
        for fixture in fixtures:
            try:
                f = fixture["fixture"]
                league_data = fixture["league"]
                teams = fixture["teams"]

                # Upsert league
                league = await session.execute(
                    select(League).where(League.external_id == str(league_data["id"]))
                )
                league = league.scalar_one_or_none()
                if not league:
                    league = League(
                        name=league_data["name"],
                        country=league_data.get("country", ""),
                        logo_url=league_data.get("logo"),
                        external_id=str(league_data["id"]),
                    )
                    session.add(league)
                    await session.flush()

                # Upsert home team
                home_team = await session.execute(
                    select(Team).where(Team.external_id == str(teams["home"]["id"]))
                )
                home_team = home_team.scalar_one_or_none()
                if not home_team:
                    home_team = Team(
                        name=teams["home"]["name"],
                        external_id=str(teams["home"]["id"]),
                        league_id=league.id,
                    )
                    session.add(home_team)
                    await session.flush()

                # Upsert away team
                away_team = await session.execute(
                    select(Team).where(Team.external_id == str(teams["away"]["id"]))
                )
                away_team = away_team.scalar_one_or_none()
                if not away_team:
                    away_team = Team(
                        name=teams["away"]["name"],
                        external_id=str(teams["away"]["id"]),
                        league_id=league.id,
                    )
                    session.add(away_team)
                    await session.flush()

                # Upsert match
                match_date = datetime.fromtimestamp(f["date"]).date()
                match = await session.execute(
                    select(Match).where(Match.external_id == str(f["id"]))
                )
                match = match.scalar_one_or_none()
                if not match:
                    match = Match(
                        league_id=league.id,
                        home_team_id=home_team.id,
                        away_team_id=away_team.id,
                        match_date=match_date,
                        external_id=str(f["id"]),
                        status=MatchStatus.SCHEDULED,
                    )
                    session.add(match)

            except Exception as e:
                logger.error(f"Error processing fixture {fixture.get('fixture', {}).get('id')}: {e}")
                continue

        await session.commit()

    logger.info(f"Processed {len(fixtures)} fixtures.")
    # Cache last refresh time
    if redis_client:
        await redis_client.set("last_refresh:matches", datetime.now().isoformat())


async def refresh_player_stats():
    """Update player match stats and form for recent matches."""
    logger.info("Refreshing player stats...")
    async with async_session_factory() as session:
        # Get recent finished matches
        three_days_ago = date.today()
        result = await session.execute(
            select(Match).where(
                Match.match_date >= three_days_ago,
                Match.status == MatchStatus.SCHEDULED,
            ).limit(50)
        )
        matches = result.scalars().all()

        if not matches:
            logger.info("No matches to process.")
            return

        for match in matches:
            if not match.external_id:
                continue

            try:
                stats_data = await fetcher.get_player_stats(int(match.external_id))
                if not stats_data:
                    continue

                for team_data in stats_data:
                    team_id = None
                    for player_entry in team_data.get("players", []):
                        # Would map player data to stats
                        pass

            except Exception as e:
                logger.error(f"Error fetching stats for match {match.id}: {e}")
                continue

    logger.info("Player stats refresh complete.")


async def refresh_odds():
    """Refresh betting odds for today's matches."""
    logger.info("Refreshing odds...")
    async with async_session_factory() as session:
        today = date.today()
        result = await session.execute(
            select(Match).where(
                Match.match_date == today,
                Match.status.in_([MatchStatus.SCHEDULED, MatchStatus.LIVE]),
            )
        )
        matches = result.scalars().all()

        updated = 0
        for match in matches:
            if not match.external_id:
                continue

            try:
                odds_data = await fetcher.get_odds(int(match.external_id))
                if not odds_data:
                    continue

                for bookmaker_entry in odds_data:
                    bookmaker_name = bookmaker_entry.get("bookmaker", {}).get("name", "Unknown")
                    for bet in bookmaker_entry.get("bets", []):
                        market_name = bet.get("name", "")
                        # Only track shot-related markets
                        if "shot" not in market_name.lower() and "shot" not in market_name.lower():
                            continue

                        for value_entry in bet.get("values", []):
                            existing = await session.execute(
                                select(Odds).where(
                                    Odds.match_id == match.id,
                                    Odds.bookmaker == bookmaker_name,
                                    Odds.market == market_name,
                                    Odds.selection == value_entry.get("value", ""),
                                )
                            )
                            existing_odds = existing.scalar_one_or_none()
                            if existing_odds:
                                existing_odds.odds_value = float(value_entry.get("odd", 1.0))
                            else:
                                session.add(Odds(
                                    match_id=match.id,
                                    bookmaker=bookmaker_name,
                                    market=market_name,
                                    selection=value_entry.get("value", ""),
                                    odds_value=float(value_entry.get("odd", 1.0)),
                                ))
                            updated += 1

            except Exception as e:
                logger.error(f"Error fetching odds for match {match.id}: {e}")
                continue

        await session.commit()
    logger.info(f"Updated {updated} odds entries.")
    if redis_client:
        await redis_client.set("last_refresh:odds", datetime.now().isoformat())


async def calculate_all_probabilities():
    """Recalculate player form and shot probabilities for all active players."""
    logger.info("Recalculating probabilities...")
    async with async_session_factory() as session:
        today = date.today()
        result = await session.execute(
            select(Match).where(
                Match.match_date == today,
                Match.status.in_([MatchStatus.SCHEDULED, MatchStatus.LIVE]),
            )
        )
        matches = result.scalars().all()

        for match in matches:
            # Get expected starters for this match
            lineups = await session.execute(
                select(ExpectedLineup).where(
                    ExpectedLineup.match_id == match.id,
                    ExpectedLineup.is_probable == True,
                    ExpectedLineup.is_injured == False,
                    ExpectedLineup.is_suspended == False,
                )
            )
            starters = lineups.scalars().all()

            for lineup_entry in starters:
                # Get last 10 match stats for this player
                stats_result = await session.execute(
                    select(PlayerMatchStats).where(
                        PlayerMatchStats.player_id == lineup_entry.player_id,
                    ).order_by(PlayerMatchStats.id.desc()).limit(10)
                )
                match_stats = stats_result.scalars().all()

                if not match_stats:
                    continue

                stats_dicts = [
                    {
                        "minutes_played": s.minutes_played,
                        "total_shots": s.total_shots,
                        "shots_on_target": s.shots_on_target,
                    }
                    for s in match_stats
                ]

                form_stats = get_player_form_weighted_stats(stats_dicts)

                # Upsert player form
                existing_form = await session.execute(
                    select(PlayerForm).where(PlayerForm.player_id == lineup_entry.player_id)
                )
                existing = existing_form.scalar_one_or_none()
                if existing:
                    existing.avg_total_shots = form_stats["avg_total_shots"]
                    existing.avg_shots_on_target = form_stats["avg_shots_on_target"]
                    existing.consistency_score = form_stats["consistency_score"]
                    existing.games_analyzed = form_stats["games_analyzed"]
                else:
                    session.add(PlayerForm(
                        player_id=lineup_entry.player_id,
                        **form_stats,
                    ))

        await session.commit()
    logger.info("Probability recalculation complete.")


async def detect_value_bets():
    """Scan all active matches and detect EV+ betting opportunities."""
    logger.info("Detecting value bets...")
    async with async_session_factory() as session:
        today = date.today()
        result = await session.execute(
            select(Match).where(
                Match.match_date == today,
                Match.status.in_([MatchStatus.SCHEDULED, MatchStatus.LIVE]),
            )
        )
        matches = result.scalars().all()
        new_bets = 0

        for match in matches:
            # Get all probable players with form data for this match
            lineups = await session.execute(
                select(ExpectedLineup, PlayerForm).join(
                    PlayerForm,
                    ExpectedLineup.player_id == PlayerForm.player_id,
                ).where(
                    ExpectedLineup.match_id == match.id,
                    ExpectedLineup.is_probable == True,
                    ExpectedLineup.is_injured == False,
                    ExpectedLineup.is_suspended == False,
                )
            )
            rows = lineups.all()

            # Get odds for this match
            odds_result = await session.execute(
                select(Odds).where(Odds.match_id == match.id)
            )
            odds_entries = odds_result.scalars().all()

            # Index odds by selection text
            odds_by_selection = {}
            for o in odds_entries:
                odds_by_selection[o.selection] = o.odds_value

            for lineup_entry, form in rows:
                # Calc shot probabilities
                probs = calculate_shot_probabilities(
                    avg_shots_per90=form.avg_total_shots,
                    avg_sot_per90=form.avg_shots_on_target,
                )

                # Map odds to market
                player = await session.get(Player, lineup_entry.player_id)
                if not player:
                    continue

                market_odds = {}
                player_name = player.name
                for selection, odds_val in odds_by_selection.items():
                    if player_name.lower() in selection.lower():
                        if "shot on target" in selection.lower() or "shot" in selection.lower():
                            market_odds[selection] = odds_val

                if not market_odds:
                    continue

                value_bets = find_value_bets_for_player(
                    player_id=lineup_entry.player_id,
                    market_odds=market_odds,
                    shot_probabilities=probs,
                    consistency_score=form.consistency_score,
                )

                for vb in value_bets:
                    # Check if this bet already exists
                    existing = await session.execute(
                        select(ValueBet).where(
                            ValueBet.match_id == match.id,
                            ValueBet.player_id == vb["player_id"],
                            ValueBet.market == vb["market"],
                            ValueBet.status == BetStatus.ACTIVE,
                        )
                    )
                    if not existing.scalar_one_or_none():
                        session.add(ValueBet(
                            match_id=match.id,
                            **vb,
                        ))
                        new_bets += 1

        await session.commit()
    logger.info(f"Detected {new_bets} new value bets.")
    if redis_client:
        await redis_client.set("last_refresh:valuebets", datetime.now().isoformat())
