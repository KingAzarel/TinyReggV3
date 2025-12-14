import logging
import random
import string
from datetime import datetime

from core.db import get_connection
from shop.rewards import REWARDS

log = logging.getLogger("tinyregg.reward_engine")


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _generate_code(length: int = 8) -> str:
    return "".join(
        random.choices(string.ascii_uppercase + string.digits, k=length)
    )


# ─────────────────────────────────────────────
# Core engine
# ─────────────────────────────────────────────

def generate_reward(user_id: str, profile_id: int, item_key: str):
    """
    Attempts to redeem a reward.

    Returns:
        dict with reward info if successful
        None if blocked or insufficient permissions/tokens
    """

    reward = REWARDS.get(item_key)
    if not reward:
        log.warning("Unknown reward key: %s", item_key)
        return None

    conn = get_connection()
    cur = conn.cursor()

    # ─────────────────────────────────────────
    # Fetch user tokens (LOCKED)
    # ─────────────────────────────────────────
    cur.execute(
        "SELECT tokens FROM users WHERE user_id = ?",
        (user_id,),
    )
    user_row = cur.fetchone()

    if not user_row:
        conn.close()
        log.warning("Reward attempt for missing user %s", user_id)
        return None

    if user_row["tokens"] < reward["cost"]:
        conn.close()
        return None

    # ─────────────────────────────────────────
    # Fetch profile opt-ins
    # ─────────────────────────────────────────
    cur.execute(
        """
        SELECT
            age_context,
            intimacy_opt_in,
            kink_opt_in,
            explicit_opt_in
        FROM profiles
        WHERE profile_id = ?
        """,
        (profile_id,),
    )
    profile = cur.fetchone()

    if not profile:
        conn.close()
        log.warning(
            "Reward attempt with missing profile %s (user=%s)",
            profile_id,
            user_id,
        )
        return None

    # ─────────────────────────────────────────
    # Safety gates
    # ─────────────────────────────────────────

    # Cloudy mode
    if profile["age_context"] == "cloudy":
        if not reward.get("cloudy_safe", False):
            conn.close()
            return None

    # Regressive mode
    if profile["age_context"] == "regressive":
        if reward.get("requires_kink") or reward.get("requires_explicit"):
            conn.close()
            return None

    # Intimacy gate
    if reward.get("requires_intimacy") and not profile["intimacy_opt_in"]:
        conn.close()
        return None

    # Kink gate
    if reward.get("requires_kink") and not profile["kink_opt_in"]:
        conn.close()
        return None

    # Explicit gate
    if reward.get("requires_explicit") and not profile["explicit_opt_in"]:
        conn.close()
        return None

    # ─────────────────────────────────────────
    # Atomic spend + log
    # ─────────────────────────────────────────
    reward_code = _generate_code()

    try:
        cur.execute("BEGIN")

        cur.execute(
            """
            UPDATE users
            SET tokens = tokens - ?
            WHERE user_id = ?
            """,
            (reward["cost"], user_id),
        )

        cur.execute(
            """
            INSERT INTO redemption_history (
                profile_id,
                item_id,
                reward_code,
                delivered,
                created_at
            )
            VALUES (?, ?, ?, 0, ?)
            """,
            (
                profile_id,
                item_key,
                reward_code,
                datetime.utcnow().isoformat(),
            ),
        )

        conn.commit()

    except Exception:
        conn.rollback()
        conn.close()
        log.exception(
            "Failed to redeem reward %s for user=%s profile=%s",
            item_key,
            user_id,
            profile_id,
        )
        return None

    conn.close()

    return {
        "item_id": item_key,
        "name": reward["name"],
        "cost": reward["cost"],
        "reward_code": reward_code,
    }
