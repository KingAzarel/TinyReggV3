import logging
import discord
from datetime import datetime

from core.db import get_connection
from shop.rewards import REWARDS
from core.theming import format_reward_delivery

log = logging.getLogger("tinyregg.reward_delivery")


# ─────────────────────────────────────────────
# PUBLIC ENTRY POINT
# ─────────────────────────────────────────────

async def deliver_pending_rewards(bot: discord.Client):
    """
    Deliver all undelivered rewards.
    Safe to call repeatedly.
    """

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            rh.id,
            rh.item_id,
            rh.reward_code,
            p.name AS profile_name,
            p.user_id
        FROM redemption_history rh
        JOIN profiles p ON rh.profile_id = p.profile_id
        WHERE rh.delivered = 0
        ORDER BY rh.created_at ASC
        """
    )

    rows = cur.fetchall()
    conn.close()

    if not rows:
        return

    for row in rows:
        try:
            await _deliver_one(bot, row)
        except Exception:
            log.exception(
                "Failed delivering reward id=%s item=%s",
                row["id"],
                row["item_id"],
            )


# ─────────────────────────────────────────────
# SINGLE DELIVERY
# ─────────────────────────────────────────────

async def _deliver_one(bot: discord.Client, row: dict):
    item = REWARDS.get(row["item_id"])

    # Unknown reward → mark delivered so it doesn’t loop forever
    if not item:
        log.warning(
            "Unknown reward item_id=%s — marking delivered",
            row["item_id"],
        )
        _mark_delivered(row["id"])
        return

    user_id = int(row["user_id"])
    profile_name = row["profile_name"]
    reward_code = row["reward_code"]

    message = format_reward_delivery(
        item=item,
        reward_code=reward_code,
        profile_name=profile_name,
    )

    # Prefer direct fetch (guild-agnostic, safer)
    try:
        user = await bot.fetch_user(user_id)
    except Exception:
        log.warning("Failed to fetch user %s", user_id)
        return

    try:
        await user.send(message)
    except discord.Forbidden:
        log.warning("DMs closed for user %s", user_id)
        return

    _mark_delivered(row["id"])
    log.info(
        "Delivered reward id=%s to user=%s",
        row["id"],
        user_id,
    )


# ─────────────────────────────────────────────
# DB UPDATE
# ─────────────────────────────────────────────

def _mark_delivered(redemption_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE redemption_history
        SET delivered = 1,
            delivered_at = ?
        WHERE id = ?
        """,
        (datetime.utcnow().isoformat(), redemption_id),
    )

    conn.commit()
    conn.close()
