import discord
from discord.ext import commands
from discord import ui
from datetime import datetime, timezone
from core.utils import get_connection
from core.theming import get_theme_colors

REY_ID = 160258339450781696
BELLA_ID = 868623435650175046


# -------------------------------------------------------------
# TIMESTAMP FORMATTING (Your choice: ALL FORMATS)
# -------------------------------------------------------------
def format_timestamp(ts_string):
    dt = datetime.fromisoformat(ts_string)
    unix = int(dt.replace(tzinfo=timezone.utc).timestamp())

    pretty = dt.strftime("%b %d, %Y — %I:%M %p")
    iso = dt.strftime("%Y-%m-%d %H:%M UTC")

    return pretty, iso, unix


# -------------------------------------------------------------
# PAGE VIEW FOR PENDING REWARDS
# -------------------------------------------------------------
class PendingPage(ui.View):
    def __init__(self, bot, records, page, per_page=3):
        super().__init__(timeout=180)
        self.bot = bot
        self.records = records
        self.page = page
        self.per_page = per_page

        max_page = max(0, (len(records) - 1) // per_page)
        self.max_page = max_page

        if page > 0:
            self.add_item(PrevButton())
        if page < max_page:
            self.add_item(NextButton())

        for record in self.records[self.page * per_page:(self.page + 1) * per_page]:
            code = record["reward_code"]
            btn = DeliverButton(code)
            self.add_item(btn)


class PrevButton(ui.Button):
    def __init__(self):
        super().__init__(label="← Prev", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        view: PendingPage = self.view
        await send_pending_page(interaction, view.bot, view.page - 1)


class NextButton(ui.Button):
    def __init__(self):
        super().__init__(label="Next →", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        view: PendingPage = self.view
        await send_pending_page(interaction, view.bot, view.page + 1)


# -------------------------------------------------------------
# DELIVER BUTTON (marks item delivered)
# -------------------------------------------------------------
class DeliverButton(ui.Button):
    def __init__(self, code):
        super().__init__(label=f"Deliver {code}", style=discord.ButtonStyle.success)
        self.code = code

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"Marking `{self.code}` delivered…",
            ephemeral=True
        )
        from shop.delivery_engine import deliver_reward
        success, msg = deliver_reward(interaction.client, self.code)

        await interaction.followup.send(
            msg,
            ephemeral=True
        )


# -------------------------------------------------------------
# SEND PAGINATED EMBED
# -------------------------------------------------------------
async def send_pending_page(interaction, bot, page):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM redemption_history
        WHERE delivered = 0
        ORDER BY redeemed_at ASC
    """)
    rows = cur.fetchall()
    conn.close()

    if not rows:
        await interaction.response.send_message(
            "🎉 No pending rituals — you're all caught up!",
            ephemeral=True
        )
        return

    theme = get_theme_colors("purple")

    embed = discord.Embed(
        title="🔮 Pending Ritual Deliveries",
        description="These rituals await fulfillment.",
        color=theme["purple"]
    )

    per_page = 3
    start = page * per_page
    end = start + per_page
    page_rows = rows[start:end]

    for row in page_rows:
        pretty, iso, unix = format_timestamp(row["redeemed_at"])

        embed.add_field(
            name=f"**{row['reward_code']} — {row['item_name']}**",
            value=(
                f"User: <@{row['user_id']}>\n"
                f"Category: `{row['category']}`\n"
                f"Cost: **{row['cost']} tokens**\n"
                f"Redeemed: **{pretty}**\n"
                f"`{iso}`\n"
                f"<t:{unix}:R>"
            ),
            inline=False
        )

    embed.set_footer(text=f"Page {page + 1}")

    view = PendingPage(bot, rows, page)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# -------------------------------------------------------------
# USER HISTORY COMMAND
# -------------------------------------------------------------
async def send_user_history(interaction, user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM redemption_history
        WHERE user_id = ?
        ORDER BY redeemed_at DESC
        LIMIT 20
    """, (user_id,))
    rows = cur.fetchall()
    conn.close()

    if not rows:
        await interaction.response.send_message(
            "You have no redeemed rituals yet.",
            ephemeral=True
        )
        return

    theme = get_theme_colors("purple")
    embed = discord.Embed(
        title="📜 Your Ritual History",
        color=theme["purple"]
    )

    for row in rows:
        pretty, iso, unix = format_timestamp(row["redeemed_at"])

        embed.add_field(
            name=f"{row['reward_code']} — {row['item_name']}",
            value=(
                f"Category: `{row['category']}`\n"
                f"Cost: {row['cost']}\n"
                f"Redeemed: **{pretty}**\n"
                f"<t:{unix}:R>"
            ),
            inline=False
        )

    await interaction.response.send_message(embed=embed, ephemeral=True)


# -------------------------------------------------------------
# ADMIN NOTES
# -------------------------------------------------------------
def add_admin_note(code, note):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO admin_notes (reward_code, note, timestamp)
        VALUES (?, ?, ?)
    """, (code, note, datetime.utcnow().isoformat()))

    conn.commit()
    conn.close()

    return True
