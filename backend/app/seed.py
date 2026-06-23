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
from app.models.value_bet import ValueBet
from app.models.player_form import PlayerForm

LEAGUES_DATA = [
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
    {"name": "Championship", "country": "England", "api_id": 40},
    {"name": "Liga MX", "country": "Mexico", "api_id": 262},
    {"name": "J-League", "country": "Japan", "api_id": 98},
]

TEAMS_DATA = {
    "Premier League": [
        ("Manchester City", "MCI"), ("Arsenal", "ARS"), ("Liverpool", "LIV"),
        ("Manchester United", "MUN"), ("Chelsea", "CHE"), ("Tottenham", "TOT"),
        ("Aston Villa", "AVL"), ("Newcastle", "NEW"), ("West Ham", "WHU"),
        ("Brighton", "BRI"),
    ],
    "La Liga": [
        ("Real Madrid", "RMA"), ("Barcelona", "FCB"), ("Atlético Madrid", "ATM"),
        ("Real Sociedad", "RSO"), ("Athletic Bilbao", "ATH"), ("Sevilla", "SEV"),
        ("Villarreal", "VIL"), ("Betis", "BET"), ("Valencia", "VAL"),
    ],
    "Serie A": [
        ("Internazionale", "INT"), ("Milan", "MIL"), ("Juventus", "JUV"),
        ("Napoli", "NAP"), ("Roma", "ROM"), ("Lazio", "LAZ"),
        ("Atalanta", "ATA"), ("Fiorentina", "FIO"), ("Bologna", "BOL"),
    ],
    "Bundesliga": [
        ("Bayern München", "BAY"), ("Borussia Dortmund", "BVB"), ("RB Leipzig", "RBL"),
        ("Bayer Leverkusen", "B04"), ("Eintracht Frankfurt", "SGE"), ("Wolfsburg", "WOB"),
        ("Stuttgart", "STU"), ("Freiburg", "FRE"),
    ],
    "Brasileirão": [
        ("Flamengo", "FLA"), ("Palmeiras", "PAL"), ("São Paulo", "SAO"),
        ("Corinthians", "COR"), ("Santos", "SAN"), ("Grêmio", "GRE"),
        ("Botafogo", "BOT"), ("Fluminense", "FLU"), ("Cruzeiro", "CRU"),
        ("Internacional", "INT"),
    ],
    "Ligue 1": [
        ("Paris SG", "PSG"), ("Marseille", "MAR"), ("Monaco", "MON"),
        ("Lyon", "LYO"), ("Lille", "LIL"), ("Nice", "NIC"),
        ("Rennes", "REN"), ("Lens", "LEN"), ("Strasbourg", "STR"),
        ("Toulouse", "TOU"),
    ],
    "Argentine League": [
        ("River Plate", "RIV"), ("Boca Juniors", "BOC"), ("Independiente", "IND"),
        ("Racing Club", "RAC"), ("San Lorenzo", "SLO"), ("Vélez Sarsfield", "VEL"),
        ("Estudiantes", "EST"), ("Rosario Central", "RCA"), ("Talleres", "TAL"),
        ("Unión", "UNI"),
    ],
    "MLS": [
        ("Inter Miami", "MIA"), ("LAFC", "LAF"), ("LA Galaxy", "LAG"),
        ("Atlanta United", "ATL"), ("NYCFC", "NYC"), ("Seattle Sounders", "SEA"),
        ("Columbus Crew", "CLB"), ("Philadelphia Union", "PHI"), ("FC Dallas", "DAL"),
        ("Portland Timbers", "POR"),
    ],
    "Eredivisie": [
        ("Ajax", "AJA"), ("PSV", "PSV"), ("Feyenoord", "FEY"),
        ("Twente", "TWE"), ("AZ Alkmaar", "AZ"), ("Utrecht", "UTR"),
        ("Sparta Rotterdam", "SPA"), ("NEC", "NEC"), ("Heerenveen", "HEE"),
        ("Go Ahead Eagles", "GAE"),
    ],
    "Primeira Liga": [
        ("Benfica", "BEN"), ("Porto", "POR"), ("Sporting CP", "SPO"),
        ("Braga", "BRA"), ("Vitória Guimarães", "GUI"), ("Famalicão", "FAM"),
        ("Casa Pia", "CAS"), ("Moreirense", "MOR"), ("Arouca", "ARO"),
        ("Rio Ave", "RIO"),
    ],
    "Champions League": [
        ("Real Madrid", "RMA"), ("Manchester City", "MCI"), ("Bayern München", "BAY"),
        ("Paris SG", "PSG"), ("Barcelona", "FCB"), ("Arsenal", "ARS"),
        ("Inter Milan", "INT"), ("Borussia Dortmund", "BVB"),
    ],
    "Europa League": [
        ("Manchester United", "MUN"), ("Tottenham", "TOT"), ("Roma", "ROM"),
        ("Lazio", "LAZ"), ("Atalanta", "ATA"), ("Lyon", "LYO"),
        ("Marseille", "MAR"), ("Porto", "POR"), ("Ajax", "AJA"),
        ("Fenerbahçe", "FEN"),
    ],
    "World Cup": [
        ("Brasil", "BRA"), ("Argentina", "ARG"), ("França", "FRA"),
        ("Inglaterra", "ENG"), ("Espanha", "ESP"), ("Alemanha", "ALE"),
        ("Portugal", "POR"), ("Holanda", "HOL"),
    ],
    "Copa America": [
        ("Brasil", "BRA"), ("Argentina", "ARG"), ("Uruguai", "URU"),
        ("Colômbia", "COL"), ("Equador", "EQU"), ("Peru", "PER"),
        ("Chile", "CHI"), ("Paraguai", "PAR"), ("Venezuela", "VEN"),
        ("Bolívia", "BOL"),
    ],
    "Copa do Brasil": [
        ("Flamengo", "FLA"), ("Palmeiras", "PAL"), ("São Paulo", "SAO"),
        ("Corinthians", "COR"), ("Grêmio", "GRE"), ("Atlético MG", "CAM"),
        ("Cruzeiro", "CRU"), ("Botafogo", "BOT"), ("Fluminense", "FLU"),
        ("Internacional", "INT"),
    ],
    "Série B": [
        ("Santos", "SAN"), ("Sport Recife", "SPO"), ("Novorizontino", "NOV"),
        ("Mirassol", "MIR"), ("Vila Nova", "VIL"), ("Ceará", "CEA"),
        ("Goiás", "GOI"), ("Amazonas", "AMA"), ("Coritiba", "CBT"),
        ("Atlético GO", "ACG"),
    ],
    "Championship": [
        ("Leeds United", "LEE"), ("Leicester City", "LEI"), ("Ipswich Town", "IPS"),
        ("Southampton", "SOU"), ("West Brom", "WBA"), ("Norwich City", "NOR"),
        ("Coventry City", "COV"), ("Watford", "WAT"), ("Middlesbrough", "MID"),
        ("Hull City", "HUL"),
    ],
    "Liga MX": [
        ("América", "AME"), ("Chivas", "CHI"), ("Cruz Azul", "CRU"),
        ("Monterrey", "MTY"), ("Tigres", "TIG"), ("Pumas", "PUM"),
        ("Toluca", "TOL"), ("Pachuca", "PAC"), ("León", "LEO"),
        ("Santos Laguna", "SAN"),
    ],
    "J-League": [
        ("Vissel Kobe", "VIS"), ("Yokohama F. Marinos", "YFM"), ("Kawasaki Frontale", "KAW"),
        ("Urawa Reds", "URA"), ("Nagoya Grampus", "NAG"), ("Sanfrecce Hiroshima", "SAN"),
        ("Cerezo Osaka", "CER"), ("FC Tokyo", "FCT"), ("Kashiwa Reysol", "KAS"),
        ("Avispa Fukuoka", "AVI"),
    ],
}

