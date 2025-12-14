import discord
from discord.ext import commands
from discord import app_commands

from core.db import get_connection
from core.presence import (
    get_active_profile,
    set_active_profile,
    set_cloudy_mode,
)


class PresenceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ─────────────────────────────────────────────
    # /p help
    # ─────────────────────────────────────────────
    @app_commands.command(
        name="p_help",
        description="How to use TinyRegg"
    )
    async def p_help(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "**TinyRegg — Presence Commands**\n\n"
            "`/p introduce` — Tell me who I’m talking to\n"
            "`/p switch` — Switch who’s fronting\n"
            "`/p cloudy` — Safe mode (no identity required)\n"
            "`/p edit` — Edit the current person\n\n"
            "You can change things at any time. Nothing is permanent.",
            ephemeral=True,
        )

    # ─────────────────────────────────────────────
    # /p switch
    # ─────────────────────────────────────────────
    @app_commands.command(
        name="p_switch",
        description="Switch who is fronting"
    )
    async def p_switch(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)

        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT profile_id, name FROM profiles WHERE user_id = ?",
            (user_id,),
        )
        profiles = cur.fetchall()
        conn.close()

        if not profiles:
            await interaction.response.send_message(
                "I don’t know anyone yet. Try `/p introduce`.",
                ephemeral=True,
            )
            return

        options = [
            discord.SelectOption(
                label=p["name"],
                value=str(p["profile_id"]),
            )
            for p in profiles
        ]

        select = discord.ui.Select(
            placeholder="Who’s here right now?",
            options=options,
        )

        async def on_select(interact: discord.Interaction):
            profile_id = int(select.values[0])
            set_active_profile(user_id, profile_id)
            await interact.response.send_message(
                "Okay. I’m with you now.",
                ephemeral=True,
            )

        select.callback = on_select

        view = discord.ui.View(timeout=60)
        view.add_item(select)

        await interaction.response.send_message(
            "Who’s fronting?",
            view=view,
            ephemeral=True,
        )

    # ─────────────────────────────────────────────
    # /p cloudy
    # ─────────────────────────────────────────────
    @app_commands.command(
        name="p_cloudy",
        description="Enter safe cloudy mode"
    )
    async def p_cloudy(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        set_cloudy_mode(user_id)

        await interaction.response.send_message(
            "Okay. We’ll keep things gentle and simple today.",
            ephemeral=True,
        )

    # ─────────────────────────────────────────────
    # /p edit
    # ─────────────────────────────────────────────
    @app_commands.command(
        name="p_edit",
        description="Edit the current person"
    )
    async def p_edit(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        profile = get_active_profile(user_id)

        if not profile:
            await interaction.response.send_message(
                "I don’t know who’s here right now.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"Editing **{profile['name']}**.\n\n"
            "Tell me what you want to change:\n"
            "- name\n"
            "- age context (adult / regressive)\n"
            "- intimacy\n"
            "- kink\n"
            "- explicit\n"
            "- gender\n"
            "- pronouns\n"
            "- nickname\n\n"
            "You can skip anything.",
            ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(PresenceCog(bot))
