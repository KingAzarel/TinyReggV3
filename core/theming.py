from typing import Dict
from core.db import get_connection

# ------------------------------------------------------------
# Defaults
# ------------------------------------------------------------

DEFAULT_SUB_FALLBACK = "you"
DEFAULT_DOM_FALLBACK = "Regg"

DEFAULT_PRONOUNS = {
    "they": "they",
    "them": "them",
    "their": "their",
    "theirs": "theirs",
    "themself": "themself",
}


# ------------------------------------------------------------
# Pronoun Parsing
# ------------------------------------------------------------

def parse_pronouns(raw: str | None) -> Dict[str, str]:
    """
    Accepts:
    - she/her
    - he/him
    - they/them
    - xe/xem
    - custom text
    - None

    Returns a complete pronoun map with safe fallbacks.
    """

    if not raw:
        return DEFAULT_PRONOUNS.copy()

    parts = raw.replace(" ", "").split("/")
    if len(parts) < 2:
        return {
            "they": raw,
            "them": raw,
            "their": raw,
            "theirs": raw,
            "themself": raw,
        }

    subject = parts[0]
    obj = parts[1]

    # Known common sets
    if subject == "he":
        possessive = "his"
        reflexive = "himself"
    elif subject == "she":
        possessive = "her"
        reflexive = "herself"
    elif subject == "they":
        possessive = "their"
        reflexive = "themself"
    else:
        # Fallback for neopronouns / custom sets
        possessive = subject
        reflexive = obj + "self"

    return {
        "they": subject,
        "them": obj,
        "their": possessive,
        "theirs": possessive,
        "themself": reflexive,
    }


# ------------------------------------------------------------
# Active Profile Resolution
# ------------------------------------------------------------

def get_active_profile(user_id: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            profile_id,
            name,
            pronouns,
            nickname,
            age_context,
            intimacy_opt_in,
            kink_opt_in,
            explicit_opt_in
        FROM profiles
        WHERE user_id = ?
          AND is_active = 1
        """,
        (user_id,),
    )

    row = cur.fetchone()
    conn.close()
    return row



# ------------------------------------------------------------
# Name Injection
# ------------------------------------------------------------

def inject_names(template: str, user_id: str) -> str:
    """
    Replaces:
    - {sub}
    - {dom}
    - pronoun tokens (they/them/their/etc)

    Fails safely if anything is missing.
    """

    profile = get_active_profile(user_id)

    sub_name = profile["nickname"] if profile and profile["nickname"] else (
        profile["name"] if profile else DEFAULT_SUB_FALLBACK
    )

    pronouns = parse_pronouns(profile["pronouns"] if profile else None)

    context = {
        "sub": sub_name,
        "dom": DEFAULT_DOM_FALLBACK,
        **pronouns,
    }

    try:
        return template.format(**context)
    except Exception:
        return template


# ------------------------------------------------------------
# Theme Colors
# ------------------------------------------------------------

def get_theme_colors(theme: str):
    THEMES = {
        "purple": {
            "purple": 0x9B59B6,
            "soft": 0xC39BD3,
        },
        "pink": {
            "pink": 0xF5B7B1,
            "soft": 0xFADBD8,
        },
    }

    return THEMES.get(theme, THEMES["purple"])

# core/theming.py

def inject_names(text: str, profile=None):
    """
    Temporary compatibility shim.

    Later this will:
    - inject profile name
    - adjust tone
    - apply AI theming

    For now, pass-through.
    """
    return text

