import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta

from core.db import get_connection
from core.presence import switch_active_person



# ─────────────────────────────────────────────
# Anniversary / Milestone system (Owner-side)
# ─────────────────────────────────────────────

class MilestonesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.milestone_loop.start()

    # ─────────────────────────────────────────────
    # OWNER: add a milestone / anniversary
    # ─────────────────────────────────────────────
    @app_commands.command(
        name="add_milestone",
        description="Owner: add an anniversary or important date"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def add_milestone(
        self,
        interaction: discord.Interaction,
        title: str,
        date: str,  # YYYY-MM-DD
    ):
        """
        Example:
        /add_milestone "Our 1 Year Anniversary" 2025-10-23
        """

        try:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            await interaction.response.send_message(
                "Date must be in YYYY-MM-DD format.",
                ephemeral=True,
            )
            return

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO milestones (
                profile_id,
                name,
                datetime,
                repeat
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                None,  # account-level / relationship-level
                title,
                target_date.isoformat(),
                "yearly",
            ),
        )

        conn.commit()
        conn.close()

        await interaction.response.send_message(
            f"Milestone **{title}** added for {date}.",
            ephemeral=True,
        )

    # ─────────────────────────────────────────────
    # LOOP: countdown notifications
    # ─────────────────────────────────────────────
    @tasks.loop(hours=12)
    async def milestone_loop(self):
        today = datetime.utcnow().date()

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT milestone_id, name, datetime
            FROM milestones
            """
        )

        milestones = cur.fetchall()
        conn.close()

        for m in milestones:
            event_date = datetime.fromisoformat(m["datetime"]).date()

            # Calculate next occurrence (yearly)
            next_event = event_date.replace(year=today.year)
            if next_event < today:
                next_event = next_event.replace(year=today.year + 1)

            days_until = (next_event - today).days

            # Notify only at gentle intervals
            if days_until in (30, 15, 7, 3, 1):
                await self._send_countdown(
                    m["name"],
                    days_until,
                )

    # ─────────────────────────────────────────────
    # Delivery
    # ─────────────────────────────────────────────
    async def _send_countdown(self, title: str, days: int):
        """
        Sends a soft, anticipatory message.
        """
        message = (
            f"💗 **Just a little reminder**\n\n"
            f"{days} days until **{title}**.\n\n"
            "No pressure. Just something sweet on the horizon."
        )

        for guild in self.bot.guilds:
            for member in guild.members:
                if member.bot:
                    continue

                try:
                    await member.send(message)
                except discord.Forbidden:
                    pass

    # ─────────────────────────────────────────────
    # SAFETY
    # ─────────────────────────────────────────────
    @milestone_loop.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(MilestonesCog(bot))
