import discord
from datetime import datetime

from core.db import get_connection
from shop.rewards import REWARDS
from core.theming import format_reward_delivery


# ─────────────────────────────────────────────
# Delivery entry point
# ─────────────────────────────────────────────

async def deliver_pending_rewards(bot: discord.Client):
    """
    Delivers all undelivered rewards.
    Safe to call multiple times.
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

    for row in rows:
        await _deliver_one(bot, row)

    conn.close()


# ─────────────────────────────────────────────
# Single delivery
# ─────────────────────────────────────────────

async def _deliver_one(bot: discord.Client, row):
    item = REWARDS.get(row["item_id"])
    if not item:
        _mark_delivered(row["id"])
        return

    user_id = row["user_id"]
    profile_name = row["profile_name"]
    reward_code = row["reward_code"]

    message = format_reward_delivery(
        item=item,
        reward_code=reward_code,
        profile_name=profile_name,
    )

    for guild in bot.guilds:
        member = guild.get_member(int(user_id))
        if not member:
            continue

        try:
            await member.send(message)
        except discord.Forbidden:
            pass

    _mark_delivered(row["id"])


# ─────────────────────────────────────────────
# DB update
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
