from core.db import get_connection


# ─────────────────────────────────────────────
# ACTIVE PROFILE HELPERS
# ─────────────────────────────────────────────

def get_active_profile(user_id: str):
    """
    Returns the currently active profile for a user.
    There should only ever be ONE active profile.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM profiles
        WHERE user_id = ?
          AND is_active = 1
        LIMIT 1
        """,
        (user_id,),
    )

    row = cur.fetchone()
    conn.close()
    return row


def get_all_profiles(user_id: str):
    """
    Returns all profiles for a user, ordered by creation.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM profiles
        WHERE user_id = ?
        ORDER BY created_at ASC
        """,
        (user_id,),
    )

    rows = cur.fetchall()
    conn.close()
    return rows


# ─────────────────────────────────────────────
# PRESENCE SWITCHING (CANONICAL)
# ─────────────────────────────────────────────

def switch_active_profile(user_id: str, profile_id: int):
    """
    Canonical presence switch.

    Guarantees:
    - exactly ONE active profile
    - atomic update
    - logged switch history

    This is the ONLY place profile activation should occur.
    """

    conn = get_connection()
    cur = conn.cursor()

    try:
        # deactivate all profiles for user
        cur.execute(
            """
            UPDATE profiles
            SET is_active = 0
            WHERE user_id = ?
            """,
            (user_id,),
        )

        # activate selected profile (scoped to user)
        cur.execute(
            """
            UPDATE profiles
            SET is_active = 1
            WHERE profile_id = ?
              AND user_id = ?
            """,
            (profile_id, user_id),
        )

        # ensure activation actually happened
        if cur.rowcount == 0:
            raise ValueError("Profile does not belong to user or does not exist.")

        # log switch
        cur.execute(
            """
            INSERT INTO profile_switch_log (user_id, profile_id)
            VALUES (?, ?)
            """,
            (user_id, profile_id),
        )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


# ─────────────────────────────────────────────
# 🔁 BACKWARD-COMPATIBILITY ALIASES
# ─────────────────────────────────────────────

# legacy name used by older cogs
def switch_active_person(user_id: str, profile_id: int):
    switch_active_profile(user_id, profile_id)


# legacy opt-in / presence cogs expect this
def set_active_profile(user_id: str, profile_id: int):
    switch_active_profile(user_id, profile_id)


# ─────────────────────────────────────────────
# EVENT EMISSION (OPTIONAL HOOK)
# ─────────────────────────────────────────────

async def emit_presence_changed(bot, user_id: str, profile_id: int):
    """
    Emits a global presence_changed event.

    Future listeners may:
    - reassess tasks
    - update presence text
    - trigger AI state changes
    """
    bot.dispatch(
        "presence_changed",
        user_id=user_id,
        profile_id=profile_id,
    )


# ─────────────────────────────────────────────
# CLOUDY MODE (SAFE DEFAULT)
# ─────────────────────────────────────────────

def set_cloudy_mode(user_id: str) -> int:
    """
    Ensures a Cloudy profile exists and activates it.

    Cloudy mode is:
    - always safe
    - always reversible
    - never destructive
    """

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT profile_id
        FROM profiles
        WHERE user_id = ?
          AND age_context = 'cloudy'
        LIMIT 1
        """,
        (user_id,),
    )
    row = cur.fetchone()

    if row:
        profile_id = row["profile_id"]
    else:
        cur.execute(
            """
            INSERT INTO profiles (
                user_id,
                name,
                age_context,
                is_active
            )
            VALUES (?, 'Cloudy', 'cloudy', 0)
            """,
            (user_id,),
        )
        profile_id = cur.lastrowid

    conn.commit()
    conn.close()

    switch_active_profile(user_id, profile_id)
    return profile_id
