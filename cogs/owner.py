# cogs/owner.py

import logging
import discord
from discord import app_commands, Object
from discord.ext import commands

from utils import BOT_OWNER_ID, MAIN_GUILD_ID

log = logging.getLogger("tinyregg.owner")


class OwnerCog(commands.Cog):
    """Bot-owner-only administrative commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        log.info("[OwnerCog] initialized")

    @app_commands.command(
        name="resync",
        description="(Owner only) Resync slash commands to the main guild"
    )
    @app_commands.check(lambda i: i.user.id == BOT_OWNER_ID)
    async def resync(self, interaction: discord.Interaction):
        log.info(
            "[RESYNC] triggered by %s (%s)",
            interaction.user,
            interaction.user.id,
        )

        try:
            guild = Object(id=MAIN_GUILD_ID)
            synced = await self.bot.tree.sync(guild=guild)

            log.info(
                "[RESYNC] successfully synced %s commands to guild %s",
                len(synced),
                MAIN_GUILD_ID,
            )

            await interaction.response.send_message(
                f"🔄 Resynced `{len(synced)}` commands.",
                ephemeral=True,
            )

        except Exception:
            log.exception("[RESYNC] failed to sync commands")

            if interaction.response.is_done():
                await interaction.followup.send(
                    "❌ Resync failed—check logs.",
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    "❌ Resync failed—check logs.",
                    ephemeral=True,
                )


async def setup(bot: commands.Bot):
    log.info("[OwnerCog] setup() adding cog")
    await bot.add_cog(OwnerCog(bot))
