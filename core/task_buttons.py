import discord
from discord.ui import Button, View
from datetime import date

from core.task_engine import complete_task_for_profile, get_tasks_for_profile
from core.theming import inject_names
from core.presence import get_active_profile


class TaskCompleteButton(Button):
    def __init__(self, user_id: str, profile_id: int, task_key: str):
        super().__init__(
            style=discord.ButtonStyle.success,
            label="Complete",
            custom_id=f"task:{profile_id}:{task_key}",
        )
        self.user_id = str(user_id)
        self.profile_id = profile_id
        self.task_key = task_key

    async def callback(self, interaction: discord.Interaction):
        # 🔒 Owner check
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message(
                "This button isn’t for you.",
                ephemeral=True,
            )
            return

        # ✅ Complete task (SYNC engine call)
        complete_task_for_profile(
            profile_id=self.profile_id,
            task_key=self.task_key,
        )

        # 🔄 Refresh active profile
        profile = get_active_profile(self.user_id)
        if not profile:
            await interaction.response.send_message(
                "I’m not sure who’s here right now.",
                ephemeral=True,
            )
            return

        # 🔄 Fetch updated tasks
        tasks = get_tasks_for_profile(
            profile_id=profile["profile_id"],
            date=date.today().isoformat(),
        )

        # 🔧 Rebuild embed + buttons
        from cogs.tasks import build_tasks_embed_and_view

        embed, view = build_tasks_embed_and_view(
            interaction.user.id,
            profile,
            tasks,
        )

        await interaction.response.edit_message(
            embed=embed,
            view=view,
        )


class TaskButtonsView(View):
    def __init__(self, user_id: str, profile_id: int, tasks: dict):
        super().__init__(timeout=None)

        for category in tasks.values():
            for task_key in category.keys():
                self.add_item(
                    TaskCompleteButton(
                        user_id=user_id,
                        profile_id=profile_id,
                        task_key=task_key,
                    )
                )
