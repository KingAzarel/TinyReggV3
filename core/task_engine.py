# core/task_engine.py

import random
from datetime import date
from core import task_pools
from core.db import get_connection

MAX_DAILY_TASKS = 10


# ─────────────────────────────────────────────
# DATE (single source of truth)
# ─────────────────────────────────────────────

def _today() -> str:
    return date.today().isoformat()


# ─────────────────────────────────────────────
# INTERNAL HELPERS
# ─────────────────────────────────────────────

def _weighted_choice(weighted_items):
    total = sum(w for _, w in weighted_items)
    roll = random.uniform(0, total)
    upto = 0
    for key, weight in weighted_items:
        if upto + weight >= roll:
            return key
        upto += weight
    return weighted_items[-1][0]


def _get_profile(profile_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM profiles WHERE profile_id = ?",
        (profile_id,),
    )
    row = cur.fetchone()
    conn.close()
    return row


def _get_existing_task_keys(profile_id):
    today = _today()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT task_key
        FROM assigned_tasks
        WHERE profile_id = ?
          AND date = ?
        """,
        (profile_id, today),
    )
    rows = cur.fetchall()
    conn.close()
    return {r["task_key"] for r in rows}


def _explicit_already_assigned(profile_id) -> bool:
    today = _today()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT 1
        FROM assigned_tasks
        WHERE profile_id = ?
          AND category = 'explicit'
          AND date = ?
        LIMIT 1
        """,
        (profile_id, today),
    )
    exists = cur.fetchone() is not None
    conn.close()
    return exists


