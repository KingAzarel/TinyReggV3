import random

# ─────────────────────────────────────────────
# REQUIRED / CARE (All modes, grounding)
# ─────────────────────────────────────────────

REQUIRED_MESSAGES = [
    "Good job, {sub}. You did what you needed today. (+{tokens} tokens)",
    "I’m proud of you, babydoll. One step at a time. (+{tokens} tokens)",
    "That mattered, {sub}. You showed up. (+{tokens} tokens)",
    "You took care of something important, babydoll. (+{tokens} tokens)",
]


# ─────────────────────────────────────────────
# CORE / DAILY MOMENTUM
# ─────────────────────────────────────────────

CORE_MESSAGES = [
    "Nicely done, {sub}. I see your effort. (+{tokens} tokens)",
    "You handled that well, my boy. (+{tokens} tokens)",
    "That was a good choice, babydoll. (+{tokens} tokens)",
    "Beautiful work, babyboy. (+{tokens} tokens)",
]


# ─────────────────────────────────────────────
# REGRESSIVE / SOFT SPACE
# ─────────────────────────────────────────────

REGRESSIVE_MESSAGES = [
    "You did so good, little one. (+{tokens} tokens)",
    "That was enough, my sweet boy. (+{tokens} tokens)",
    "I’m really proud of you, babydoll. (+{tokens} tokens)",
    "You’re safe — you did well, sweetheart. (+{tokens} tokens)",
]


# ─────────────────────────────────────────────
# INTIMACY / CLOSENESS (Non-D/s)
# ─────────────────────────────────────────────

INTIMACY_MESSAGES = [
    "Thank you for sharing that with me, {sub}. (+{tokens} tokens)",
    "That felt close. I liked that, babydoll. (+{tokens} tokens)",
    "Your softness is safe with me, my prince. (+{tokens} tokens)",
    "I felt you there, babyboy. (+{tokens} tokens)",
]


# ─────────────────────────────────────────────
# KINK / POWER DYNAMIC (Intentional rotation)
# ─────────────────────────────────────────────

KINK_MESSAGES = [
    "Good boy… you followed beautifully. (+{tokens} tokens)",
    "That obedience was noted, babydoll. (+{tokens} tokens)",
    "Just like that. You listened well, my boy. (+{tokens} tokens)",
    "You pleased me, babyboy. (+{tokens} tokens)",
]


# ─────────────────────────────────────────────
# EXPLICIT / HIGH INTENSITY (Rare, charged)
# ─────────────────────────────────────────────

EXPLICIT_MESSAGES = [
    "Good boy. That was exactly what I wanted. (+{tokens} tokens)",
    "You gave yourself to that so well, babydoll… (+{tokens} tokens)",
    "That control you offered felt delicious, my boy. (+{tokens} tokens)",
    "You’re making it very hard not to take you further. (+{tokens} tokens)",
]


# ─────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────

def get_completion_message(category: str, is_required: bool = False) -> str:
    """
    Returns a raw message template.
    Token values and names are injected later.
    """

    if is_required:
        return random.choice(REQUIRED_MESSAGES)

    match category:
        case "core":
            return random.choice(CORE_MESSAGES)
        case "regressive":
            return random.choice(REGRESSIVE_MESSAGES)
        case "intimacy":
            return random.choice(INTIMACY_MESSAGES)
        case "kink":
            return random.choice(KINK_MESSAGES)
        case "explicit":
            return random.choice(EXPLICIT_MESSAGES)
        case _:
            return "Task completed. (+{tokens} tokens)"
