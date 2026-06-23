"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-06-23

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "leagues",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("country", sa.String(100), nullable=False),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("external_id", sa.String(50), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("external_id"),
    )
    op.create_index("ix_leagues_name", "leagues", ["name"])

    op.create_table(
        "teams",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("short_name", sa.String(10), nullable=True),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("league_id", sa.Integer(), nullable=False),
        sa.Column("external_id", sa.String(50), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["league_id"], ["leagues.id"]),
        sa.UniqueConstraint("external_id"),
    )

    op.create_table(
        "players",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.String(50), nullable=True),
        sa.Column("nationality", sa.String(100), nullable=True),
        sa.Column("photo_url", sa.String(500), nullable=True),
        sa.Column("external_id", sa.String(50), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"]),
        sa.UniqueConstraint("external_id"),
    )
    op.create_index("ix_players_name", "players", ["name"])

    op.create_table(
        "matches",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("league_id", sa.Integer(), nullable=False),
        sa.Column("home_team_id", sa.Integer(), nullable=False),
        sa.Column("away_team_id", sa.Integer(), nullable=False),
        sa.Column("match_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(20), default="scheduled"),
        sa.Column("home_score", sa.Integer(), nullable=True),
        sa.Column("away_score", sa.Integer(), nullable=True),
        sa.Column("external_id", sa.String(50), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["league_id"], ["leagues.id"]),
        sa.ForeignKeyConstraint(["home_team_id"], ["teams.id"]),
        sa.ForeignKeyConstraint(["away_team_id"], ["teams.id"]),
        sa.UniqueConstraint("external_id"),
    )
    op.create_index("ix_matches_date", "matches", ["match_date"])

    op.create_table(
        "player_match_stats",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("match_id", sa.Integer(), nullable=False),
        sa.Column("minutes_played", sa.Integer(), default=0),
        sa.Column("total_shots", sa.Integer(), default=0),
        sa.Column("shots_on_target", sa.Integer(), default=0),
        sa.Column("goals", sa.Integer(), default=0),
        sa.Column("assists", sa.Integer(), default=0),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"]),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"]),
        sa.UniqueConstraint("player_id", "match_id", name="uq_player_match"),
    )
    op.create_index("ix_stats_player", "player_match_stats", ["player_id"])

    op.create_table(
        "expected_lineups",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("match_id", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("is_probable", sa.Boolean(), default=True),
        sa.Column("is_injured", sa.Boolean(), default=False),
        sa.Column("is_suspended", sa.Boolean(), default=False),
        sa.Column("source", sa.String(50), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"]),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"]),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"]),
        sa.UniqueConstraint("match_id", "player_id", name="uq_lineup_player"),
    )

    op.create_table(
        "odds",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("match_id", sa.Integer(), nullable=False),
        sa.Column("bookmaker", sa.String(50), nullable=False),
        sa.Column("market", sa.String(100), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=True),
        sa.Column("selection", sa.String(200), nullable=False),
        sa.Column("odds_value", sa.Float(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"]),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"]),
    )

    op.create_table(
        "value_bets",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("match_id", sa.Integer(), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("market", sa.String(100), nullable=False),
        sa.Column("calc_probability", sa.Float(), nullable=False),
        sa.Column("market_odds", sa.Float(), nullable=False),
        sa.Column("implied_probability", sa.Float(), nullable=False),
        sa.Column("expected_value", sa.Float(), nullable=False),
        sa.Column("confidence", sa.String(20), nullable=True),
        sa.Column("status", sa.String(20), default="active"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"]),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"]),
    )

    op.create_table(
        "player_form",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("games_analyzed", sa.Integer(), default=0),
        sa.Column("avg_total_shots", sa.Float(), default=0.0),
        sa.Column("avg_shots_on_target", sa.Float(), default=0.0),
        sa.Column("avg_minutes_played", sa.Float(), default=0.0),
        sa.Column("consistency_score", sa.Float(), default=0.0),
        sa.Column("last_updated", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_form_player", "player_form", ["player_id"])


def downgrade() -> None:
    op.drop_table("value_bets")
    op.drop_table("odds")
    op.drop_table("expected_lineups")
    op.drop_table("player_form")
    op.drop_table("player_match_stats")
    op.drop_table("matches")
    op.drop_table("players")
    op.drop_table("teams")
    op.drop_table("leagues")