SHOOTER_TEMPLATES = [
    {"name": "Erling Haaland", "base_shots": 4.5, "base_sot": 2.8, "consistency": 0.85},
    {"name": "Kylian Mbappé", "base_shots": 3.8, "base_sot": 2.2, "consistency": 0.80},
    {"name": "Harry Kane", "base_shots": 4.2, "base_sot": 2.5, "consistency": 0.88},
    {"name": "Mohamed Salah", "base_shots": 3.5, "base_sot": 2.0, "consistency": 0.82},
    {"name": "Robert Lewandowski", "base_shots": 3.9, "base_sot": 2.3, "consistency": 0.85},
    {"name": "Vinicius Jr", "base_shots": 3.2, "base_sot": 1.8, "consistency": 0.72},
    {"name": "Lautaro Martínez", "base_shots": 3.4, "base_sot": 2.0, "consistency": 0.78},
    {"name": "Victor Osimhen", "base_shots": 3.1, "base_sot": 1.9, "consistency": 0.74},
    {"name": "Pedro", "base_shots": 3.6, "base_sot": 2.1, "consistency": 0.80},
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
    {"name": "Neymar", "base_shots": 3.3, "base_sot": 1.7, "consistency": 0.70},
    {"name": "Lionel Messi", "base_shots": 3.8, "base_sot": 2.1, "consistency": 0.83},
    {"name": "Cristiano Ronaldo", "base_shots": 4.0, "base_sot": 2.2, "consistency": 0.82},
    {"name": "Nico Williams", "base_shots": 2.5, "base_sot": 1.2, "consistency": 0.65},
    {"name": "Lamine Yamal", "base_shots": 2.3, "base_sot": 1.1, "consistency": 0.60},
    {"name": "Gabriel Jesus", "base_shots": 3.1, "base_sot": 1.6, "consistency": 0.71},
    {"name": "Richarlison", "base_shots": 2.9, "base_sot": 1.5, "consistency": 0.68},
    {"name": "Rodrygo", "base_shots": 2.7, "base_sot": 1.4, "consistency": 0.69},
    {"name": "Darwin Núñez", "base_shots": 3.4, "base_sot": 1.8, "consistency": 0.66},
    {"name": "Marcus Rashford", "base_shots": 2.8, "base_sot": 1.5, "consistency": 0.67},
    {"name": "Rasmus Højlund", "base_shots": 2.9, "base_sot": 1.6, "consistency": 0.68},
    {"name": "Alejandro Garnacho", "base_shots": 2.4, "base_sot": 1.2, "consistency": 0.63},
    {"name": "Kobbie Mainoo", "base_shots": 1.8, "base_sot": 0.8, "consistency": 0.65},
    {"name": "Dejan Kulusevski", "base_shots": 2.5, "base_sot": 1.3, "consistency": 0.70},
    {"name": "Heung-Min Son", "base_shots": 3.2, "base_sot": 1.8, "consistency": 0.78},
]

