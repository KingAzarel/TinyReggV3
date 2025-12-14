import discord
from discord.ext import commands
from discord import app_commands

from core.db import get_connection


class PendingRewardsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ─────────────────────────────────────────────
    # /pending_rewards
    # ─────────────────────────────────────────────

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
                rh.created_at,
                p.name AS profile_name,
                p.user_id
            FROM redemption_history rh
            JOIN profiles p
              ON rh.profile_id = p.profile_id
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

        # ─────────────────────────────────────────
        # Build embed (safer than raw text)
        # ─────────────────────────────────────────

        embed = discord.Embed(
            title="🎁 Pending Rewards",
            description="Undelivered rewards awaiting fulfillment.",
            color=discord.Color.from_rgb(160, 120, 200),
        )

        for r in rows:
            embed.add_field(
                name=f"{r['item_id']}",
                value=(
                    f"Code: `{r['reward_code']}`\n"
                    f"Profile: *{r['profile_name']}*\n"
                    f"User ID: `{r['user_id']}`\n"
                    f"Created: {r['created_at']}"
                ),
                inline=False,
            )

        embed.set_footer(
            text=f"{len(rows)} reward(s) pending delivery"
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True,  # keep admin output private
        )


async def setup(bot):
    await bot.add_cog(PendingRewardsCog(bot))
