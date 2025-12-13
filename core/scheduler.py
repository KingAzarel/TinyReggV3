import discord
import pytz
from datetime import datetime
from discord.ext import commands, tasks

from core.db import get_connection
from core.theming import build_embed, purple_doll_colors

CENTRAL = pytz.timezone("America/Chicago")


class MorningScheduler(commands.Cog):
    """
    Morning Orchestrator:
    - Runs once per day at the set time
    - Prompts Bella to choose who is fronting
    - Does NOT assign tasks
    """

    def __init__(self, bot):
        self.bot = bot
        self.morning_loop.start()

    # ---------------------------------------------------------
    # Morning Loop (checks every minute)
    # ---------------------------------------------------------
    @tasks.loop(minutes=1)
    async def morning_loop(self):
        now = datetime.now(CENTRAL)

        # Fire exactly at 6:00 AM
        if not (now.hour == 6 and now.minute == 0):
            return

        today = str(now.date())

        if self._already_prompted_today(today):
            return

        self._mark_prompted(today)

        # Fetch Bella directly (single recipient system)
        try:
            bella = await self.bot.fetch_user(868623435650175046)
        except:
            return

        embed = build_embed(
            title="🌅 Good Morning",
            description=(
                "Who’s fronting today?\n\n"
                "You can choose a profile, create a new one, or stay in **Cloudy Mode**.\n"
                "Cloudy Mode still counts toward streaks and rewards."
            ),
            color=purple_doll_colors["accent"]
        )

        view = FrontingSelectionView()

        try:
            await bella.send(embed=embed, view=view)
        except discord.Forbidden:
            pass

    # ---------------------------------------------------------
    # Daily State Tracking
    # ---------------------------------------------------------
    def _already_prompted_today(self, today: str) -> bool:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT value
            FROM task_reset_state
            WHERE id = 1
        """)
        row = cur.fetchone()
        conn.close()

        if not row:
            return False

        return row["value"] == today

    def _mark_prompted(self, today: str):
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO task_reset_state (id, last_reset_date)
            VALUES (1, ?)
            ON CONFLICT(id) DO UPDATE SET last_reset_date = excluded.last_reset_date
        """, (today,))

        conn.commit()
        conn.close()


# ---------------------------------------------------------
# Placeholder View (wired next)
# ---------------------------------------------------------
class FrontingSelectionView(discord.ui.View):
    """
    This view will be wired to:
    - profile selection
    - profile creation
    - Cloudy mode
    """
    def __init__(self):
        super().__init__(timeout=None)


async def setup(bot):
    await bot.add_cog(MorningScheduler(bot))