MID_TEMPLATES = [
    {"name": "Kevin De Bruyne", "base_shots": 2.5, "base_sot": 1.2, "consistency": 0.78},
    {"name": "Bruno Fernandes", "base_shots": 2.8, "base_sot": 1.3, "consistency": 0.80},
    {"name": "Martin Ødegaard", "base_shots": 2.0, "base_sot": 0.9, "consistency": 0.72},
    {"name": "Federico Valverde", "base_shots": 2.3, "base_sot": 1.1, "consistency": 0.74},
    {"name": "Alexis Mac Allister", "base_shots": 2.1, "base_sot": 1.0, "consistency": 0.70},
    {"name": "De Arrascaeta", "base_shots": 2.4, "base_sot": 1.2, "consistency": 0.73},
    {"name": "James Rodríguez", "base_shots": 2.2, "base_sot": 1.0, "consistency": 0.65},
    {"name": "Rodri", "base_shots": 1.8, "base_sot": 0.7, "consistency": 0.80},
    {"name": "Declan Rice", "base_shots": 1.5, "base_sot": 0.6, "consistency": 0.75},
    {"name": "Bernardo Silva", "base_shots": 1.9, "base_sot": 0.8, "consistency": 0.76},
    {"name": "Pedri", "base_shots": 1.6, "base_sot": 0.7, "consistency": 0.72},
    {"name": "Gavi", "base_shots": 1.7, "base_sot": 0.7, "consistency": 0.68},
    {"name": "Eduardo Camavinga", "base_shots": 1.8, "base_sot": 0.8, "consistency": 0.70},
    {"name": "Aurélien Tchouaméni", "base_shots": 1.5, "base_sot": 0.6, "consistency": 0.73},
    {"name": "Enzo Fernández", "base_shots": 2.0, "base_sot": 0.9, "consistency": 0.71},
    {"name": "Douglas Luiz", "base_shots": 1.9, "base_sot": 0.8, "consistency": 0.72},
]

DEF_TEMPLATES = [
    {"name": "Virgil van Dijk", "base_shots": 1.0, "base_sot": 0.4, "consistency": 0.60},
    {"name": "Rúben Dias", "base_shots": 0.8, "base_sot": 0.3, "consistency": 0.50},
    {"name": "Cristian Romero", "base_shots": 1.2, "base_sot": 0.4, "consistency": 0.55},
    {"name": "Éder Militão", "base_shots": 0.9, "base_sot": 0.3, "consistency": 0.52},
    {"name": "Marquinhos", "base_shots": 0.7, "base_sot": 0.2, "consistency": 0.48},
    {"name": "Gabriel Magalhães", "base_shots": 1.1, "base_sot": 0.4, "consistency": 0.58},
    {"name": "William Saliba", "base_shots": 0.6, "base_sot": 0.2, "consistency": 0.55},
    {"name": "Josko Gvardiol", "base_shots": 1.0, "base_sot": 0.3, "consistency": 0.57},
    {"name": "Antonio Rüdiger", "base_shots": 1.1, "base_sot": 0.4, "consistency": 0.56},
    {"name": "John Stones", "base_shots": 0.8, "base_sot": 0.3, "consistency": 0.54},
]


