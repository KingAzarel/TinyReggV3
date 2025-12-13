import discord
from discord.ext import commands

from core.task_engine import reassess_tasks_for_profile


class PresenceListener(commands.Cog):
    """
    Reacts to presence/fronting changes.
    This is the orchestration layer between presence and systems
    like tasks, AI tone, reminders, etc.
    """

    def __init__(self, bot):
        self.bot = bot

    # ─────────────────────────────────────────────
    # Presence change event
    # ─────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_presence_changed(self, user_id: str, profile_id: int):
        """
        Fired whenever the active presence/profile changes.
        """

        # 🔁 TASK REASSESSMENT
        try:
            reassess_tasks_for_profile(profile_id)
        except Exception as e:
            print(
                f"[PresenceListener] Failed to reassess tasks "
                f"(user={user_id}, profile={profile_id}): {e}"
            )

        # 🧠 FUTURE HOOKS (do not remove)
        # ─────────────────────────────────────────
        # - AI tone adjustment
        # - Reminder tone filtering
        # - Message style changes
        # - Memory / journaling context
        #
        # Example later:
        # self.bot.dispatch("ai_tone_changed", profile_id)


async def setup(bot):
    await bot.add_cog(PresenceListener(bot))
