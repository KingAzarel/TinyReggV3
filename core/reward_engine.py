import random
import string
from datetime import datetime

from core.db import get_connection
from shop.rewards import REWARDS


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _generate_code(length: int = 8) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


# ─────────────────────────────────────────────
# Core engine
# ─────────────────────────────────────────────

def generate_reward(user_id: str, profile_id: int, item_key: str):
    """
    Attempts to redeem a reward.

    Returns:
        dict with reward info if successful
        None if blocked
    """

    reward = REWARDS.get(item_key)
    if not reward:
        return None

    conn = get_connection()
    cur = conn.cursor()

    # ─────────────────────────────────────────
    # Fetch user tokens
    # ─────────────────────────────────────────
    cur.execute(
        "SELECT tokens FROM users WHERE user_id = ?",
        (user_id,),
    )
    user_row = cur.fetchone()
    if not user_row or user_row["tokens"] < reward["cost"]:
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
        return None

    # ─────────────────────────────────────────
    # Safety gates
    # ─────────────────────────────────────────

    # Cloudy mode: only safe rewards
    if profile["age_context"] == "cloudy" and not reward.get("cloudy_safe", False):
        conn.close()
        return None

    # Regressive: no kink or explicit
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
    # Spend tokens
    # ─────────────────────────────────────────
    cur.execute(
        "UPDATE users SET tokens = tokens - ? WHERE user_id = ?",
        (reward["cost"], user_id),
    )

    # ─────────────────────────────────────────
    # Log redemption
    # ─────────────────────────────────────────
    reward_code = _generate_code()

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
    conn.close()

    # Return minimal info for UI / delivery
    return {
        "item_id": item_key,
        "name": reward["name"],
        "cost": reward["cost"],
        "reward_code": reward_code,
    }
