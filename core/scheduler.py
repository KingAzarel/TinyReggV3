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
    - Prompts each user to choose who is fronting
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

        today = now.date().isoformat()

        if self._already_prompted_today(today):
            return

        self._mark_prompted(today)

        conn = get_connection()
        cur = conn.cursor()

        # Fetch ALL users who have started
        cur.execute(
            """
            SELECT user_id
            FROM users
            WHERE has_started = 1
            """
        )
        users = cur.fetchall()
        conn.close()

        if not users:
            return

        for row in users:
            user_id = row["user_id"]

            try:
                user = await self.bot.fetch_user(int(user_id))
            except Exception:
                continue

            embed = build_embed(
                title="🌅 Good Morning",
                description=(
                    "Who’s fronting today?\n\n"
                    "You can choose a profile, create a new one, or stay in **Cloudy Mode**.\n"
                    "Cloudy Mode still counts toward streaks and rewards."
                ),
                color=purple_doll_colors["accent"],
            )

            view = FrontingSelectionView(user_id=str(user_id))

            try:
                await user.send(embed=embed, view=view)
            except discord.Forbidden:
                continue

    # ---------------------------------------------------------
    # Daily State Tracking
    # ---------------------------------------------------------
    def _already_prompted_today(self, today: str) -> bool:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT last_reset_date
            FROM task_reset_state
            WHERE id = 1
            """
        )
        row = cur.fetchone()
        conn.close()

        if not row:
            return False

        return row["last_reset_date"] == today

    def _mark_prompted(self, today: str):
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO task_reset_state (id, last_reset_date)
            VALUES (1, ?)
            ON CONFLICT(id)
            DO UPDATE SET last_reset_date = excluded.last_reset_date
            """,
            (today,),
        )

        conn.commit()
        conn.close()


# ---------------------------------------------------------
# Fronting Selection View (wired elsewhere)
# ---------------------------------------------------------
class FrontingSelectionView(discord.ui.View):
    """
    Orchestration-only view.
    Actual buttons/selects are wired in presence cogs.
    """

    def __init__(self, user_id: str):
        super().__init__(timeout=None)
        self.user_id = user_id


async def setup(bot):
    await bot.add_cog(MorningScheduler(bot))
