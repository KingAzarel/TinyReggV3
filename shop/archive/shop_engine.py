# shop/shop_engine.py

import discord
from discord.ext import commands
from discord import app_commands
from typing import List, Dict

from core.db import get_connection
from shop.rewards import REWARDS, COZY, EXPRESSION, VOUCHERS, INTIMACY, KINK, EXPLICIT


# -------------------------------------------------------
# Helper: filter rewards per user settings + streak gate
# -------------------------------------------------------
def filter_rewards_for_user(user_id: str) -> Dict[str, List[dict]]:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT is_intimacy, is_kink, is_explicit, is_heavy FROM user_settings WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()

    if row is None:
        # default: only cozy + expression visible
        user_flags = {
            "intimacy": False,
            "kink": False,
            "explicit": False,
            "heavy": False,
        }
    else:
        user_flags = {
            "intimacy": row["is_intimacy"] == 1,
            "kink": row["is_kink"] == 1,
            "explicit": row["is_explicit"] == 1,
            "heavy": row["is_heavy"] == 1,
        }

    # Now fetch streak
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT task_streak FROM streaks WHERE user_id = ?", (user_id,))
    srow = cur.fetchone()
    conn.close()

    streak = srow["task_streak"] if srow else 0

    # Bucket categories
    pages = {
        COZY: [],
        EXPRESSION: [],
        VOUCHERS: [],
        INTIMACY: [],
        KINK: [],
        EXPLICIT: [],
    }

    for reward in REWARDS:
        # Streak lock
        if streak < reward["min_streak"]:
            continue

        # Opt-in locks
        if reward["requires_intimacy"] and not user_flags["intimacy"]:
            continue
        if reward["requires_kink"] and not user_flags["kink"]:
            continue
        if reward["requires_explicit"] and not user_flags["explicit"]:
            continue
        if reward["requires_heavy"] and not user_flags["heavy"]:
            continue

        pages[reward["category"]].append(reward)

    # Remove empty pages entirely
    return {cat: items for cat, items in pages.items() if len(items) > 0}


# -------------------------------------------------------
# Make embed for a category page
# -------------------------------------------------------
def make_shop_embed(category: str, items: List[dict], page_index: int, total_pages: int, streak: int):
    titles = {
        COZY: "Cozy Rewards",
        EXPRESSION: "Expression / Creative",
        VOUCHERS: "Voucher Rewards (Streak Locked)",
        INTIMACY: "Intimacy Tier (Opt-in)",
        KINK: "Kink Tier (Opt-in)",
        EXPLICIT: "Explicit Tier (Double Locked)",
    }

    embed = discord.Embed(
        title=f"🛍️ {titles.get(category, category)}",
        description=f"Your current streak: **{streak} days**",
        color=0xFFC0CB
    )

    for reward in items:
        embed.add_field(
            name=f"{reward['emoji']} {reward['name']} — {reward['cost']} tokens",
            value=reward["desc"],
            inline=False
        )

    embed.set_footer(text=f"Page {page_index + 1}/{total_pages}")
    return embed


# -------------------------------------------------------
# Pagination View with buttons
# -------------------------------------------------------
class ShopView(discord.ui.View):
    def __init__(self, user_id: str, pages: List[discord.Embed]):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.pages = pages
        self.index = 0

    async def update_message(self, interaction: discord.Interaction):
        embed = self.pages[self.index]
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="◀ Prev", style=discord.ButtonStyle.secondary)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != int(self.user_id):
            return await interaction.response.send_message("This isn't your shop menu.", ephemeral=True)

        self.index = (self.index - 1) % len(self.pages)
        await self.update_message(interaction)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != int(self.user_id):
            return await interaction.response.send_message("This isn't your shop menu.", ephemeral=True)

        self.index = (self.index + 1) % len(self.pages)
        await self.update_message(interaction)


# -------------------------------------------------------
# Purchase logic
# -------------------------------------------------------
def purchase_reward(user_id: str, reward_key: str) -> str:
    conn = get_connection()
    cur = conn.cursor()

    # fetch reward
    reward = next((r for r in REWARDS if r["key"] == reward_key), None)
    if reward is None:
        return "Invalid reward."

    # get token count
    cur.execute("SELECT tokens FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    if row is None:
        return "You do not have a token record yet."

    tokens = row["tokens"]
    if tokens < reward["cost"]:
        return "Not enough tokens."

    # deduct + log
    new_tokens = tokens - reward["cost"]
    cur.execute("UPDATE users SET tokens = ? WHERE user_id = ?", (new_tokens, user_id))
    cur.execute("INSERT INTO purchases (user_id, item_key) VALUES (?, ?)", (user_id, reward_key))
    conn.commit()
    conn.close()

    return f"Successfully redeemed **{reward['name']}**!"


# -------------------------------------------------------
# Cog: Slash commands for shop display + buying
# -------------------------------------------------------
class Shop(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # /shop
    @app_commands.command(name="shop", description="View your available rewards.")
    async def shop(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)

        # Fetch streak
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT task_streak FROM streaks WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        conn.close()

        streak = row["task_streak"] if row else 0

        pages_data = filter_rewards_for_user(user_id)

        if not pages_data:
            return await interaction.response.send_message(
                "No rewards available yet. Keep building your streak!",
                ephemeral=True
            )

        embeds = []
        categories = list(pages_data.keys())

        for cat in categories:
            items = pages_data[cat]
            embed = make_shop_embed(
                category=cat,
                items=items,
                page_index=len(embeds),
                total_pages=len(categories),
                streak=streak
            )
            embeds.append(embed)

        view = ShopView(user_id=user_id, pages=embeds)
        await interaction.response.send_message(embed=embeds[0], view=view)

    # /buy key:<reward>
    @app_commands.command(name="buy", description="Redeem a reward using your tokens.")
    @app_commands.describe(key="The reward key, as listed in /shop")
    async def buy(self, interaction: discord.Interaction, key: str):
        user_id = str(interaction.user.id)
        result = purchase_reward(user_id, key)

        # DM confirmation if purchased
        if result.startswith("Successfully redeemed"):
            try:
                await interaction.user.send(f"🎁 **{result}**")
            except discord.Forbidden:
                pass

        await interaction.response.send_message(result, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Shop(bot))
