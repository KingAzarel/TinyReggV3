import discord
from discord.ext import commands
from discord import app_commands
from datetime import date

from core.db import get_connection
from core.task_engine import (
    generate_daily_tasks,
    get_tasks_for_profile,
    complete_task_for_profile,
)
from core.theming import inject_names
from core.users import ensure_user
from core.presence import get_active_profile


def has_started(user_id: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT has_started FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return bool(row and row["has_started"])


class TaskButton(discord.ui.Button):
    def __init__(self, profile_id: int, task_key: str):
        super().__init__(label="Complete", style=discord.ButtonStyle.primary)
        self.profile_id = profile_id
        self.task_key = task_key

    async def callback(self, interaction: discord.Interaction):
        complete_task_for_profile(self.profile_id, self.task_key)

        profile = get_active_profile(str(interaction.user.id))
        tasks = get_tasks_for_profile(
            profile["profile_id"],
            date.today().isoformat(),
        )

        embed, view = build_tasks_embed_and_view(
            interaction.user.id,
            profile,
            tasks,
        )

        await interaction.response.edit_message(embed=embed, view=view)


def build_tasks_embed_and_view(user_id: int, profile: dict, tasks: dict):
    title_name = profile["nickname"] or profile["name"]

    embed = discord.Embed(
        title=f"Tasks for Today — {title_name}",
        color=discord.Color.from_rgb(160, 120, 200),
    )

    def section(items: dict):
        if not items:
            return "✔ Nothing left here."
        return "\n".join(
            f"• {inject_names(text, user_id)}"
            for text in items.values()
        )

    embed.add_field("Required", section(tasks.get("required", {})), inline=False)
    embed.add_field("Core", section(tasks.get("core", {})), inline=False)

    for optional in ("intimacy", "kink", "explicit"):
        if tasks.get(optional):
            embed.add_field(
                name=optional.capitalize(),
                value=section(tasks[optional]),
                inline=False,
            )

    embed.set_footer(text="Tasks update as you complete them.")

    view = discord.ui.View(timeout=None)
    seen = set()

    for category in tasks.values():
        for task_key in category:
            if task_key in seen:
                continue
            seen.add(task_key)
            view.add_item(TaskButton(profile["profile_id"], task_key))

    return embed, view


class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="tasks", description="Show today’s tasks")
    async def tasks(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        ensure_user(user_id)

        if not has_started(user_id):
            await interaction.response.send_message(
                "Let’s start first 💜 Use `/start`.",
                ephemeral=True,
            )
            return

        profile = get_active_profile(user_id)
        if not profile:
            await interaction.response.send_message(
                "I’m not sure who’s here yet.",
                ephemeral=True,
            )
            return

        generate_daily_tasks(profile["profile_id"])

        tasks = get_tasks_for_profile(
            profile["profile_id"],
            date.today().isoformat(),
        )

        embed, view = build_tasks_embed_and_view(
            interaction.user.id,
            profile,
            tasks,
        )

        await interaction.response.send_message(
            embed=embed,
            view=view,
            ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(Tasks(bot))
