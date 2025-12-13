# cogs/owner.py

import logging
import discord
from discord import app_commands, Object
from discord.ext import commands
from core.presence import switch_active_person


from utils import BOT_OWNER_ID, MAIN_GUILD_ID

log = logging.getLogger(__name__)

class OwnerCog(commands.Cog):
    """Bot‑owner‑only administrative commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        log.info("[OwnerCog] initialized")

    @app_commands.command(
        name="resync",
        description="(Owner only) Resync slash commands to the main guild and dump logs"
    )
    @app_commands.check(lambda i: i.user.id == BOT_OWNER_ID)
    async def resync(self, interaction: discord.Interaction):
        log.info(f"[RESYNC] triggered by {interaction.user} ({interaction.user.id})")

        before = [c.name for c in self.bot.tree.get_commands()]
        log.info(f"[RESYNC] commands before sync: {before}")

        try:
            guild_obj = Object(id=MAIN_GUILD_ID)
            synced = await self.bot.tree.sync(guild=guild_obj)
            after = [c.name for c in synced]
            log.info(f"[RESYNC] successfully synced {len(synced)} commands: {after}")

            await interaction.response.send_message(
                f"🔄 Resynced {len(synced)} commands to guild {MAIN_GUILD_ID}.",
                ephemeral=True
            )
        except Exception:
            log.exception("[RESYNC] failed to sync commands")
            await interaction.response.send_message(
                "❌ Resync failed—check logs for details.",
                ephemeral=True
            )

async def setup(bot: commands.Bot):
    log.info("[OwnerCog] setup() adding cog")
    await bot.add_cog(OwnerCog(bot))
