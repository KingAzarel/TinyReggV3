import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta

from core.db import get_connection
from core.presence import get_active_profile


class StatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ─────────────────────────────────────────────
    # /stats today
    # ─────────────────────────────────────────────
    @app_commands.command(
        name="stats_today",
        description="See what you’ve done today"
    )
    async def stats_today(self, interaction: discord.Interaction):
        await self._send_stats(interaction, days=1)

    # ─────────────────────────────────────────────
    # /stats week
    # ─────────────────────────────────────────────
    @app_commands.command(
        name="stats_week",
        description="See your last 7 days"
    )
    async def stats_week(self, interaction: discord.Interaction):
        await self._send_stats(interaction, days=7)

    # ─────────────────────────────────────────────
    # Core logic
    # ─────────────────────────────────────────────
    async def _send_stats(self, interaction: discord.Interaction, days: int):
        user_id = str(interaction.user.id)
        profile = get_active_profile(user_id)

        if not profile:
            await interaction.response.send_message(
                "I don’t know who’s here right now.",
                ephemeral=True,
            )
            return

        since = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT category, COUNT(*) AS count
            FROM task_history
            WHERE profile_id = ?
              AND completed = 1
              AND date >= ?
            GROUP BY category
            """,
            (profile["profile_id"], since),
        )

        rows = cur.fetchall()
        conn.close()

        if not rows:
            await interaction.response.send_message(
                f"No completed tasks yet for **{profile['name']}**.",
                ephemeral=True,
            )
            return

        lines = [f"**Stats for {profile['name']}**\n"]

        for r in rows:
            lines.append(f"• **{r['category']}** — {r['count']}")

        await interaction.response.send_message(
            "\n".join(lines),
            ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(StatsCog(bot))
