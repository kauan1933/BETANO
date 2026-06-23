"""
APScheduler setup for periodic data refresh tasks.
"""

import logging
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.tasks.refresh import (
    refresh_today_matches,
    refresh_player_stats,
    refresh_odds,
    calculate_all_probabilities,
    detect_value_bets,
)

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


async def start_scheduler():
    """Initialize and start all periodic jobs."""

    # Fetch today's matches every 15 minutes
    scheduler.add_job(
        refresh_today_matches,
        trigger="interval",
        minutes=15,
        id="refresh_matches",
        replace_existing=True,
        next_run_time=datetime.now(timezone.utc),
    )

    # Refresh player stats every 30 minutes
    scheduler.add_job(
        refresh_player_stats,
        trigger="interval",
        minutes=30,
        id="refresh_player_stats",
        replace_existing=True,
    )

    # Refresh odds every 5 minutes
    scheduler.add_job(
        refresh_odds,
        trigger="interval",
        minutes=5,
        id="refresh_odds",
        replace_existing=True,
    )

    # Recalculate probabilities every 30 minutes
    scheduler.add_job(
        calculate_all_probabilities,
        trigger="interval",
        minutes=30,
        id="calc_probabilities",
        replace_existing=True,
    )

    # Detect value bets every 10 minutes
    scheduler.add_job(
        detect_value_bets,
        trigger="interval",
        minutes=10,
        id="detect_value_bets",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler started with all periodic jobs.")
    logger.info("  - Today's matches: every 15 min")
    logger.info("  - Player stats: every 30 min")
    logger.info("  - Odds: every 5 min")
    logger.info("  - Probabilities: every 30 min")
    logger.info("  - Value bets: every 10 min")


async def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped.")
