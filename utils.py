import os
import logging
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

import discord
from discord import app_commands
from discord.app_commands import AppCommandError

log = logging.getLogger(__name__)

# ─── Environment ─────────────────────────────────────────────
load_dotenv()

BOT_OWNER_ID  = int(os.getenv("BOT_OWNER_ID", "0"))
MAIN_GUILD_ID = int(os.getenv("MAIN_GUILD_ID", "0"))

CT = ZoneInfo("America/Chicago")

# ─── Role Guards (optional, keep if used) ────────────────────
async def enforce_role(interaction: discord.Interaction, role_name: str) -> bool:
    if interaction.guild:
        member = await interaction.guild.fetch_member(interaction.user.id)
        if not any(r.name == role_name for r in member.roles):
            raise AppCommandError(
                f"You need the **{role_name}** role to use this command."
            )
    return True