def _insert_tasks(profile_id, tasks):
    today = _today()
    conn = get_connection()
    cur = conn.cursor()

    for task in tasks:
        cur.execute(
            """
            INSERT OR IGNORE INTO assigned_tasks
            (profile_id, date, task_key, category, is_required, hidden_until_complete)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                profile_id,
                today,
                task["key"],
                task["category"],
                task["required"],
                task["hidden"],
            ),
        )

    conn.commit()
    conn.close()


def _remove_uncompleted_unsafe(profile_id, allowed_categories):
    if not allowed_categories:
        return

    today = _today()
    placeholders = ",".join("?" * len(allowed_categories))

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        f"""
        DELETE FROM assigned_tasks
        WHERE profile_id = ?
          AND date = ?
          AND task_key NOT IN (
              SELECT task_key
              FROM task_history
              WHERE profile_id = ?
                AND completed = 1
                AND date = ?
          )
          AND category NOT IN ({placeholders})
        """,
        (profile_id, today, profile_id, today, *allowed_categories),
    )

    conn.commit()
    conn.close()


# ─────────────────────────────────────────────
# DAILY GENERATION
# ─────────────────────────────────────────────

def generate_daily_tasks(profile_id):
    profile = _get_profile(profile_id)
    if not profile:
        return []

    age = profile["age_context"]
    intimacy_ok = bool(profile["intimacy_opt_in"])
    kink_ok = bool(profile["kink_opt_in"])
    explicit_ok = bool(profile["explicit_opt_in"])

    existing = _get_existing_task_keys(profile_id)
    tasks = []

    # Required tasks
    for t in task_pools.get_required_tasks():
        if t["key"] not in existing:
            tasks.append(t)

    remaining = MAX_DAILY_TASKS - len(existing) - len(tasks)
    if remaining <= 0:
        _insert_tasks(profile_id, tasks)
        return tasks

    explicit_used = _explicit_already_assigned(profile_id)

    if age in ("cloudy", "regressive"):
        weighted = [
            ("basic", 35),
            ("fun", 30),
            ("regressive", 25),
            ("small_clean", 10),
        ]
    else:
        weighted = [
            ("basic", 25),
            ("fun", 20),
            ("small_clean", 20),
            ("medium_clean", 15),
            ("heavy_clean", 5),
        ]
        if intimacy_ok:
            weighted.append(("intimacy", 10))
        if kink_ok:
            weighted.append(("kink", 7))

    while remaining > 0:
        pool = _weighted_choice(weighted)

        if (
            age == "adult"
            and explicit_ok
            and not explicit_used
            and random.random() <= 0.18
        ):
            picked = task_pools.get_explicit_tasks()
            explicit_used = True
        else:
            picker = {
                "basic": task_pools.get_basic_care,
                "fun": task_pools.get_fun_tasks,
                "regressive": task_pools.get_regressive_tasks,
                "small_clean": task_pools.get_small_cleaning,
                "medium_clean": task_pools.get_medium_cleaning,
                "heavy_clean": task_pools.get_heavy_cleaning,
                "intimacy": task_pools.get_intimacy_tasks,
                "kink": task_pools.get_kink_tasks,
            }.get(pool)

            if not picker:
                break

            picked = picker()

        for t in picked:
            if t["key"] not in existing:
                tasks.append(t)
                remaining -= 1
                if remaining <= 0:
                    break

    _insert_tasks(profile_id, tasks)
    return tasks


# ─────────────────────────────────────────────
# PRESENCE CHANGE HANDLER
# ─────────────────────────────────────────────

def reassess_tasks_for_profile(profile_id):
    profile = _get_profile(profile_id)
    if not profile:
        return

    age = profile["age_context"]
    allowed = {"required", "basic", "fun", "small_clean"}

    if age in ("cloudy", "regressive"):
        allowed.add("regressive")

    if age == "adult":
        allowed |= {"medium_clean", "heavy_clean"}
        if profile["intimacy_opt_in"]:
            allowed.add("intimacy")
        if profile["kink_opt_in"]:
            allowed.add("kink")
        if profile["explicit_opt_in"]:
            allowed.add("explicit")

    _remove_uncompleted_unsafe(profile_id, allowed)
    generate_daily_tasks(profile_id)


# ─────────────────────────────────────────────
# USER-REQUESTED TASKS
# ─────────────────────────────────────────────

def request_tasks_from_pool(profile_id, pool, count=1):
    profile = _get_profile(profile_id)
    if not profile:
        return []

    age = profile["age_context"]
    tasks = []

    for _ in range(count):
        if pool == "basic":
            tasks += task_pools.get_basic_care()
        elif pool == "fun":
            tasks += task_pools.get_fun_tasks()
        elif pool == "regressive" and age in ("regressive", "cloudy"):
            tasks += task_pools.get_regressive_tasks()
        elif pool == "small_clean":
            tasks += task_pools.get_small_cleaning()
        elif pool == "medium_clean" and age == "adult":
            tasks += task_pools.get_medium_cleaning()
        elif pool == "heavy_clean" and age == "adult":
            tasks += task_pools.get_heavy_cleaning()
        elif pool == "intimacy" and age == "adult" and profile["intimacy_opt_in"]:
            tasks += task_pools.get_intimacy_tasks()
        elif pool == "kink" and age == "adult" and profile["kink_opt_in"]:
            tasks += task_pools.get_kink_tasks()
        elif pool == "explicit" and age == "adult" and profile["explicit_opt_in"]:
            if not _explicit_already_assigned(profile_id):
                tasks += task_pools.get_explicit_tasks()

    _insert_tasks(profile_id, tasks)
    return tasks


# ─────────────────────────────────────────────
# TASK ACCESS + COMPLETION
# ─────────────────────────────────────────────

def get_tasks_for_profile(profile_id: int, date_str: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT *
        FROM assigned_tasks
        WHERE profile_id = ?
          AND date = ?
        """,
        (profile_id, date_str),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def complete_task_for_profile(profile_id: int, task_key: str):
    today = _today()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT OR REPLACE INTO task_history
        (profile_id, date, task_key, completed)
        VALUES (?, ?, ?, 1)
        """,
        (profile_id, today, task_key),
    )

    conn.commit()
    conn.close()
