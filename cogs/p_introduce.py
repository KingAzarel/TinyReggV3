import discord
from discord.ext import commands
from discord import app_commands

from core.db import get_connection
from core.users import ensure_user
from core.presence import emit_presence_changed, switch_active_person
from core.presence import switch_active_person



# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def create_person(user_id: str, data: dict) -> int:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO profiles (
            user_id,
            name,
            age_context,
            intimacy_opt_in,
            kink_opt_in,
            explicit_opt_in,
            gender,
            pronouns,
            nickname,
            is_active
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        """,
        (
            user_id,
            data["name"],
            data["age_context"],
            data["intimacy"],
            data["kink"],
            data["explicit"],
            data["gender"],
            data["pronouns"],
            data["nickname"],
        ),
    )

    pid = cur.lastrowid
    conn.commit()
    conn.close()
    return pid


# ─────────────────────────────────────────────────────────────
# Introduce Flow
# ─────────────────────────────────────────────────────────────

class IntroduceFlow(discord.ui.View):
    """
    Gentle, step-by-step introduction.
    Everything is optional.
    Skipping safety questions defaults to cloudy.
    """

    def __init__(self, bot, interaction: discord.Interaction):
        super().__init__(timeout=600)
        self.bot = bot
        self.interaction = interaction
        self.user_id = str(interaction.user.id)

        self.data = {
            "name": None,
            "age_context": "cloudy",
            "intimacy": 0,
            "kink": 0,
            "explicit": 0,
            "gender": None,
            "pronouns": None,
            "nickname": None,
        }

    # ─────────────────────────────────────────────
    # Utilities
    # ─────────────────────────────────────────────

    async def ask(self, prompt: str):
        await self.interaction.followup.send(prompt, ephemeral=True)
        msg = await self.bot.wait_for(
            "message",
            check=lambda m: m.author.id == self.interaction.user.id
            and m.channel == self.interaction.channel,
            timeout=300,
        )
        return msg.content.strip()

    async def yes_no(self, prompt: str) -> int:
        reply = (await self.ask(prompt + " (yes / no — or skip)")).lower()
        if reply.startswith("y"):
            return 1
        return 0

    # ─────────────────────────────────────────────
    # Flow
    # ─────────────────────────────────────────────

    async def start(self):
        await self.interaction.followup.send(
            "Hey. I’m really glad you’re here.\n\nLet’s take this one step at a time.",
            ephemeral=True,
        )

        # Name
        name = await self.ask(
            "Who am I talking to right now?\n(You can say a name — or type `skip`.)"
        )
        if name.lower() != "skip":
            self.data["name"] = name
        else:
            self.data["name"] = "Someone Soft"

        # Age context
        age = await self.ask(
            "Are you feeling **adult**, **regressive**, or **unsure** right now?\n"
            "(You can type one — or `skip`.)"
        )
        if age.lower() in ("adult", "regressive"):
            self.data["age_context"] = age.lower()
        else:
            self.data["age_context"] = "cloudy"

        # Opt-ins (only if adult)
        if self.data["age_context"] == "adult":
            self.data["intimacy"] = await self.yes_no(
                "Would you like gentle intimacy-based tasks?"
            )
            self.data["kink"] = await self.yes_no(
                "Would you like kink / D/s flavored tasks?"
            )
            if self.data["kink"]:
                self.data["explicit"] = await self.yes_no(
                    "Are explicit tasks okay too?"
                )

        # Gender
        gender = await self.ask(
            "If you’d like, how do you describe your gender?\n(`skip` is okay.)"
        )
        if gender.lower() != "skip":
            self.data["gender"] = gender

        # Pronouns
        pronouns = await self.ask(
            "What pronouns do you want me to use for you?\n(`skip` is okay.)"
        )
        if pronouns.lower() != "skip":
            self.data["pronouns"] = pronouns

        # Nickname
        nickname = await self.ask(
            "Is there a nickname or pet name you like?\n(`skip` is okay.)"
        )
        if nickname.lower() != "skip":
            self.data["nickname"] = nickname

        # Create + activate
        pid = create_person(self.user_id, self.data)
        switch_active_person(self.user_id, pid)
        await emit_presence_changed(self.bot, self.user_id, pid)

        await self.interaction.followup.send(
            "Thank you for trusting me with that.\n\n"
            "You can always change or edit things later.\n\n"
            "Whenever you’re ready, try `/tasks`.",
            ephemeral=True,
        )

        self.stop()


# ─────────────────────────────────────────────────────────────
# Cog
# ─────────────────────────────────────────────────────────────

class Introduce(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="p_introduce",
        description="Tell me who you are, gently and at your own pace",
    )
    async def introduce(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        ensure_user(user_id)

        await interaction.response.send_message(
            "I’ll stay with you while we do this.",
            ephemeral=True,
        )

        flow = IntroduceFlow(self.bot, interaction)
        await flow.start()


async def setup(bot):
    await bot.add_cog(Introduce(bot))
