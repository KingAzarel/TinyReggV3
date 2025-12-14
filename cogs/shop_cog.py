import discord
from discord.ext import commands
from discord import app_commands

from core.presence import get_active_profile
from core.reward_engine import generate_reward
from shop.rewards import REWARDS


class ShopCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ─────────────────────────────────────────────
    # /shop — view available rewards
    # ─────────────────────────────────────────────
    @app_commands.command(
        name="shop",
        description="Browse available rewards"
    )
    async def shop(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        profile = get_active_profile(user_id)

        if not profile:
            await interaction.response.send_message(
                "I don’t know who’s here right now.\n"
                "Try `/p introduce`, `/p switch`, or `/p cloudy`.",
                ephemeral=True,
            )
            return

        available = []

        for key, reward in REWARDS.items():
            if self._reward_allowed(profile, reward):
                available.append((key, reward))

        if not available:
            await interaction.response.send_message(
                f"Nothing available right now for **{profile['name']}**.",
                ephemeral=True,
            )
            return

        lines = [f"**Available rewards for {profile['name']}**\n"]

        for key, reward in available:
            lines.append(
                f"**{reward['name']}** — {reward['cost']} tokens\n"
                f"`/buy {key}`"
            )

        await interaction.response.send_message(
            "\n\n".join(lines),
            ephemeral=True,
        )

    # ─────────────────────────────────────────────
    # /buy — redeem a reward
    # ─────────────────────────────────────────────
    @app_commands.command(
        name="buy",
        description="Redeem a reward"
    )
    async def buy(self, interaction: discord.Interaction, item_key: str):
        user_id = str(interaction.user.id)
        profile = get_active_profile(user_id)

        if not profile:
            await interaction.response.send_message(
                "I don’t know who’s here right now.",
                ephemeral=True,
            )
            return

        if item_key not in REWARDS:
            await interaction.response.send_message(
                "That reward doesn’t exist.",
                ephemeral=True,
            )
            return

        result = generate_reward(
            user_id=user_id,
            profile_id=profile["profile_id"],
            item_key=item_key,
        )

        if not result:
            await interaction.response.send_message(
                "That reward isn’t available right now.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"💜 **{profile['name']}** redeemed **{result['name']}**.\n"
            "I’ll take care of the rest.",
            ephemeral=True,
        )

    # ─────────────────────────────────────────────
    # Internal helper
    # ─────────────────────────────────────────────
    def _reward_allowed(self, profile: dict, reward: dict) -> bool:
        """
        Local filtering for shop display.
        Final validation happens in reward_engine.
        """

        # Cloudy safety
        if profile["age_context"] == "cloudy":
            return reward.get("cloudy_safe", False)

        # Regressive safety
        if profile["age_context"] == "regressive":
            if reward.get("requires_kink") or reward.get("requires_explicit"):
                return False

        # Intimacy
        if reward.get("requires_intimacy") and not profile["intimacy_opt_in"]:
            return False

        # Kink
        if reward.get("requires_kink") and not profile["kink_opt_in"]:
            return False

        # Explicit
        if reward.get("requires_explicit") and not profile["explicit_opt_in"]:
            return False

        return True


async def setup(bot):
    await bot.add_cog(ShopCog(bot))
