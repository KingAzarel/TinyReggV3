from datetime import date

from core.db import get_connection
from core.task_engine import generate_daily_tasks, reassess_tasks_for_profile
from core.presence import get_active_profile


# ─────────────────────────────────────────────
# DATE (single source of truth)
# ─────────────────────────────────────────────

def _today() -> str:
    return date.today().isoformat()


# ─────────────────────────────────────────────
# DAILY RESET
# ─────────────────────────────────────────────

def reset_daily_tasks(user_id: str, profile_id: int):
    """
    Called once per day by the scheduler.

    Responsibilities:
    - clear previous days' assigned tasks
    - clear previous days' task history
    - generate today's tasks via task_engine
    """

    today = _today()

    conn = get_connection()
    cur = conn.cursor()

    # Clear assigned tasks before today
    cur.execute(
        """
        DELETE FROM assigned_tasks
        WHERE profile_id = ?
          AND date < ?
        """,
        (profile_id, today),
    )

    # Clear task history before today
    cur.execute(
        """
        DELETE FROM task_history
        WHERE profile_id = ?
          AND date < ?
        """,
        (profile_id, today),
    )

    conn.commit()
    conn.close()

    # Generate today's tasks (engine owns all logic)
    return generate_daily_tasks(profile_id)


# ─────────────────────────────────────────────
# MID-DAY PRESENCE CHANGE
# ─────────────────────────────────────────────

def reassess_tasks_on_presence_change(user_id: str, profile_id: int):
    """
    Called when presence/fronting changes mid-day.

    Responsibilities:
    - remove tasks that are no longer allowed
    - regenerate tasks safely
    """

    profile = get_active_profile(user_id)
    if not profile:
        return

    # Delegate fully to the canonical engine
    reassess_tasks_for_profile(profile_id)
