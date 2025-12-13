import discord
from discord.ext import commands
from discord import app_commands

from core.presence import switch_active_person



class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="help",
        description="What TinyRegg can do"
    )
    async def help(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "**TinyRegg — Overview**\n\n"
            "TinyRegg is a structured support system designed to help you keep moving, "
            "even when motivation, clarity, or energy are low.\n\n"

            "**Getting started**\n"
            "• `/start` — First-time setup and welcome\n"
            "• `/p help` — Presence, switching, and identity commands\n\n"

            "**Daily support**\n"
            "• Required grounding tasks each day\n"
            "• Optional tasks based on who’s present\n"
            "• Cloudy mode for low-clarity days\n\n"

            "**Progress & rewards**\n"
            "• Earn tokens for completed tasks\n"
            "• Spend tokens in the shop\n"
            "• Weekly bosses for showing up consistently\n\n"

            "**Organization & structure**\n"
            "• Admin-set deadlines and reminders\n"
            "• Clear task history and recent stats\n\n"

            "**Important things to know**\n"
            "• Nothing here is permanent\n"
            "• You’re never punished for struggling\n"
            "• Switching or going cloudy is always okay\n\n"

            "If you’re unsure what to do next, start with `/start` "
            "or use `/p help` to orient yourself.",
            ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(HelpCog(bot))
