import datetime
from core.utils import get_connection
from core.theming import get_theme_colors


BELLA_ID = 868623435650175046
REY_ID = 160258339450781696


async def deliver_reward(bot, code):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM redemption_history
        WHERE reward_code = ?
    """, (code,))
    row = cur.fetchone()

    if not row:
        return False, "❌ Code not found."

    if row["delivered"] == 1:
        return False, "❌ Already delivered."

    cur.execute("""
        UPDATE redemption_history
        SET delivered = 1,
            delivered_at = ?
        WHERE reward_code = ?
    """, (datetime.datetime.utcnow().isoformat(), code))
    conn.commit()
    conn.close()

    # Notify Bella & Rey
    msg = (
        f"🔮 **Ritual Delivered**\n"
        f"Code: `{code}`\n"
        f"Item: **{row['item_name']}**\n"
        f"User: <@{row['user_id']}>"
    )

    bella = bot.get_user(BELLA_ID)
    rey = bot.get_user(REY_ID)

    if bella:
        try: await bella.send(msg)
        except: pass

    if rey:
        try: await rey.send(msg)
        except: pass

    return True, f"✔️ Ritual `{code}` marked delivered."
