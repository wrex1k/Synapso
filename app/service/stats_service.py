from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from app.repository.activity_repository import get_time_played
from app.repository.run_repository import fetch_user_run_history, parse_datetime
from app.repository.stats_repository import (
    fetch_all_user_stats,
    fetch_player_game_stats,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

def calculate_user_streak(histories: dict[str, list[dict]]) -> int:
    """Calculate consecutive days with activity from today backwards."""
    today = datetime.now().astimezone().date()
    days = set()
    
    for hist in histories.values():
        for row in hist or []:
            dt = parse_datetime(row.get("started_at"))
            if dt is not None and dt.date() <= today:
                days.add(dt.date())
    
    if not days:
        return 0
    
    cursor = today if today in days else today - timedelta(days=1)
    streak = 0
    
    while cursor in days:
        streak += 1
        cursor -= timedelta(days=1)
    
    return streak

def estimate_daily_goal(histories: dict[str, list[dict]]) -> int:
    """Estimate daily goal from average runs per day in history."""
    runs_by_day: dict[Any, int] = {}
    
    for hist in histories.values():
        for row in hist or []:
            dt = parse_datetime(row.get("started_at"))
            if dt is None:
                continue
            day = dt.date()
            runs_by_day[day] = runs_by_day.get(day, 0) + 1
    
    if not runs_by_day:
        return 3
    
    avg = sum(runs_by_day.values()) / len(runs_by_day)
    return max(1, round(avg))

def calculate_goal_status(done: int, goal: int) -> dict[str, Any]:
    """Calculate daily goal progress and completion status."""
    shown_done = min(done, goal) if goal > 0 else done
    remaining = max(goal - done, 0)
    
    if done >= goal and goal > 0:
        status = "completed"
    elif done == 0:
        status = "not_started"
    else:
        status = "in_progress"
    
    return {
        "goal": goal,
        "done": done,
        "shown_done": shown_done,
        "remaining": remaining,
        "status": status,
    }

def get_dashboard_stats(
    user_id: str,
    game_slugs: list[str],
    history_limit: int | None = None,
) -> dict[str, Any]:
    """Get comprehensive dashboard statistics for all games."""
    try:
        time_played_total = get_time_played(user_id) or 0
    except Exception:
        logger.exception("Failed to get time played for user ..%s", user_id[-10:])
        time_played_total = 0
    
    try:
        all_stats = fetch_all_user_stats(user_id) or {"games": []}
    except Exception:
        logger.exception("Failed to get all user stats for user ..%s", user_id[-10:])
        all_stats = {"games": []}
    
    per_game: dict[str, dict | None] = {}
    histories: dict[str, list[dict]] = {}
    
    for slug in game_slugs:
        try:
            per_game[slug] = fetch_player_game_stats(user_id, slug)
        except Exception:
            logger.exception("Failed to get stats for game %s", slug)
            per_game[slug] = None
            
        try:
            histories[slug] = fetch_user_run_history(user_id, slug, limit=history_limit) or []
        except Exception:
            logger.exception("Failed to get history for game %s", slug)
            histories[slug] = []
    
    return {
        "time_played_total": time_played_total,
        "all_stats": all_stats,
        "per_game": per_game,
        "histories": histories,
    }
