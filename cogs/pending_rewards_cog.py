import discord
from discord.ext import commands
from discord import app_commands

from core.db import get_connection
from core.presence import switch_active_person



class PendingRewardsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="pending_rewards",
        description="Admin: view undelivered rewards"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def pending_rewards(self, interaction: discord.Interaction):
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
            await interaction.response.send_message(
                "No pending rewards 🎉",
                ephemeral=True,
            )
            return

        lines = []
        for r in rows:
            lines.append(
                f"**{r['item_id']}** → `{r['reward_code']}`\n"
                f"earned by *{r['profile_name']}* (user `{r['user_id']}`)"
            )

        await interaction.response.send_message(
            "\n\n".join(lines),
            ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(PendingRewardsCog(bot))
