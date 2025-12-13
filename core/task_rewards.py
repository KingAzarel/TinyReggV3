from core.db import get_connection
from core.completion_messages import get_completion_message


# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

BASE_TOKEN_REWARD = 1
REQUIRED_TASK_BONUS = 1


# ─────────────────────────────────────────────
# PUBLIC ENTRY POINT
# ─────────────────────────────────────────────

def handle_task_completion(user_id, profile_id, task_key):
    """
    Handles:
    - token rewards
    - streak updates
    - completion messaging

    Returns a completion message template (not themed yet).
    """

    conn = get_connection()
    cur = conn.cursor()

    # Get task info
    cur.execute(
        """
        SELECT category, is_required
        FROM assigned_tasks
        WHERE profile_id = ?
          AND task_key = ?
          AND date = DATE('now')
        """,
        (profile_id, task_key),
    )
    task = cur.fetchone()

    if not task:
        conn.close()
        return "I couldn’t find that task anymore."

    category = task["category"]
    is_required = task["is_required"] == 1

    # Award base token
    cur.execute(
        """
        UPDATE users
        SET tokens = tokens + ?
        WHERE user_id = ?
        """,
        (BASE_TOKEN_REWARD, user_id),
    )

    # Award required bonus
    if is_required:
        cur.execute(
            """
            UPDATE users
            SET tokens = tokens + ?
            WHERE user_id = ?
            """,
            (REQUIRED_TASK_BONUS, user_id),
        )

    # Update streaks
    _update_streaks(cur, profile_id, category, is_required)

    conn.commit()
    conn.close()

    # Return completion message (template only)
    return get_completion_message(category, is_required)


# ─────────────────────────────────────────────
# STREAK HANDLING
# ─────────────────────────────────────────────

def _update_streaks(cur, profile_id, category, is_required):
    """
    Updates streaks in profile_streaks.
    Only touches relevant streak fields.
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
                last_required_day = DATE('now')
            WHERE profile_id = ?
            """,
            (profile_id,),
        )

    # Category-specific streaks
    if category == "intimacy":
        cur.execute(
            """
            UPDATE profile_streaks
            SET
                intimacy_streak = intimacy_streak + 1,
                last_intimacy_day = DATE('now')
            WHERE profile_id = ?
            """,
            (profile_id,),
        )

    elif category == "kink":
        cur.execute(
            """
            UPDATE profile_streaks
            SET
                kink_streak = kink_streak + 1,
                last_kink_day = DATE('now')
            WHERE profile_id = ?
            """,
            (profile_id,),
        )

    elif category == "explicit":
        cur.execute(
            """
            UPDATE profile_streaks
            SET
                explicit_streak = explicit_streak + 1,
                last_explicit_day = DATE('now')
            WHERE profile_id = ?
            """,
            (profile_id,),
        )
