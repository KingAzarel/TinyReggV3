from datetime import date

from core.db import get_connection
from core.completion_messages import get_completion_message


# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

BASE_TOKEN_REWARD = 1
REQUIRED_TASK_BONUS = 1


# ─────────────────────────────────────────────
# DATE (single source of truth)
# ─────────────────────────────────────────────

def _today() -> str:
    return date.today().isoformat()


# ─────────────────────────────────────────────
# PUBLIC ENTRY POINT
# ─────────────────────────────────────────────

def handle_task_completion(user_id: str, profile_id: int, task_key: str):
    """
    Handles:
    - token rewards
    - streak updates
    - completion messaging

    Returns a completion message template (names injected elsewhere).
    """

    today = _today()

    conn = get_connection()
    cur = conn.cursor()

    # ─────────────────────────────────────────
    # Fetch task info
    # ─────────────────────────────────────────
    cur.execute(
        """
        SELECT category, is_required
        FROM assigned_tasks
        WHERE profile_id = ?
          AND task_key = ?
          AND date = ?
        """,
        (profile_id, task_key, today),
    )
    task = cur.fetchone()

    if not task:
        conn.close()
        return "That task is already gone."

    category = task["category"]
    is_required = bool(task["is_required"])

    # ─────────────────────────────────────────
    # Token rewards
    # ─────────────────────────────────────────
    total_tokens = BASE_TOKEN_REWARD + (REQUIRED_TASK_BONUS if is_required else 0)

    cur.execute(
        """
        UPDATE users
        SET tokens = tokens + ?
        WHERE user_id = ?
        """,
        (total_tokens, user_id),
    )

    # ─────────────────────────────────────────
    # Streak updates
    # ─────────────────────────────────────────
    _update_streaks(cur, profile_id, category, is_required, today)

    conn.commit()
    conn.close()

    # Return completion message template
    return get_completion_message(category, is_required)


# ─────────────────────────────────────────────
# STREAK HANDLING
# ─────────────────────────────────────────────

def _update_streaks(cur, profile_id: int, category: str, is_required: bool, today: str):
    """
    Updates streaks in profile_streaks.
    Only touches fields relevant to the task completed.
    """

    # Ensure row exists
    cur.execute(
        """
        INSERT OR IGNORE INTO profile_streaks (profile_id)
        VALUES (?)
        """,
        (profile_id,),
    )

    # Required streak
    if is_required:
        cur.execute(
            """
            UPDATE profile_streaks
            SET
                required_streak = required_streak + 1,
                last_required_day = ?
            WHERE profile_id = ?
            """,
            (today, profile_id),
        )

    # Category-specific streaks
    if category == "intimacy":
        cur.execute(
            """
            UPDATE profile_streaks
            SET
                intimacy_streak = intimacy_streak + 1,
                last_intimacy_day = ?
            WHERE profile_id = ?
            """,
            (today, profile_id),
        )

    elif category == "kink":
        cur.execute(
            """
            UPDATE profile_streaks
            SET
                kink_streak = kink_streak + 1,
                last_kink_day = ?
            WHERE profile_id = ?
            """,
            (today, profile_id),
        )

    elif category == "explicit":
        cur.execute(
            """
            UPDATE profile_streaks
            SET
                explicit_streak = explicit_streak + 1,
                last_explicit_day = ?
            WHERE profile_id = ?
            """,
            (today, profile_id),
        )