def generate_stats(base_shots: float, base_sot: float, consistency: float, n_games: int = 10) -> list[dict]:
    stats = []
    for _ in range(n_games):
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


async def seed_database():
    """Drop all tables, recreate, and seed with fresh data."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        league_map = {}
        team_map = {}

        for ld in LEAGUES_DATA:
            league = League(name=ld["name"], country=ld["country"], external_id=ld["api_id"], is_active=True)
            session.add(league)
            await session.flush()
            league_map[ld["name"]] = league
            for tname, short in TEAMS_DATA[ld["name"]]:
                team = Team(name=tname, short_name=short, league_id=league.id)
                session.add(team)
                await session.flush()
                team_map[tname] = team

        player_map = {}
        for tname, team in team_map.items():
            for tpl in SHOOTER_TEMPLATES:
                p = Player(name=f"{tpl['name']} ({tname[:3]})", team_id=team.id, position="Forward")
                session.add(p)
                await session.flush()
                player_map.setdefault(team.id, []).append((p.id, tpl))
            for tpl in MID_TEMPLATES[:2]:
                p = Player(name=f"{tpl['name']} ({tname[:3]})", team_id=team.id, position="Midfielder")
                session.add(p)
                await session.flush()
                player_map.setdefault(team.id, []).append((p.id, tpl))
            for tpl in DEF_TEMPLATES[:1]:
                p = Player(name=f"{tpl['name']} ({tname[:3]})", team_id=team.id, position="Defender")
                session.add(p)
                await session.flush()
                player_map.setdefault(team.id, []).append((p.id, tpl))

        today = date.today()
        for league_name, league in league_map.items():
            teams_in_league = [(tname, team_map[tname]) for tname, _ in TEAMS_DATA[league_name]]
            random.shuffle(teams_in_league)
            for i in range(0, len(teams_in_league) - 1, 2):
                hname, home = teams_in_league[i]
                aname, away = teams_in_league[i + 1]
                match = Match(league_id=league.id, home_team_id=home.id, away_team_id=away.id,
                              match_date=today, status=MatchStatus.SCHEDULED)
                session.add(match)
                await session.flush()

                for team, tname in [(home, hname), (away, aname)]:
                    for pid, tpl in player_map[team.id]:
                        session.add(ExpectedLineup(match_id=match.id, team_id=team.id,
                                                    player_id=pid, is_probable=True))
                        stats_list = generate_stats(tpl["base_shots"], tpl["base_sot"], tpl["consistency"], 10)
                        for gi, s in enumerate(stats_list):
                            past_date = today - timedelta(days=(gi + 1) * 3)
                            pm = Match(league_id=league.id, home_team_id=home.id, away_team_id=away.id,
                                        match_date=past_date, status=MatchStatus.FINISHED)
                            session.add(pm)
                            await session.flush()
                            session.add(PlayerMatchStats(player_id=pid, match_id=pm.id, **s))

                        per90_shots = [((s["total_shots"] / max(s["minutes_played"], 1)) * 90) for s in stats_list if s["minutes_played"] >= 15]
                        per90_sot = [((s["shots_on_target"] / max(s["minutes_played"], 1)) * 90) for s in stats_list if s["minutes_played"] >= 15]
                        avg_shots = sum(per90_shots) / len(per90_shots) if per90_shots else 0
                        avg_sot = sum(per90_sot) / len(per90_sot) if per90_sot else 0
                        mean = sum(per90_shots) / len(per90_shots) if per90_shots else 0
                        cv = (math.sqrt(sum((x - mean) ** 2 for x in per90_shots) / len(per90_shots)) / mean) if mean > 0 and per90_shots else 1.0
                        session.add(PlayerForm(player_id=pid, games_analyzed=10,
                            avg_total_shots=round(avg_shots, 3), avg_shots_on_target=round(avg_sot, 3),
                            consistency_score=round(max(0.0, 1.0 - min(cv, 1.5) / 1.5), 3)))

                for team, tname in [(home, hname), (away, aname)]:
                    for pid, tpl in player_map[team.id]:
                        base_prob = min(0.95, max(0.3, tpl["base_sot"] / 3.5))
                        for label, mult in [("Player Shots on Target - Over 0.5", 0.92),
                                            ("Player Shots on Target - Over 1.5", 0.55)]:
                            pp = base_prob * mult
                            fo = 1.0 / pp if pp > 0 else 10.0
                            mo = round(fo * random.uniform(1.3, 1.8), 2) if random.random() < 0.2 else round(fo * random.uniform(0.85, 1.10), 2)
                            session.add(Odds(match_id=match.id, bookmaker="Betano", market=label,
                                              player_id=pid, selection=label, odds_value=mo))

        await session.commit()
