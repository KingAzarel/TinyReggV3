import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "tinyregg.db")


# ─────────────────────────────────────────────────────────────
# Connection helper
# ─────────────────────────────────────────────────────────────

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ─────────────────────────────────────────────────────────────
# Initialization
# ─────────────────────────────────────────────────────────────

def initialize_db():
    conn = get_connection()
    cur = conn.cursor()

    # ─────────────────────────────────────────────────────────
    # USERS (account-level only)
    # ─────────────────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        tokens INTEGER DEFAULT 0,
        boss_tokens INTEGER DEFAULT 0,
        theme TEXT DEFAULT 'purple_doll',
        has_started INTEGER NOT NULL DEFAULT 0
    )
    """)

    # ─────────────────────────────────────────────────────────
    # PROFILES (presence / context)
    # ─────────────────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS profiles (
        profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        name TEXT NOT NULL,

        age_context TEXT NOT NULL
            CHECK (age_context IN ('adult', 'regressive', 'cloudy'))
            DEFAULT 'cloudy',

        intimacy_opt_in INTEGER NOT NULL DEFAULT 0,
        kink_opt_in INTEGER NOT NULL DEFAULT 0,
        explicit_opt_in INTEGER NOT NULL DEFAULT 0,

        gender TEXT,
        pronouns TEXT,
        nickname TEXT,

        is_active INTEGER NOT NULL DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (user_id)
            REFERENCES users(user_id)
            ON DELETE CASCADE
    )
    """)

    # ─────────────────────────────────────────────────────────
    # PROFILE SWITCH LOG
    # ─────────────────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS profile_switch_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        profile_id INTEGER NOT NULL,
        switched_at TEXT DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (profile_id)
            REFERENCES profiles(profile_id)
            ON DELETE CASCADE
    )
    """)

    # ─────────────────────────────────────────────────────────
    # TASK ASSIGNMENT
    # ─────────────────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS assigned_tasks (
        profile_id INTEGER,
        date TEXT,
        task_key TEXT,
        category TEXT,
        is_required INTEGER DEFAULT 0,
        hidden_until_complete INTEGER DEFAULT 1,

        PRIMARY KEY (profile_id, date, task_key),
        FOREIGN KEY (profile_id)
            REFERENCES profiles(profile_id)
            ON DELETE CASCADE
    )
    """)

    # ─────────────────────────────────────────────────────────
    # TASK HISTORY
    # ─────────────────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS task_history (
        profile_id INTEGER,
        date TEXT,
        task_key TEXT,
        completed INTEGER DEFAULT 0,
        points_awarded INTEGER DEFAULT 0,

        PRIMARY KEY (profile_id, date, task_key),
        FOREIGN KEY (profile_id)
            REFERENCES profiles(profile_id)
            ON DELETE CASCADE
    )
    """)

    # ─────────────────────────────────────────────────────────
    # STREAKS
    # ─────────────────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS profile_streaks (
        profile_id INTEGER PRIMARY KEY,
        required_streak INTEGER DEFAULT 0,
        intimacy_streak INTEGER DEFAULT 0,
        kink_streak INTEGER DEFAULT 0,
        explicit_streak INTEGER DEFAULT 0,
        regression_streak INTEGER DEFAULT 0,

        last_required_day TEXT,
        last_intimacy_day TEXT,
        last_kink_day TEXT,
        last_explicit_day TEXT,

        FOREIGN KEY (profile_id)
            REFERENCES profiles(profile_id)
            ON DELETE CASCADE
    )
    """)

    # ─────────────────────────────────────────────────────────
    # BOSSES
    # ─────────────────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS boss_state (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS boss_progress (
        profile_id INTEGER,
        requirement_key TEXT,
        count INTEGER DEFAULT 0,

        PRIMARY KEY (profile_id, requirement_key),
        FOREIGN KEY (profile_id)
            REFERENCES profiles(profile_id)
            ON DELETE CASCADE
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS boss_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profile_id INTEGER,
        boss_name TEXT,
        defeated_at TEXT DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (profile_id)
            REFERENCES profiles(profile_id)
            ON DELETE CASCADE
    )
    """)

    # ─────────────────────────────────────────────────────────
    # WEEKLY SUMMARY
    # ─────────────────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS weekly (
        profile_id INTEGER,
        week INTEGER,
        tasks_completed INTEGER DEFAULT 0,
        bosses_defeated INTEGER DEFAULT 0,
        bonus_awarded INTEGER DEFAULT 0,

        PRIMARY KEY (profile_id, week),
        FOREIGN KEY (profile_id)
            REFERENCES profiles(profile_id)
            ON DELETE CASCADE
    )
    """)

    # ─────────────────────────────────────────────────────────
    # TITLES & BADGES
    # ─────────────────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS titles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profile_id INTEGER,
        title TEXT,
        earned_at TEXT DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (profile_id)
            REFERENCES profiles(profile_id)
            ON DELETE CASCADE
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS badges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profile_id INTEGER,
        badge TEXT,
        earned_at TEXT DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (profile_id)
            REFERENCES profiles(profile_id)
            ON DELETE CASCADE
    )
    """)

    # ─────────────────────────────────────────────────────────
    # SHOP / REDEMPTIONS
    # ─────────────────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS purchases (
        profile_id INTEGER,
        item_key TEXT,
        timestamp TEXT,

        FOREIGN KEY (profile_id)
            REFERENCES profiles(profile_id)
            ON DELETE CASCADE
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS redemption_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profile_id INTEGER NOT NULL,
        item_id TEXT NOT NULL,
        reward_code TEXT NOT NULL,

        delivered INTEGER DEFAULT 0,
        delivered_at TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (profile_id)
            REFERENCES profiles(profile_id)
            ON DELETE CASCADE
    )
    """)

    # ─────────────────────────────────────────────────────────
    # CONSENT LOG (audit safety)
    # ─────────────────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS consent_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
        category TEXT,
        new_value INTEGER,

        FOREIGN KEY (user_id)
            REFERENCES users(user_id)
    )
    """)

    # ─────────────────────────────────────────────────────────
    # REMINDERS
    # ─────────────────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS reminders (
        reminder_id INTEGER PRIMARY KEY AUTOINCREMENT,
        profile_id INTEGER,
        hour INTEGER,
        minute INTEGER,
        text TEXT,
        is_recurring INTEGER DEFAULT 0,

        FOREIGN KEY (profile_id)
            REFERENCES profiles(profile_id)
            ON DELETE CASCADE
    )
    """)

    # ─────────────────────────────────────────────────────────
    # MILESTONES
    # ─────────────────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS milestones (
        milestone_id INTEGER PRIMARY KEY AUTOINCREMENT,
        profile_id INTEGER,
        name TEXT,
        datetime TEXT,
        repeat TEXT,

        FOREIGN KEY (profile_id)
            REFERENCES profiles(profile_id)
            ON DELETE CASCADE
    )
    """)

    # ─────────────────────────────────────────────────────────
    # MOOD LOG
    # ─────────────────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS mood_log (
        profile_id INTEGER,
        timestamp TEXT,
        mood TEXT,

        FOREIGN KEY (profile_id)
            REFERENCES profiles(profile_id)
            ON DELETE CASCADE
    )
    """)

    # ─────────────────────────────────────────────────────────
    # SYSTEM STATE
    # ─────────────────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS task_reset_state (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        last_reset_date TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS message_queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profile_id INTEGER,
        content TEXT,
        embed BLOB,
        timestamp TEXT,
        sent INTEGER DEFAULT 0,

        FOREIGN KEY (profile_id)
            REFERENCES profiles(profile_id)
            ON DELETE CASCADE
    )
    """)

    conn.commit()
    conn.close()
