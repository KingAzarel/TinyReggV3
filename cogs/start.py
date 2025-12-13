import discord
from discord import app_commands
from discord.ext import commands

from core.users import ensure_user
from core.db import get_connection
from core.presence import switch_active_person



class StartCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ------------------------------------------------------------
    # INTERNAL HELPERS
    # ------------------------------------------------------------

    def _has_started(self, user_id: str) -> bool:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT has_started FROM users WHERE user_id = ?",
            (user_id,),
        )
        row = cur.fetchone()
        conn.close()

        return bool(row and row["has_started"])

    def _mark_started(self, user_id: str):
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            "UPDATE users SET has_started = 1 WHERE user_id = ?",
            (user_id,),
        )

        conn.commit()
        conn.close()

    # ------------------------------------------------------------
    # /start COMMAND
    # ------------------------------------------------------------

    @app_commands.command(name="start", description="Begin your journey with TinyRegg")
    async def start(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)

        # Ensure base user exists
        ensure_user(user_id)

        # Prevent re-running onboarding
        if self._has_started(user_id):
            await interaction.response.send_message(
                "You’ve already started 💜\n\n"
                "If you want to switch who’s here or make changes, you can use `/p help`.",
                ephemeral=True,
            )
            return

        self._mark_started(user_id)

        # --------------------------------------------------------
        # WELCOME MESSAGE
        # --------------------------------------------------------

        embed = discord.Embed(
            title="Welcome. I’m TinyRegg.",
            description=(
                "I’m here to help you take care of yourself — gently, consistently, "
                "and without pressure.\n\n"
                "Some days you’ll have energy. Some days you won’t.\n"
                "Some days you’ll feel grown, playful, small, soft, or unsure.\n\n"
                "You get to tell me **who’s here today**, and I’ll meet you there."
            ),
            color=discord.Color.from_rgb(160, 120, 200),
        )

        embed.add_field(
            name="What I can do",
            value=(
                "• Offer small daily tasks\n"
                "• Encourage you without shame\n"
                "• Track progress gently\n"
                "• Give rewards that feel personal\n"
            ),
            inline=False,
        )

        embed.add_field(
            name="Important to know",
            value=(
                "Nothing intimate, romantic, or explicit ever happens without your consent.\n"
                "You are always in control.\n\n"
                "You can change your preferences at any time."
            ),
            inline=False,
        )

        embed.set_footer(text="When you’re ready, let me know who I’m talking to.")

        # --------------------------------------------------------
        # BUTTON → HANDOFF TO PRESENCE / INTRO
        # --------------------------------------------------------

        view = discord.ui.View(timeout=None)

        class IntroduceButton(discord.ui.Button):
            def __init__(self):
                super().__init__(
                    label="Introduce myself",
                    style=discord.ButtonStyle.primary,
                )

            async def callback(self, button_interaction: discord.Interaction):
                await button_interaction.response.send_message(
                    "Alright 💜\n\nLet’s take this one step at a time.\n"
                    "Use `/p introduce` when you’re ready.",
                    ephemeral=True,
                )

        view.add_item(IntroduceButton())

        await interaction.response.send_message(
            embed=embed,
            view=view,
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(StartCog(bot))
