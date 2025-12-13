from core.db import get_connection
from core.task_engine import generate_daily_tasks
from core.presence import get_current_presence


# ─────────────────────────────────────────────
# DAILY RESET
# ─────────────────────────────────────────────

def reset_daily_tasks(user_id, profile_id):
    """
    Called once per day by the scheduler.

    Responsibilities:
    - clear yesterday's assigned tasks
    - reset hidden state
    - generate today's tasks via task_engine
    """

    conn = get_connection()
    cur = conn.cursor()

    # 1️⃣ Clear old assigned tasks (yesterday and earlier)
    cur.execute(
        """
        DELETE FROM assigned_tasks
        WHERE profile_id = ?
          AND date < DATE('now')
        """,
        (profile_id,),
    )

    # 2️⃣ Clear old task history (optional but recommended)
    cur.execute(
        """
        DELETE FROM task_history
        WHERE profile_id = ?
          AND date < DATE('now')
        """,
        (profile_id,),
    )

    conn.commit()
    conn.close()

    # 3️⃣ Generate today's tasks (engine handles everything)
    return generate_daily_tasks(
        user_id=user_id,
        profile_id=profile_id,
    )


# ─────────────────────────────────────────────
# MID-DAY PRESENCE RESET
# ─────────────────────────────────────────────

def reassess_tasks_on_presence_change(user_id, profile_id):
    """
    Called when presence/fronting changes mid-day.

    Responsibilities:
    - remove tasks that are no longer allowed
    - replace required tasks only
    """

    presence = get_current_presence(user_id)
    age = presence.get("age_context", "cloudy")

    conn = get_connection()
    cur = conn.cursor()

    # Get all active tasks for today
    cur.execute(
        """
        SELECT task_key, category, is_required
        FROM assigned_tasks
        WHERE profile_id = ?
          AND date = DATE('now')
        """,
        (profile_id,),
    )
    tasks = cur.fetchall()

    to_remove = []
    required_removed = False

    for task in tasks:
        category = task["category"]

        if age == "cloudy" and category in ("intimacy", "kink", "explicit"):
            to_remove.append(task["task_key"])
            if task["is_required"]:
                required_removed = True

        elif age == "regressive" and category in ("kink", "explicit"):
            to_remove.append(task["task_key"])
            if task["is_required"]:
                required_removed = True

    # Remove disallowed tasks
    for key in to_remove:
        cur.execute(
            """
            DELETE FROM assigned_tasks
            WHERE profile_id = ?
              AND task_key = ?
              AND date = DATE('now')
            """,
            (profile_id, key),
        )

    conn.commit()
    conn.close()

    # Replace required tasks only
    if required_removed:
        generate_daily_tasks(
            user_id=user_id,
            profile_id=profile_id,
        )
