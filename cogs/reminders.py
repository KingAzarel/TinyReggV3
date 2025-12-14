import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime

from core.db import get_connection
from core.presence import get_active_profile


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
        try:
            datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError:
            await interaction.response.send_message(
                "Date format must be YYYY-MM-DD.",
                ephemeral=True,
            )
            return

        # Resolve active profile
        profile = get_active_profile(str(user.id))
        if not profile:
            await interaction.response.send_message(
                "That user has no active profile.",
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
                profile["profile_id"],
                hour,
                minute,
                f"DEADLINE: {title} — due {due_date}",
            ),
        )

        conn.commit()
        conn.close()

        await interaction.response.send_message(
            f"Deadline set for **{title}** on {due_date} for {user.mention}.",
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
            SELECT
                r.reminder_id,
                r.text,
                p.user_id
            FROM reminders r
            JOIN profiles p ON p.profile_id = r.profile_id
            WHERE r.hour = ? AND r.minute = ?
            """,
            (now.hour, now.minute),
        )

        reminders = cur.fetchall()
        conn.close()

        for r in reminders:
            await self._deliver_reminder(r["user_id"], r["text"])

    async def _deliver_reminder(self, user_id: str, text: str):
        try:
            user = await self.bot.fetch_user(int(user_id))
            await user.send(f"⏱ **Reminder**\n\n{text}")
        except discord.Forbidden:
            pass
        except Exception:
            pass

    # ─────────────────────────────────────────────
    # SAFETY
    # ─────────────────────────────────────────────
    @deadline_loop.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(DeadlineReminderCog(bot))
