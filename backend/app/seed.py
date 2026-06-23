"""
Seed script - populates the database with synthetic test data.
Run: python -m app.seed
"""

import asyncio
import random
import math
from datetime import date, timedelta
from sqlalchemy import select

from app.core.database import async_session_factory, engine
from app.models.base import Base
from app.models.league import League
from app.models.team import Team
from app.models.player import Player
from app.models.match import Match, MatchStatus
from app.models.player_match_stats import PlayerMatchStats
from app.models.expected_lineup import ExpectedLineup
from app.models.odds import Odds
from app.models.player_form import PlayerForm

LEAGUES_DATA = [
    {"name": "Premier League", "country": "England", "api_id": "39"},
    {"name": "La Liga", "country": "Spain", "api_id": "140"},
    {"name": "Serie A", "country": "Italy", "api_id": "135"},
    {"name": "Bundesliga", "country": "Germany", "api_id": "78"},
    {"name": "Brasileirão", "country": "Brazil", "api_id": "71"},
]

TEAMS_DATA = {
    "Premier League": [
        ("Manchester City", "MCI"), ("Arsenal", "ARS"), ("Liverpool", "LIV"),
        ("Manchester United", "MUN"), ("Chelsea", "CHE"), ("Tottenham", "TOT"),
    ],
    "La Liga": [
        ("Real Madrid", "RMA"), ("Barcelona", "FCB"), ("Atlético Madrid", "ATM"),
        ("Real Sociedad", "RSO"), ("Athletic Bilbao", "ATH"), ("Sevilla", "SEV"),
    ],
    "Serie A": [
        ("Internazionale", "INT"), ("Milan", "MIL"), ("Juventus", "JUV"),
        ("Napoli", "NAP"), ("Roma", "ROM"), ("Lazio", "LAZ"),
    ],
    "Bundesliga": [
        ("Bayern München", "BAY"), ("Borussia Dortmund", "BVB"), ("RB Leipzig", "RBL"),
        ("Bayer Leverkusen", "B04"), ("Eintracht Frankfurt", "SGE"), ("Wolfsburg", "WOB"),
    ],
    "Brasileirão": [
        ("Flamengo", "FLA"), ("Palmeiras", "PAL"), ("São Paulo", "SAO"),
        ("Corinthians", "COR"), ("Santos", "SAN"), ("Grêmio", "GRE"),
    ],
}

# Forwards/attackers with high shot volumes
SHOOTER_TEMPLATES = [
    {"name": "Erling Haaland", "base_shots": 4.5, "base_sot": 2.8, "consistency": 0.85},
    {"name": "Kylian Mbappé", "base_shots": 3.8, "base_sot": 2.2, "consistency": 0.80},
    {"name": "Harry Kane", "base_shots": 4.2, "base_sot": 2.5, "consistency": 0.88},
    {"name": "Mohamed Salah", "base_shots": 3.5, "base_sot": 2.0, "consistency": 0.82},
    {"name": "Robert Lewandowski", "base_shots": 3.9, "base_sot": 2.3, "consistency": 0.85},
    {"name": "Vinicius Jr", "base_shots": 3.2, "base_sot": 1.8, "consistency": 0.72},
    {"name": "Lautaro Martínez", "base_shots": 3.4, "base_sot": 2.0, "consistency": 0.78},
    {"name": "Victor Osimhen", "base_shots": 3.1, "base_sot": 1.9, "consistency": 0.74},
    {"name": "Pedro (Flamengo)", "base_shots": 3.6, "base_sot": 2.1, "consistency": 0.80},
    {"name": "Endrick", "base_shots": 2.8, "base_sot": 1.6, "consistency": 0.65},
    {"name": "Bukayo Saka", "base_shots": 3.0, "base_sot": 1.7, "consistency": 0.76},
    {"name": "Phil Foden", "base_shots": 2.8, "base_sot": 1.5, "consistency": 0.70},
    {"name": "Cole Palmer", "base_shots": 3.3, "base_sot": 1.9, "consistency": 0.79},
    {"name": "Alexander Isak", "base_shots": 3.2, "base_sot": 1.8, "consistency": 0.75},
    {"name": "Jude Bellingham", "base_shots": 2.9, "base_sot": 1.6, "consistency": 0.73},
    {"name": "Antoine Griezmann", "base_shots": 3.0, "base_sot": 1.7, "consistency": 0.77},
    {"name": "Raphinha", "base_shots": 2.7, "base_sot": 1.4, "consistency": 0.68},
    {"name": "Serhou Guirassy", "base_shots": 3.5, "base_sot": 2.0, "consistency": 0.81},
    {"name": "Loïs Openda", "base_shots": 3.1, "base_sot": 1.8, "consistency": 0.74},
    {"name": "Florian Wirtz", "base_shots": 2.6, "base_sot": 1.4, "consistency": 0.69},
    {"name": "Ciro Immobile", "base_shots": 3.3, "base_sot": 1.9, "consistency": 0.76},
    {"name": "Paulo Dybala", "base_shots": 2.9, "base_sot": 1.6, "consistency": 0.71},
    {"name": "Olivier Giroud", "base_shots": 2.8, "base_sot": 1.5, "consistency": 0.72},
    {"name": "Rafael Leão", "base_shots": 2.7, "base_sot": 1.4, "consistency": 0.66},
    {"name": "Gabriel Martinelli", "base_shots": 2.6, "base_sot": 1.3, "consistency": 0.67},
]

