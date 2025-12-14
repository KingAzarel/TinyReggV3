from datetime import date

from core.db import get_connection
from core.completion_messages import get_completion_message


# ─────────────────────────────────────────────
# CONFIG (easy to scale later)
# ─────────────────────────────────────────────

BASE_TOKEN_REWARD = 1
REQUIRED_TASK_BONUS = 1


# ─────────────────────────────────────────────
# DATE (single source of truth)
# ─────────────────────────────────────────────

def _today() -> str:
    return date.today().isoformat()


# ─────────────────────────────────────────────
# PUBLIC ENTRY POINT (CANONICAL)
# ─────────────────────────────────────────────

def handle_task_completion(user_id: str, profile_id: int, task_key: str) -> str:
    """
    Canonical task completion handler.

    Responsibilities:
    - idempotent completion safety
    - token rewards
    - streak updates
    - returns a completion message template

    UI / theming / injection happens elsewhere.
    """

    today = _today()

    conn = get_connection()
    cur = conn.cursor()

    # ─────────────────────────────────────────
    # Validate task exists for today
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
        return "That task isn’t available anymore."

    category = task["category"]
    is_required = bool(task["is_required"])

    # ─────────────────────────────────────────
    # Idempotency guard (NO double rewards)
    # ─────────────────────────────────────────
    cur.execute(
        """
        SELECT completed
        FROM task_history
        WHERE profile_id = ?
          AND task_key = ?
          AND date = ?
        """,
        (profile_id, task_key, today),
    )
    existing = cur.fetchone()

    if existing and existing["completed"]:
        conn.close()
        return "That task was already completed 💜"

    # ─────────────────────────────────────────
    # Record completion FIRST (source of truth)
    # ─────────────────────────────────────────
    cur.execute(
        """
        INSERT OR REPLACE INTO task_history
        (profile_id, date, task_key, completed)
        VALUES (?, ?, ?, 1)
        """,
        (profile_id, today, task_key),
    )

    # ─────────────────────────────────────────
    # Token rewards (isolated + scalable)
    # ─────────────────────────────────────────
    total_tokens = BASE_TOKEN_REWARD
    if is_required:
        total_tokens += REQUIRED_TASK_BONUS

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
    _update_streaks(
        cur=cur,
        profile_id=profile_id,
        category=category,
        is_required=is_required,
        today=today,
    )

    conn.commit()
    conn.close()

    # ─────────────────────────────────────────
    # Return completion message (template only)
    # ─────────────────────────────────────────
    return get_completion_message(category, is_required)


# ─────────────────────────────────────────────
# STREAK HANDLING (ISOLATED + SAFE)
# ─────────────────────────────────────────────

def _update_streaks(
    *,
    cur,
    profile_id: int,
    category: str,
    is_required: bool,
    today: str,
):
    """
    Updates profile_streaks safely.

    This function:
    - assumes an open transaction
    - never commits
    - only mutates relevant fields
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
