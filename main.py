# main.py

import os
import logging
import discord
from discord.ext import commands, tasks
from discord import app_commands
from dotenv import load_dotenv

from core.db import initialize_db
from core import admin_services
from core.presence import get_active_profile
from utils import BOT_OWNER_ID, MAIN_GUILD_ID

# ─────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────

BELLA_USER_ID = "868623435650175046"

WATCHING_ACTIVITY = discord.Activity(
    type=discord.ActivityType.watching,
    name="Watching Over You 💜"
)

LISTENING_ACTIVITY = discord.Activity(
    type=discord.ActivityType.listening,
    name="Listening Out For You 💜"
)

CLOUDY_ACTIVITY = discord.Activity(
    type=discord.ActivityType.playing,
    name="Take your time, I’m here, Your Regg is Here."
)

# ─────────────────────────────────────────────────────────────
# ENVIRONMENT
# ─────────────────────────────────────────────────────────────

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("Missing DISCORD_TOKEN environment variable")


# ─────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(name)s: %(message)s",
    handlers=[
        logging.FileHandler("discord.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

log = logging.getLogger("tinyregg")

# ─────────────────────────────────────────────────────────────
# INTENTS
# ─────────────────────────────────────────────────────────────

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.messages = True
intents.message_content = True  # enabled intentionally

# ─────────────────────────────────────────────────────────────
# BOT DEFINITION
# ─────────────────────────────────────────────────────────────

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )

    async def setup_hook(self):
        initialize_db()
        log.info("Database initialized")

        for filename in os.listdir("./cogs"):
            if filename.endswith(".py") and not filename.startswith("_"):
                ext = f"cogs.{filename[:-3]}"
                try:
                    await self.load_extension(ext)
                    log.info(f"Loaded cog: {ext}")
                except Exception:
                    log.exception(f"Failed to load cog {ext}")

        await self.tree.sync()
        log.info("Slash commands synced")

bot = MyBot()

# ─────────────────────────────────────────────────────────────
# ADMIN SERVICE WIRING
# ─────────────────────────────────────────────────────────────

bot.dispatch_daily_tasks = admin_services.dispatch_daily_tasks
bot.force_daily_reset = admin_services.force_daily_reset
bot.reset_user_state = admin_services.reset_user_state
bot.set_user_streak = admin_services.set_user_streak
bot.add_tokens = admin_services.add_tokens
bot.remove_tokens = admin_services.remove_tokens

# ─────────────────────────────────────────────────────────────
# GLOBAL APP COMMAND ERROR HANDLER
# ─────────────────────────────────────────────────────────────

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: Exception):
    if isinstance(error, app_commands.CommandNotFound):
        return

    if interaction.response.is_done():
        return

    await interaction.response.send_message(
        "Something went wrong. Try again later.",
        ephemeral=True
    )
    log.exception("App command error", exc_info=error)

# ─────────────────────────────────────────────────────────────
# READY EVENT
# ─────────────────────────────────────────────────────────────

@bot.event
async def on_ready():
    log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    log.info("🤖 TinyRegg is ONLINE")
    log.info(f"Connected as: {bot.user} (ID: {bot.user.id})")
    log.info(f"Guilds: {len(bot.guilds)}")
    log.info("System state: STABLE")
    log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    await bot.change_presence(
        status=discord.Status.online,
        activity=WATCHING_ACTIVITY
    )

    if not presence_watcher.is_running():
        presence_watcher.start()

# ─────────────────────────────────────────────────────────────
# PRESENCE WATCHER
# ─────────────────────────────────────────────────────────────

@tasks.loop(seconds=60)
async def presence_watcher():
    """
    Presence logic:
    - If Bella is in Cloudy → override everything
    - Else:
        - Idle → Listening out for you
        - Online → Watching over you
    """
    is_cloudy = False

    try:
        active = get_active_profile(BELLA_USER_ID)
        if active and active["age_context"] == "cloudy":
            is_cloudy = True
    except Exception as e:
        log.warning(f"Presence watcher failed to read profile: {e}")

    if is_cloudy:
        await bot.change_presence(
            status=bot.status,
            activity=CLOUDY_ACTIVITY
        )
        return

    if bot.status == discord.Status.idle:
        await bot.change_presence(
            status=discord.Status.idle,
            activity=LISTENING_ACTIVITY
        )
    else:
        await bot.change_presence(
            status=discord.Status.online,
            activity=WATCHING_ACTIVITY
        )

@presence_watcher.before_loop
async def before_presence_watcher():
    await bot.wait_until_ready()

# ─────────────────────────────────────────────────────────────
# ENTRYPOINT
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    log.info("Starting TinyRegg...")
    bot.run(TOKEN)