MID_TEMPLATES = [
    {"name": "Kevin De Bruyne", "base_shots": 2.5, "base_sot": 1.2, "consistency": 0.78},
    {"name": "Bruno Fernandes", "base_shots": 2.8, "base_sot": 1.3, "consistency": 0.80},
    {"name": "James Rodríguez", "base_shots": 2.2, "base_sot": 1.0, "consistency": 0.65},
    {"name": "Martin Ødegaard", "base_shots": 2.0, "base_sot": 0.9, "consistency": 0.72},
    {"name": "Federico Valverde", "base_shots": 2.3, "base_sot": 1.1, "consistency": 0.74},
    {"name": "Alexis Mac Allister", "base_shots": 2.1, "base_sot": 1.0, "consistency": 0.70},
    {"name": "De Arrascaeta", "base_shots": 2.4, "base_sot": 1.2, "consistency": 0.73},
    {"name": "Raphinha (Leeds)", "base_shots": 2.3, "base_sot": 1.1, "consistency": 0.69},
]

DEF_TEMPLATES = [
    {"name": "Cristian Romero", "base_shots": 1.2, "base_sot": 0.4, "consistency": 0.55},
    {"name": "Rúben Dias", "base_shots": 0.8, "base_sot": 0.3, "consistency": 0.50},
    {"name": "Virgil van Dijk", "base_shots": 1.0, "base_sot": 0.4, "consistency": 0.60},
    {"name": "Éder Militão", "base_shots": 0.9, "base_sot": 0.3, "consistency": 0.52},
    {"name": "Marquinhos", "base_shots": 0.7, "base_sot": 0.2, "consistency": 0.48},
]


def generate_stats(base_shots: float, base_sot: float, consistency: float, n_games: int = 10) -> list[dict]:
    """Generate n games of synthetic stats for a player."""
    stats = []
    for _ in range(n_games):
        # More consistent players have less variance
        variance = max(0.3, 1.5 - consistency)
        mins = random.randint(60, 95) if random.random() > 0.1 else random.randint(20, 59)

        per90_shots = base_shots + random.gauss(0, base_shots * variance * 0.3)
        per90_sot = base_sot + random.gauss(0, base_sot * variance * 0.3)

        total_shots = max(0, round((per90_shots / 90) * mins))
        shots_ot = max(0, min(total_shots, round((per90_sot / 90) * mins)))

        stats.append({
            "minutes_played": mins,
            "total_shots": total_shots,
            "shots_on_target": shots_ot,
            "goals": random.randint(0, min(2, shots_ot)),
            "assists": random.randint(0, 1),
        })
    return stats


