import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta

from core.db import get_connection
from core.presence import switch_active_person



class DeadlineReminderCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.deadline_loop.start()

    # ─────────────────────────────────────────────
    # ADMIN: create a hard deadline
    # ─────────────────────────────────────────────
    @app_commands.command(
        name="set_deadline",
        description="Admin: set a hard deadline reminder"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def set_deadline(
        self,
        interaction: discord.Interaction,
        user: discord.User,
        title: str,
        due_date: str,  # YYYY-MM-DD
        hour: int = 9,
        minute: int = 0,
    ):
        """
        Example:
        /set_deadline @Bella "Bio Exam 2" 2025-03-15 9 0
        """

        try:
            due = datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError:
            await interaction.response.send_message(
                "Date format must be YYYY-MM-DD.",
                ephemeral=True,
            )
            return

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO reminders (
                profile_id,
                hour,
                minute,
                text,
                is_recurring
            )
            VALUES (?, ?, ?, ?, 0)
            """,
            (
                None,  # account-level reminder
                hour,
                minute,
                f"DEADLINE: {title} — due {due_date}",
            ),
        )

        conn.commit()
        conn.close()

        await interaction.response.send_message(
            f"Deadline set for **{title}** on {due_date}.",
            ephemeral=True,
        )

    # ─────────────────────────────────────────────
    # LOOP: check & deliver reminders
    # ─────────────────────────────────────────────
    @tasks.loop(minutes=1)
    async def deadline_loop(self):
        now = datetime.now()

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT reminder_id, text
            FROM reminders
            WHERE hour = ? AND minute = ?
            """,
            (now.hour, now.minute),
        )

        reminders = cur.fetchall()
        conn.close()

        if not reminders:
            return

        for r in reminders:
            await self._deliver_reminder(r["text"])

    async def _deliver_reminder(self, text: str):
        """
        Deliver reminder to Bella (user-level delivery).
        """
        for guild in self.bot.guilds:
            for member in guild.members:
                if member.bot:
                    continue

                try:
                    await member.send(
                        f"⏱ **Reminder**\n\n{text}"
                    )
                except discord.Forbidden:
                    pass  # DMs closed, silently ignore

    # ─────────────────────────────────────────────
    # SAFETY
    # ─────────────────────────────────────────────
    @deadline_loop.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(DeadlineReminderCog(bot))
