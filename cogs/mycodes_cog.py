import discord
from discord.ext import commands
from discord import app_commands

from core.db import get_connection
from core.presence import switch_active_person


class MyCodesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="mycodes",
        description="See your redeemed reward codes"
    )
    async def mycodes(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                rh.item_id,
                rh.reward_code,
                rh.delivered,
                p.name AS profile_name
            FROM redemption_history rh
            JOIN profiles p ON rh.profile_id = p.profile_id
            WHERE p.user_id = ?
            ORDER BY rh.created_at DESC
            """,
            (user_id,),
        )

        rows = cur.fetchall()
        conn.close()

        if not rows:
            await interaction.response.send_message(
                "You don’t have any codes yet.",
                ephemeral=True,
            )
            return

        lines = []
        for r in rows:
            status = "📦 delivered" if r["delivered"] else "⏳ pending"
            lines.append(
                f"**{r['item_id']}** — `{r['reward_code']}`\n"
                f"earned by *{r['profile_name']}* ({status})"
            )

        await interaction.response.send_message(
            "\n\n".join(lines),
            ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(MyCodesCog(bot))
