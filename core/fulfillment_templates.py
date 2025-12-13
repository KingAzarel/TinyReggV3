# This file ONLY formats reward delivery messages.
# Tone, names, and consent are handled elsewhere.


def reward_delivered(item_name, profile_name):
    """
    Used when a reward has been successfully delivered.
    """
    return (
        f"✨ **Reward Delivered** ✨\n\n"
        f"**Item:** {item_name}\n"
        f"**Redeemed by:** {profile_name}\n\n"
        f"Enjoy it 💜"
    )


def reward_pending(item_name, profile_name):
    """
    Used when a reward is logged but not yet delivered.
    """
    return (
        f"🕯 **Reward Queued** 🕯\n\n"
        f"**Item:** {item_name}\n"
        f"**Redeemed by:** {profile_name}\n\n"
        f"I’ll take care of the rest."
    )


def reward_failed(item_name):
    """
    Used if something goes wrong.
    """
    return (
        f"⚠️ **Something went wrong** ⚠️\n\n"
        f"I couldn’t deliver **{item_name}** just yet.\n"
        f"It hasn’t been lost — we can retry."
    )
