# cogs/boss.py

import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta

from core.db import get_connection
from core.users import add_tokens


WEEKLY_BOSS = {
    "name": "The Weight of the Week",
    "required_tasks": 10,
    "reward_tokens": 50,
    "message": (
        "You pushed through the week and didn’t disappear.\n"
        "That counts for more than you think."
    ),
}


class BossCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.weekly_check.start()

    @tasks.loop(hours=6)
    async def weekly_check(self):
        now = datetime.utcnow()
        since = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        week = now.isocalendar().week

        conn = get_connection()
        cur = conn.cursor()

        # 1️⃣ Find profiles with completed tasks this week
        cur.execute(
            """
            SELECT profile_id, COUNT(*) as completed
            FROM task_history
            WHERE completed = 1
              AND date >= ?
            GROUP BY profile_id
            """,
            (since,),
        )

        profiles = cur.fetchall()

        for row in profiles:
            profile_id = row["profile_id"]
            completed = row["completed"]

            if completed < WEEKLY_BOSS["required_tasks"]:
                continue

            # 2️⃣ Check if boss already defeated this week
            cur.execute(
                """
                SELECT 1
                FROM boss_history
                WHERE profile_id = ?
                  AND boss_name = ?
                  AND defeated_at >= ?
                """,
                (profile_id, WEEKLY_BOSS["name"], since),
            )

            if cur.fetchone():
                continue

            # 3️⃣ Record boss defeat
            cur.execute(
                """
                INSERT INTO boss_history (profile_id, boss_name)
                VALUES (?, ?)
                """,
                (profile_id, WEEKLY_BOSS["name"]),
            )

            # 4️⃣ Update weekly summary
            cur.execute(
                """
                INSERT INTO weekly (profile_id, week, tasks_completed, bosses_defeated)
                VALUES (?, ?, ?, 1)
                ON CONFLICT(profile_id, week) DO UPDATE SET
                    bosses_defeated = bosses_defeated + 1
                """,
                (profile_id, week, completed),
            )

            # 5️⃣ Resolve user + profile name for messaging
            cur.execute(
                """
                SELECT user_id, name
                FROM profiles
                WHERE profile_id = ?
                """,
                (profile_id,),
            )
            profile = cur.fetchone()

            if not profile:
                continue

            add_tokens(profile["user_id"], WEEKLY_BOSS["reward_tokens"])

            await self._announce_defeat(
                profile["user_id"],
                profile["name"],
            )

        conn.commit()
        conn.close()

    async def _announce_defeat(self, user_id: str, profile_name: str):
        for guild in self.bot.guilds:
            member = guild.get_member(int(user_id))
            if not member:
                continue

            try:
                await member.send(
                    f"🏆 **Weekly Boss Defeated**\n\n"
                    f"**{profile_name}** faced *{WEEKLY_BOSS['name']}*.\n\n"
                    f"{WEEKLY_BOSS['message']}\n\n"
                    f"+{WEEKLY_BOSS['reward_tokens']} tokens"
                )
            except discord.Forbidden:
                pass

    @weekly_check.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(BossCog(bot))
