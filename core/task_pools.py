import random

#############################################
# REQUIRED / DAILY ANCHORS
#############################################

DAILY_REQUIRED = [
    ("eat_meal", "🍽️ Eat a meal"),
    ("drink_water", "💧 Drink 1 cup of water"),
    ("work_school", "📘 Do school or work tasks"),
    ("fun_activity", "🎉 Do one fun activity"),
    ("brush_teeth", "🪥 Brush your teeth"),
]

#############################################
# BASIC CARE — ALWAYS AVAILABLE
#############################################

BASIC_CARE = {
    "lip_balm": "💄 Apply lip balm",
    "wash_hands": "🫧 Wash your hands",
    "brush_hair": "🌸 Brush your hair gently",
    "moisturize": "💧 Moisturize your face or hands",
    "stretch": "🧍 Stretch your body gently",
}

#############################################
# FUN / LIGHT TASKS — MOOD LIFTING
#############################################

FUN_TASKS = {
    "music_vibe": "🎧 Play a song you like and vibe for a minute",
    "take_photo": "📷 Take a photo of something comforting",
    "draw_doodle": "✏️ Doodle anything at all",
    "look_outside": "🌤️ Look outside and notice one thing",
    "watch_clip": "📺 Watch a short comforting video",
}

#############################################
# CLEANING — SMALL WINS (LOW SPOONS)
#############################################

SMALL_CLEANING = {
    "put_away_items": "🧺 Put a few items back where they belong",
    "clear_bottles": "🧴 Gather a few empty bottles or cups",
    "small_trash": "🗑️ Throw away a small handful of trash",
    "wipe_surface": "🧻 Wipe one small surface",
    "reset_pillow": "🛏️ Straighten your pillow or blanket",
}

#############################################
# CLEANING — MEDIUM TASKS
#############################################

MEDIUM_CLEANING = {
    "desk_reset": "🖥️ Clear and reset your desk",
    "nightstand": "🛏️ Clean up your nightstand",
    "clothes_pile": "👕 Put away a small pile of clothes",
    "room_trash": "🗑️ Pick up trash in one area of the room",
    "dishes": "🍽️ Load or unload the dishwasher",
}

#############################################
# CLEANING — HEAVY TASKS (HIGH ENERGY)
#############################################

HEAVY_CLEANING = {
    "laundry_wash": "🧺 Wash a load of laundry",
    "laundry_fold": "👕 Fold and put away laundry",
    "sweep_floor": "🧹 Sweep or vacuum a floor",
    "mop_floor": "🧼 Mop a floor",
    "deep_clean": "🧽 Deep clean a surface (desk, table, counter)",
}

#############################################
# REGRESSIVE TASKS — SOFT & SAFE
#############################################

REGRESSIVE_TASKS = {
    "hug_stuffie": "🧸 Hug a stuffie or something soft",
    "color_animals": "🎨 Color or doodle some animals",
    "bedtime_story": "📖 Pick out a bedtime story or cozy book",
    "cozy_show": "🐰 Watch a gentle or cartoon show",
    "blanket_nest": "🛌 Get comfy under a blanket",
    "gentle_music": "🎶 Listen to soft or sleepy music",
}

#############################################
# INTIMACY / KINK / EXPLICIT (RAW TEMPLATES)
#############################################

INTIMACY_TASKS = [
    "Send me a soft selfie that makes me feel like I’m right there with you, {sub}.",
    "Tell me one moment today when you wished I was beside you, {sub}.",
    "Send me a picture of your current vibe (bed, desk, lighting).",
    "Tell me how your body feels right now — tired, warm, restless, craving?",
    "Send a cozy outfit or blanket photo you want me to imagine you in, {sub}.",
    "Tell me something you'd want me to whisper to you if I were next to your ear.",
    "Send me a photo of something you touched today that you wish I had touched instead.",
    "Give me one honest line about what you’re feeling right now — no mask, {sub}.",
]

KINK_LEVEL_1 = [
    "Send {dom} a ‘Yes, {dom}’ message in the tone you'd use if I were sitting beside you.",
    "Take a photo from your bed or chair showing how you’d sit when waiting for my instructions, {sub}.",
    "Tell {dom} one craving you felt today — emotional or physical.",
    "Hold your posture the way you imagine {dom} likes it and send a photo of your silhouette.",
    "Send me a picture of your hand placed where you want guidance, {sub}.",
]

KINK_LEVEL_2 = [
    "Take a kneeling posture and send {dom} a photo of your position.",
    "Send a photo showing your neck or collarbone the way you'd offer it.",
    "Begin a message with: 'I obey because…' and finish it honestly, {sub}.",
    "Send {dom} a picture of your legs or thighs arranged invitingly.",
    "Whisper 'Yes, {dom}' into a voice note — the tone is the task.",
]

KINK_LEVEL_3 = [
    "Take the posture you'd use if you were waiting at {dom}'s feet.",
    "Send a voice note whispering what you think your purpose is right now.",
    "Send {dom} a picture of your thighs or hips in a way that silently says 'use me'.",
    "Write one sentence describing what you'd let {dom} take from you tonight.",
    "Send a photo with your hand where you'd want {dom}'s hand if he were there.",
]

EXPLICIT_TASKS = [
    "Put your toy on standby and tell {dom} when you're ready.",
    "Place your toy against your body (PG-13 framing) and send a setup photo.",
    "Get into the position you'd take if {dom} controlled the toy from behind.",
    "Turn the toy on its lowest setting and describe how your body reacts.",
    "Tell {dom} which pattern you'd want first — steady, pulse, tease.",
]

#############################################
# NORMALIZATION
#############################################

def _task(key, text, category, required=False):
    return {
        "key": key,
        "text": text,
        "category": category,
        "required": 1 if required else 0,
        "hidden": 1,
    }

#############################################
# PUBLIC API — ENGINE PICKS FROM HERE
#############################################

def get_required_tasks():
    return [_task(k, t, "required", True) for k, t in DAILY_REQUIRED]


def get_basic_care():
    k, t = random.choice(list(BASIC_CARE.items()))
    return [_task(k, t, "core")]


def get_fun_tasks():
    k, t = random.choice(list(FUN_TASKS.items()))
    return [_task(k, t, "fun")]


def get_small_cleaning():
    k, t = random.choice(list(SMALL_CLEANING.items()))
    return [_task(k, t, "core")]


def get_medium_cleaning():
    k, t = random.choice(list(MEDIUM_CLEANING.items()))
    return [_task(k, t, "core")]


def get_heavy_cleaning():
    k, t = random.choice(list(HEAVY_CLEANING.items()))
    return [_task(k, t, "core")]


def get_regressive_tasks():
    k, t = random.choice(list(REGRESSIVE_TASKS.items()))
    return [_task(k, t, "regressive")]


def get_intimacy_tasks():
    pick = random.choice(INTIMACY_TASKS)
    return [_task(f"intimacy_{abs(hash(pick))}", pick, "intimacy")]


def get_kink_tasks(level=1):
    pool = {
        1: KINK_LEVEL_1,
        2: KINK_LEVEL_2,
        3: KINK_LEVEL_3,
    }.get(level, KINK_LEVEL_1)

    pick = random.choice(pool)
    return [_task(f"kink_{abs(hash(pick))}", pick, "kink")]


def get_explicit_tasks():
    pick = random.choice(EXPLICIT_TASKS)
    return [_task(f"explicit_{abs(hash(pick))}", pick, "explicit")]


def get_safe_required_replacement():
    k, t = random.choice(DAILY_REQUIRED)
    return _task(k, t, "required", True)
