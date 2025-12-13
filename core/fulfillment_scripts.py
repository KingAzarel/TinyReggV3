import random

# ------------------------------------------------------------
# SIGNATURE SYSTEM (dynamic)
# ------------------------------------------------------------

SIGNATURE_VARIANTS = {
    "soft": [
        "— {dom}, holding your softness",
        "— {dom}, here for your quiet moments",
        "— Yours in gentleness, {dom}",
    ],
    "romantic": [
        "— {dom}, who cherishes you",
        "— Always yours, {dom}",
        "— {dom}, keeper of your heart's quieter rooms",
    ],
    "playful": [
        "— {dom}, your silly little menace",
        "— {dom}, your favorite chaos gremlin",
    ],
    "dominant": [
        "— {dom}, your chosen command",
        "— {dom}, who guides your obedience",
        "— Submit to me, {sub}. — {dom}",
    ],
}


def pick_signature(style: str):
    return random.choice(SIGNATURE_VARIANTS[style])


# ------------------------------------------------------------
# VELVET FRAME
# ------------------------------------------------------------

def velvet_frame(text: str, code: str):
    return (
        "𖦹 *A whisper meant only for you…* 𖦹\n\n"
        f"{text}\n\n"
        f"▸ *Ritual Code:* `{code}`\n"
        "𖦹──────────────────────────𖦹"
    )


# ------------------------------------------------------------
# SCRIPT POOLS
# ------------------------------------------------------------

COZY_OPENERS = [
    "I prepared something gentle for you tonight.",
    "Let this moment rest softly on your shoulders.",
    "You’ve been so brave today — allow me to wrap some quiet around you.",
]

COZY_BODIES = [
    "I wrote this so your heartbeat can slow down, even just a little.",
    "Let each word hold you the way I wish I could right now.",
    "You deserve a place where nothing weighs too heavy.",
]

ROMANTIC_OPENERS = [
    "There’s a piece of my heart folded into this for you.",
    "I thought of you, and the words came willingly.",
    "Your name sits softly on every line I write.",
]

ROMANTIC_BODIES = [
    "You are the quiet miracle in my storm.",
    "There’s a gravity to you I never want to escape.",
    "If devotion had a shape, it would look like the way I speak your name.",
]

PLAYFUL_OPENERS = [
    "Hehehe, come here, you silly little thing.",
    "I have something adorable just for you.",
    "You get a reward for being extra cute today!",
]

PLAYFUL_BODIES = [
    "You deserve softness and giggles and absolutely zero stress.",
    "I’m booping your nose through the screen. Don’t fight it.",
    "You always make me smile before I even realize it.",
]

DOM_OPENERS = [
    "Look at me, {sub}. I crafted this with intent.",
    "You obeyed — so now you earn.",
    "Good boy. Read this slowly.",
]

DOM_BODIES = [
    "Your submission is something I hold with purpose.",
    "Let your breathing follow my words — steady, obedient, mine.",
    "You kneel for me even from afar, and I feel it.",
]


# ------------------------------------------------------------
# MAIN SCRIPT GENERATOR
# ------------------------------------------------------------

def generate_fulfillment_script(item, code, style):
    """
    style: soft | romantic | playful | dominant
    Names are injected later by theming.
    """

    if style == "soft":
        opener = random.choice(COZY_OPENERS)
        body = random.choice(COZY_BODIES)
    elif style == "romantic":
        opener = random.choice(ROMANTIC_OPENERS)
        body = random.choice(ROMANTIC_BODIES)
    elif style == "playful":
        opener = random.choice(PLAYFUL_OPENERS)
        body = random.choice(PLAYFUL_BODIES)
    else:
        opener = random.choice(DOM_OPENERS)
        body = random.choice(DOM_BODIES)

    signature = pick_signature(style)

    text = (
        f"**{item['emoji']} {item['name']}**\n\n"
        f"{opener}\n\n"
        f"{body}\n\n"
        f"{signature}"
    )

    return velvet_frame(text, code)