async def seed_database(session):
    """Seed using an existing session (called from API endpoint)."""
    existing = await session.execute(select(League).limit(1))
    if existing.scalar_one_or_none():
        return

    league_map = {}
    team_map = {}

    for league_data in LEAGUES_DATA:
        league = League(name=league_data["name"], country=league_data["country"],
                       external_id=league_data["api_id"], is_active=True)
        session.add(league)
        await session.flush()
        league_map[league.name] = league
        for team_name, short_name in TEAMS_DATA[league.name]:
            team = Team(name=team_name, short_name=short_name, league_id=league.id)
            session.add(team)
            await session.flush()
            team_map[team_name] = team

    player_counts = {"Shooter": 0, "Midfielder": 0, "Defender": 0}
    player_map = {}

    for team_name, team in team_map.items():
        league_name = next(k for k, v in league_map.items() if v.id == team.league_id)
        is_top = league_name in ["Premier League", "La Liga"]
        for template in SHOOTER_TEMPLATES:
            player = Player(name=template["name"], team_id=team.id,
                          position="Forward", nationality=template.get("nationality", "Unknown"))
            session.add(player)
            await session.flush()
            player_map[(team_name, player.name)] = player
            player_counts["Shooter"] += 1
        for template in MID_TEMPLATES[:3]:
            player = Player(name=template["name"], team_id=team.id,
                          position="Midfielder", nationality="Various")
            session.add(player)
            await session.flush()
            player_map[(team_name, player.name)] = player
            player_counts["Midfielder"] += 1

    today = date.today()
    match_id_counter = 1
    for league_name, league in league_map.items():
        teams_in_league = [t for t_name, t in team_map.items()
                          if any(k == league_name for k, v in league_map.items() if v.id == t.league_id)]
        random.shuffle(teams_in_league)
        for i in range(0, len(teams_in_league) - 1, 2):
            home = teams_in_league[i]
            away = teams_in_league[i + 1]
            match = Match(league_id=league.id, home_team_id=home.id,
                         away_team_id=away.id, match_date=today,
                         status="scheduled")
            session.add(match)
            await session.flush()
            for team, side in [(home, "home"), (away, "away")]:
                for (pkey, pname), player in player_map.items():
                    if pkey == team.name:
                        lineup = ExpectedLineup(match_id=match.id, team_id=team.id,
                                              player_id=player.id, is_probable=True)
                        session.add(lineup)
                        stats = generate_stats(3.5, 1.8, 0.75, n_games=10)
                        for s in stats:
                            pms = PlayerMatchStat(player_id=player.id, match_id=match.id,
                                                minutes_played=s["minutes_played"],
                                                total_shots=s["total_shots"],
                                                shots_on_target=s["shots_on_target"],
                                                goals=s["goals"], assists=s["assists"])
                            session.add(pms)

            # Odds
            bookmaker = "Betano"
            for (pkey, pname), player in player_map.items():
                if pkey == home.name or pkey == away.name:
                    avg_sot = sum(
                        g["shots_on_target"] for g in
                        generate_stats(3.5, 1.8, 0.75, n_games=10)
                    ) / 10
                    prob_1 = round(1 - math.exp(-avg_sot), 2)
                    prob_2 = round(1 - math.exp(-avg_sot) - avg_sot * math.exp(-avg_sot), 2)
                    for label, prob in [("Player Shots on Target", prob_1),
                                       ("Player Shots on Target 2+", prob_2)]:
                        fair_odds = round(1.0 / prob, 2) if prob > 0 else 10.0
                        market_odds = round(fair_odds * random.uniform(0.85, 1.10), 2)
                        odds = Odds(match_id=match.id, bookmaker=bookmaker,
                                  market=f"{label} (Player Props)", player_id=player.id,
                                  selection=pname.split()[-1], odds_value=market_odds)
                        session.add(odds)
            match_id_counter += 1

    await session.commit()


