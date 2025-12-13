import discord
from discord.ui import Button, View
from core.db import get_connection
from core.theming import inject_names
from core.task_rewards import handle_task_completion
from core.presence import get_current_presence


class TaskCompleteButton(Button):
    def __init__(self, user_id, profile_id, task_key, label="Complete"):
        super().__init__(
            style=discord.ButtonStyle.success,
            label=label,
            custom_id=f"complete:{task_key}",
        )
        self.user_id = user_id
        self.profile_id = profile_id
        self.task_key = task_key

    async def callback(self, interaction: discord.Interaction):
        # Safety: only allow the owner
        if str(interaction.user.id) != str(self.user_id):
            await interaction.response.send_message(
                "This button isn’t for you.",
                ephemeral=True,
            )
            return

        conn = get_connection()
        cur = conn.cursor()

        # Check if already completed
        cur.execute(
            """
            SELECT completed
            FROM task_history
            WHERE profile_id = ?
              AND task_key = ?
              AND date = DATE('now')
            """,
            (self.profile_id, self.task_key),
        )
        row = cur.fetchone()

        if row and row["completed"] == 1:
            conn.close()
            await interaction.response.send_message(
                "That task is already complete 💜",
                ephemeral=True,
            )
            return

        # Mark task as completed in history
        cur.execute(
            """
            INSERT INTO task_history (profile_id, date, task_key, completed)
            VALUES (?, DATE('now'), ?, 1)
            ON CONFLICT(profile_id, date, task_key)
            DO UPDATE SET completed = 1
            """,
            (self.profile_id, self.task_key),
        )

        # Reveal the task in assigned_tasks
        cur.execute(
            """
            UPDATE assigned_tasks
            SET hidden_until_complete = 0
            WHERE profile_id = ?
              AND task_key = ?
              AND date = DATE('now')
            """,
            (self.profile_id, self.task_key),
        )

        conn.commit()
        conn.close()

        # Handle rewards, streaks, messaging
        completion_message = handle_task_completion(
            user_id=self.user_id,
            profile_id=self.profile_id,
            task_key=self.task_key,
        )

        # Inject theming (nickname / pronouns)
        completion_message = inject_names(
            completion_message,
            self.user_id,
        )

        await interaction.response.send_message(
            completion_message,
            ephemeral=True,
        )


class TaskButtonsView(View):
    def __init__(self, user_id, profile_id, tasks):
        super().__init__(timeout=None)

        for task in tasks:
            self.add_item(
                TaskCompleteButton(
                    user_id=user_id,
                    profile_id=profile_id,
                    task_key=task["key"],
                )
            )
