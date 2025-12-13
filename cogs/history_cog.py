import discord
from discord.ext import commands
from discord import app_commands

from core.db import get_connection
from core.presence import get_active_profile
from core.presence import switch_active_person



class HistoryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="history",
        description="See what you've completed recently"
    )
    async def history(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        profile = get_active_profile(user_id)

        if not profile:
            await interaction.response.send_message(
                "I don’t know who’s here right now. Try `/p switch` first.",
                ephemeral=True,
            )
            return

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT date, task_key, completed
            FROM task_history
            WHERE profile_id = ?
            ORDER BY date DESC
            LIMIT 10
            """,
            (profile["profile_id"],),
        )

        rows = cur.fetchall()
        conn.close()

        if not rows:
            await interaction.response.send_message(
                f"No history yet for **{profile['name']}**.",
                ephemeral=True,
            )
            return

        lines = []
        for r in rows:
            status = "✅" if r["completed"] else "❌"
            lines.append(f"{status} `{r['date']}` — {r['task_key']}")

        await interaction.response.send_message(
            f"**Recent activity for {profile['name']}**\n\n" + "\n".join(lines),
            ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(HistoryCog(bot))
