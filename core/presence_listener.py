import logging
import inspect
from discord.ext import commands

from core.task_engine import reassess_tasks_for_profile

log = logging.getLogger("tinyregg.presence_listener")


class PresenceListener(commands.Cog):
    """
    Reacts to presence/fronting changes.

    This is the orchestration layer between presence and
    downstream systems like:
    - task generation
    - AI tone
    - reminders
    - journaling context
    """

    def __init__(self, bot):
        self.bot = bot
        log.info("PresenceListener initialized")

    # ─────────────────────────────────────────────
    # Presence change event
    # ─────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_presence_changed(self, user_id: str, profile_id: int):
        """
        Fired whenever the active presence/profile changes.
        Dispatched by core.presence.emit_presence_changed().
        """

        log.info(
            "Presence changed: user=%s profile=%s",
            user_id,
            profile_id,
        )

        # 🔁 TASK REASSESSMENT
        try:
            result = reassess_tasks_for_profile(profile_id)

            # allow reassess to be sync OR async
            if inspect.isawaitable(result):
                await result

        except Exception:
            log.exception(
                "Failed to reassess tasks "
                "(user=%s, profile=%s)",
                user_id,
                profile_id,
            )

        # 🧠 FUTURE HOOKS (INTENTIONAL STUBS)
        # ─────────────────────────────────────────
        # Examples for later expansion:
        #
        # self.bot.dispatch("ai_tone_changed", profile_id)
        # self.bot.dispatch("reminder_context_changed", profile_id)
        # self.bot.dispatch("journal_context_changed", profile_id)
        #
        # Do NOT remove — this is the system spine.


async def setup(bot):
    await bot.add_cog(PresenceListener(bot))
