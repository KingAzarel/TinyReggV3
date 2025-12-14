from core.db import get_connection


# ─────────────────────────────────────────────
# ACTIVE PROFILE HELPERS
# ─────────────────────────────────────────────

def get_active_profile(user_id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT *
        FROM profiles
        WHERE user_id = ?
          AND is_active = 1
        """,
        (user_id,),
    )
    row = cur.fetchone()
    conn.close()
    return row


def get_all_profiles(user_id: str):
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
    Deactivate all profiles for user, then activate one.
    This is the ONLY place presence switching should happen.
    """
    conn = get_connection()
    cur = conn.cursor()

    # deactivate all
    cur.execute(
        "UPDATE profiles SET is_active = 0 WHERE user_id = ?",
        (user_id,),
    )

    # activate selected
    cur.execute(
        """
        UPDATE profiles
        SET is_active = 1
        WHERE profile_id = ?
          AND user_id = ?
        """,
        (profile_id, user_id),
    )

    # log switch
    cur.execute(
        """
        INSERT INTO profile_switch_log (user_id, profile_id)
        VALUES (?, ?)
        """,
        (user_id, profile_id),
    )

    conn.commit()
    conn.close()


# ─────────────────────────────────────────────
# 🔁 BACKWARD-COMPATIBILITY ALIASES
# ─────────────────────────────────────────────

# legacy name used by many cogs
def switch_active_person(user_id: str, profile_id: int):
    switch_active_profile(user_id, profile_id)


# legacy opt-in / presence cogs expect this
def set_active_profile(user_id: str, profile_id: int):
    switch_active_profile(user_id, profile_id)


# ─────────────────────────────────────────────
# EVENT EMISSION
# ─────────────────────────────────────────────

async def emit_presence_changed(bot, user_id: str, profile_id: int):
    """
    Emits a global presence_changed event.
    Optional listeners can react to this.
    """
    bot.dispatch(
        "presence_changed",
        user_id=user_id,
        profile_id=profile_id,
    )


# ─────────────────────────────────────────────
# CLOUDY MODE (SAFE DEFAULT)
# ─────────────────────────────────────────────

def set_cloudy_mode(user_id: str):
    """
    Ensures a cloudy profile exists and activates it.
    Cloudy is always safe and always switchable.
    """
    conn = get_connection()
    cur = conn.cursor()

    # look for existing cloudy profile
    cur.execute(
        """
        SELECT profile_id
        FROM profiles
        WHERE user_id = ?
          AND age_context = 'cloudy'
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
