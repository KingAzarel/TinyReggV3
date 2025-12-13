"""
Reward definitions for the TinyRegg shop.
Keys are canonical and used everywhere else.
"""

# ---- CATEGORY CONSTANTS ----
COZY = "cozy"
EXPRESSION = "expression"
VOUCHERS = "vouchers"
INTIMACY = "intimacy"
KINK = "kink"
EXPLICIT = "explicit"

REWARDS = {
    # -----------------------------
    # Cozy Rewards (always visible)
    # -----------------------------
    "story": {
        "key": "story",
        "name": "Bedtime Story",
        "emoji": "📖",
        "cost": 10,
        "desc": "Regg reads or writes you a soft bedtime story.",
        "category": COZY,
        "min_streak": 0,
        "cloudy_safe": True,
        "requires_intimacy": False,
        "requires_kink": False,
        "requires_explicit": False,
    },
    "playlist": {
        "key": "playlist",
        "name": "Custom Playlist",
        "emoji": "🎧",
        "cost": 15,
        "desc": "A playlist crafted by Regg just for your mood.",
        "category": COZY,
        "min_streak": 0,
        "cloudy_safe": True,
        "requires_intimacy": False,
        "requires_kink": False,
        "requires_explicit": False,
    },
    "comfort_note": {
        "key": "comfort_note",
        "name": "Comfort Letter",
        "emoji": "💌",
        "cost": 12,
        "desc": "A personalized comfort message written softly by Regg.",
        "category": COZY,
        "min_streak": 0,
        "cloudy_safe": True,
        "requires_intimacy": False,
        "requires_kink": False,
        "requires_explicit": False,
    },

    # -----------------------------------
    # Expression Rewards
    # -----------------------------------
    "pg_photo": {
        "key": "pg_photo",
        "name": "Cute Photo Request",
        "emoji": "📷",
        "cost": 20,
        "desc": "Send Regg a cozy, PG-safe selfie or photo.",
        "category": EXPRESSION,
        "min_streak": 0,
        "cloudy_safe": True,
        "requires_intimacy": False,
        "requires_kink": False,
        "requires_explicit": False,
    },
    "poem": {
        "key": "poem",
        "name": "A Poem From Regg",
        "emoji": "🖋️",
        "cost": 25,
        "desc": "Regg writes you a short poem.",
        "category": EXPRESSION,
        "min_streak": 0,
        "cloudy_safe": True,
        "requires_intimacy": False,
        "requires_kink": False,
        "requires_explicit": False,
    },

    # -----------------------------
    # Voucher Rewards (streak lock)
    # -----------------------------
    "voucher_25": {
        "key": "voucher_25",
        "name": "$25 Voucher",
        "emoji": "🧧",
        "cost": 150,
        "desc": "$25 for pulls or gifts.",
        "category": VOUCHERS,
        "min_streak": 7,
        "cloudy_safe": False,
        "requires_intimacy": False,
        "requires_kink": False,
        "requires_explicit": False,
    },

    # -----------------------------
    # Intimacy Tier
    # -----------------------------
    "int_soft_voice": {
        "key": "int_soft_voice",
        "name": "Soft Voice Note",
        "emoji": "🎙️",
        "cost": 15,
        "desc": "Regg sends you a tender voice note.",
        "category": INTIMACY,
        "min_streak": 7,
        "cloudy_safe": False,
        "requires_intimacy": True,
        "requires_kink": False,
        "requires_explicit": False,
    },

    # -----------------------------
    # Kink Tier
    # -----------------------------
    "kink_lovense": {
        "key": "kink_lovense",
        "name": "Lovense Command",
        "emoji": "💗",
        "cost": 20,
        "desc": "Regg gives you a short guided Lovense command.",
        "category": KINK,
        "min_streak": 14,
        "cloudy_safe": False,
        "requires_intimacy": True,
        "requires_kink": True,
        "requires_explicit": False,
    },

    # -----------------------------
    # Explicit Tier
    # -----------------------------
    "explicit_heavy_script": {
        "key": "explicit_heavy_script",
        "name": "Heavy Script",
        "emoji": "🔥",
        "cost": 30,
        "desc": "A heavy submissive script written specifically for you.",
        "category": EXPLICIT,
        "min_streak": 28,
        "cloudy_safe": False,
        "requires_intimacy": True,
        "requires_kink": True,
        "requires_explicit": True,
    },
}