async def seed():
    print("Creating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        # Check if already seeded
        existing = await session.execute(select(League).limit(1))
        if existing.scalar_one_or_none():
            print("Database already seeded. Skipping.")
            return

        print("Seeding leagues and teams...")
        league_map = {}
        team_map = {}

        for league_data in LEAGUES_DATA:
            league = League(name=league_data["name"], country=league_data["country"],
                          external_id=league_data["api_id"], is_active=True)
            session.add(league)
            await session.flush()
            league_map[league.name] = league

            for team_name, short_name in TEAMS_DATA[league.name]:
                team = Team(name=team_name, short_name=short_name, league_id=league.id)
                session.add(team)
                await session.flush()
                team_map[team_name] = team

        print("Seeding players...")
        player_map = {}  # team_name -> [player_ids]

        for league_name, teams in TEAMS_DATA.items():
            for team_name, _ in teams:
                team = team_map[team_name]
                player_map[team_name] = []

                # 3-4 attackers/shooters per team
                n_shooters = random.randint(3, 4)
                shooters = random.sample(SHOOTER_TEMPLATES, n_shooters)
                for tpl in shooters:
                    name_suffix = f"({team_name[:3]})" if tpl["name"].count("(") == 0 else ""
                    full_name = tpl["name"].split("(")[0].strip() + name_suffix if "(" not in tpl["name"] else tpl["name"]
                    player = Player(
                        name=full_name,
                        team_id=team.id,
                        position="Attacker" if "(" not in tpl["name"] else "Forward",
                    )
                    session.add(player)
                    await session.flush()
                    player_map[team_name].append((player.id, tpl))

                # 2 midfielders
                mids = random.sample(MID_TEMPLATES, 2)
                for tpl in mids:
                    player = Player(name=tpl["name"], team_id=team.id, position="Midfielder")
                    session.add(player)
                    await session.flush()
                    player_map[team_name].append((player.id, tpl))

                # 1 defender who shoots
                def_tpl = random.choice(DEF_TEMPLATES)
                player = Player(name=def_tpl["name"], team_id=team.id, position="Defender")
                session.add(player)
                await session.flush()
                player_map[team_name].append((player.id, def_tpl))

        await session.commit()

        print("Seeding matches and stats...")
        today = date.today()
        match_id_counter = 1

        for league_name, teams in TEAMS_DATA.items():
            league = league_map[league_name]
            # Pair teams: (0v1, 2v3, 4v5)
            for i in range(0, len(teams), 2):
                home_name, _ = teams[i]
                away_name, _ = teams[i + 1]
                home_team = team_map[home_name]
                away_team = team_map[away_name]

                match = Match(
                    league_id=league.id,
                    home_team_id=home_team.id,
                    away_team_id=away_team.id,
                    match_date=today,
                    status=MatchStatus.SCHEDULED,
                )
                session.add(match)
                await session.flush()
                match_id_counter += 1

                # For each player in both teams, generate 10-game history + lineup
                for team_name, team_obj in [(home_name, home_team), (away_name, away_team)]:
                    for player_id, tpl in player_map[team_name]:
                        stats_list = generate_stats(tpl["base_shots"], tpl["base_sot"], tpl["consistency"], 10)

                        # Insert match stats (simulated past games)
                        for game_idx, s in enumerate(stats_list):
                            past_date = today - timedelta(days=(game_idx + 1) * 3)
                            past_match = Match(
                                league_id=league.id,
                                home_team_id=home_team.id,
                                away_team_id=away_team.id,
                                match_date=past_date,
                                status=MatchStatus.FINISHED,
                                home_score=random.randint(0, 4),
                                away_score=random.randint(0, 4),
                            )
                            session.add(past_match)
                            await session.flush()

                            stat = PlayerMatchStats(
                                player_id=player_id,
                                match_id=past_match.id,
                                minutes_played=s["minutes_played"],
                                total_shots=s["total_shots"],
                                shots_on_target=s["shots_on_target"],
                                goals=s["goals"],
                                assists=s["assists"],
                            )
                            session.add(stat)

                        # Expected lineup (probable starters)
                        lineup = ExpectedLineup(
                            match_id=match.id,
                            team_id=team_obj.id,
                            player_id=player_id,
                            is_probable=True,
                            is_injured=False,
                            is_suspended=False,
                        )
                        session.add(lineup)

                        # Calc player form from the 10 games
                        total_shots_list = [s["total_shots"] for s in stats_list]
                        total_sot_list = [s["shots_on_target"] for s in stats_list]
                        minutes_list = [s["minutes_played"] for s in stats_list]

                        per90_shots = []
                        per90_sot = []
                        for s in stats_list:
                            if s["minutes_played"] >= 15:
                                per90_shots.append((s["total_shots"] / s["minutes_played"]) * 90)
                                per90_sot.append((s["shots_on_target"] / s["minutes_played"]) * 90)

                        avg_shots = sum(per90_shots) / len(per90_shots) if per90_shots else 0
                        avg_sot = sum(per90_sot) / len(per90_sot) if per90_sot else 0

                        if per90_shots:
                            mean = sum(per90_shots) / len(per90_shots)
                            variance = sum((x - mean) ** 2 for x in per90_shots) / len(per90_shots)
                            cv = math.sqrt(variance) / mean if mean > 0 else 1.0
                            consistency_score = max(0.0, 1.0 - min(cv, 1.5) / 1.5)
                        else:
                            consistency_score = 0.0

                        form = PlayerForm(
                            player_id=player_id,
                            games_analyzed=10,
                            avg_total_shots=round(avg_shots, 3),
                            avg_shots_on_target=round(avg_sot, 3),
                            avg_minutes_played=round(sum(minutes_list) / len(minutes_list), 1),
                            consistency_score=round(consistency_score, 3),
                        )
                        session.add(form)

                # Generate odds for the match
                bookmaker = "Betano"
                for team_name, _ in [(home_name, home_team), (away_name, away_team)]:
                    for player_id, tpl in player_map[team_name]:
                        # Map player stats to odds
                        base_prob = min(0.95, max(0.3, tpl["base_sot"] / 3.5))
                        for label, multiplier in [
                            ("Player Shots on Target - Over 0.5", 0.92),
                            ("Player Shots on Target - Over 1.5", 0.55),
                            ("Player Total Shots - Over 1.5", 0.65),
                        ]:
                            pseudo_prob = base_prob * multiplier
                            # Add some market inefficiency for value bet detection
                            fair_odds = 1.0 / pseudo_prob if pseudo_prob > 0 else 10.0
                            # Randomly inflate odds (creating value ~20% of the time)
                            if random.random() < 0.2:
                                market_odds = round(fair_odds * random.uniform(1.3, 1.8), 2)
                            else:
                                market_odds = round(fair_odds * random.uniform(0.85, 1.10), 2)

                            player_obj = await session.get(Player, player_id)
                            player_name = player_obj.name if player_obj else "Unknown"

                            odds = Odds(
                                match_id=match.id,
                                bookmaker=bookmaker,
                                market=label,
                                player_id=player_id,
                                selection=f"{player_name} - {label}",
                                odds_value=market_odds,
                            )
                            session.add(odds)

                await session.commit()
                print(f"  Match: {home_name} vs {away_name} ({league_name})")

        print("\nSeed complete!")
        print(f"  Leagues: {len(LEAGUES_DATA)}")
        print(f"  Teams: {sum(len(t) for t in TEAMS_DATA.values())}")
        print(f"  Players: ~{sum(len(p) for p in player_map.values())}")
        print(f"  Today's matches: {match_id_counter - 1}")


if __name__ == "__main__":
    asyncio.run(seed())
