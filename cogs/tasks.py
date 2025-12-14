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


# ------------------------------------------------------------
# Guards
# ------------------------------------------------------------

def has_started(user_id: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT has_started FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return bool(row and row["has_started"])


# ------------------------------------------------------------
# Normalizer (THIS WAS MISSING)
# ------------------------------------------------------------

def normalize_tasks(rows: list[dict]) -> dict:
    """
    Converts task rows into:
    {
        "required": {task_key: text},
        "core": {...},
        "intimacy": {...},
        "kink": {...},
        "explicit": {...},
    }
    """
    buckets = {
        "required": {},
        "core": {},
        "fun": {},
        "regressive": {},
        "intimacy": {},
        "kink": {},
        "explicit": {},
    }

    for r in rows:
        buckets.setdefault(r["category"], {})
        buckets[r["category"]][r["task_key"]] = r["text"]

    return buckets


# ------------------------------------------------------------
# Task Button
# ------------------------------------------------------------

class TaskButton(discord.ui.Button):
    def __init__(self, profile_id: int, task_key: str):
        super().__init__(label="Complete", style=discord.ButtonStyle.primary)
        self.profile_id = profile_id
        self.task_key = task_key

    async def callback(self, interaction: discord.Interaction):
        bot = interaction.client

        await complete_task_for_profile(
            bot=bot,
            profile_id=self.profile_id,
            task_key=self.task_key,
        )

        profile = get_active_profile(str(interaction.user.id))
        raw_tasks = get_tasks_for_profile(
            profile["profile_id"],
            date.today().isoformat(),
        )

        tasks = normalize_tasks(raw_tasks)

        embed, view = build_tasks_embed_and_view(
            interaction.user.id,
            profile,
            tasks,
        )

        await interaction.response.edit_message(embed=embed, view=view)


# ------------------------------------------------------------
# Embed Builder
# ------------------------------------------------------------

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

    embed.add_field(
        name="Required",
        value=section(tasks.get("required", {})),
        inline=False,
    )

    embed.add_field(
        name="Core",
        value=section(tasks.get("core", {})),
        inline=False,
    )

    if tasks.get("intimacy"):
        embed.add_field(
            name="Intimacy",
            value=section(tasks["intimacy"]),
            inline=False,
        )

    if tasks.get("kink"):
        embed.add_field(
            name="Kink",
            value=section(tasks["kink"]),
            inline=False,
        )

    if tasks.get("explicit"):
        embed.add_field(
            name="Explicit",
            value=section(tasks["explicit"]),
            inline=False,
        )

    embed.set_footer(text="Tasks update as you complete them.")

    view = discord.ui.View(timeout=None)

    for category in tasks.values():
        for task_key in category.keys():
            view.add_item(
                TaskButton(
                    profile_id=profile["profile_id"],
                    task_key=task_key,
                )
            )

    return embed, view


# ------------------------------------------------------------
# Cog
# ------------------------------------------------------------

class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --------------------------------------------------------
    # /tasks
    # --------------------------------------------------------

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

        raw_tasks = get_tasks_for_profile(
            profile["profile_id"],
            date.today().isoformat(),
        )

        tasks = normalize_tasks(raw_tasks)

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

    # --------------------------------------------------------
    # /task_history
    # --------------------------------------------------------

    @app_commands.command(
        name="task_history",
        description="See recent task history"
    )
    async def task_history(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)

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

        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT date, task_key, points_awarded
            FROM task_history
            WHERE profile_id = ?
            ORDER BY date DESC
            LIMIT 25
            """,
            (profile["profile_id"],),
        )
        rows = cur.fetchall()
        conn.close()

        if not rows:
            await interaction.response.send_message(
                "No task history yet.",
                ephemeral=True,
            )
            return

        name = profile["nickname"] or profile["name"]
        embed = discord.Embed(
            title=f"Task History — {name}",
            color=discord.Color.from_rgb(160, 120, 200),
        )

        embed.add_field(
            name="Recent",
            value="\n".join(
                f"• {r['date']} — `{r['task_key']}` (+{r['points_awarded']} tokens)"
                for r in rows
            ),
            inline=False,
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(Tasks(bot))
