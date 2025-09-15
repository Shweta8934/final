# create current streak and week topic suggest
import sqlite3
import json
from datetime import datetime, timedelta

DB_NAME = "student.db"


def init_db():
    """Initialize main student database with enhanced tables"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Basic interactions table
    c.execute(
        """
    CREATE TABLE IF NOT EXISTS interactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student TEXT NOT NULL,
        subject TEXT,
        grade TEXT,
        question TEXT,
        answer TEXT,
        resources TEXT,
        feedback INTEGER DEFAULT 0,
        feedback_comment TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """
    )

    # Student progress table
    c.execute(
        """
    CREATE TABLE IF NOT EXISTS student_progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_name TEXT,
        subject TEXT,
        topic TEXT,
        difficulty_level INTEGER,
        mastery_score REAL,
        struggle_areas TEXT,
        learning_style TEXT,
        last_session TIMESTAMP,
        total_sessions INTEGER DEFAULT 0,
        success_rate REAL DEFAULT 0
    )
    """
    )

    # Learning patterns / adaptive learning
    c.execute(
        """
    CREATE TABLE IF NOT EXISTS learning_patterns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_name TEXT,
        preferred_explanation_type TEXT,
        response_time_average REAL,
        common_mistakes TEXT,
        motivation_triggers TEXT,
        engagement_level INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    )

    # Gamification (XP, streaks, badges, daily interactions)
    c.execute(
        """
    CREATE TABLE IF NOT EXISTS gamification (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_name TEXT,
        xp_points INTEGER DEFAULT 0,
        streak INTEGER DEFAULT 0,
        badges TEXT,
        last_activity TIMESTAMP,
        daily_interactions INTEGER DEFAULT 0
    )
    """
    )

    conn.commit()
    conn.close()


# ---------------------- Interactions ----------------------


def log_interaction(student_name, grade, subject, question, answer, resources=""):
    conn = sqlite3.connect("student.db")
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO interactions (student, grade, subject, question, answer, resources, created_at)
        VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
    """,
        (student_name, grade, subject, question, answer, resources),
    )
    conn.commit()
    inter_id = c.lastrowid
    conn.close()
    return inter_id


def get_recent_interactions(student_name, grade, limit=10):
    conn = sqlite3.connect("student.db")
    c = conn.cursor()
    c.execute(
        """
        SELECT id, question, answer, resources, feedback, feedback_comment, created_at
        FROM interactions
        WHERE student = ? AND grade = ?
        ORDER BY created_at DESC
        LIMIT ?
    """,
        (student_name, grade, limit),
    )
    rows = c.fetchall()
    conn.close()
    return rows


def set_feedback(inter_id, feedback_val, comment):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        """
        UPDATE interactions
        SET feedback = ?, feedback_comment = ?
        WHERE id = ?
    """,
        (feedback_val, comment, inter_id),
    )
    conn.commit()
    conn.close()


# ---------------------- Progress ----------------------


def update_student_progress(
    student_name,
    subject,
    topic,
    difficulty,
    mastery_score,
    struggle_areas,
    learning_style,
):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        """
        SELECT id, total_sessions FROM student_progress
        WHERE student_name = ? AND subject = ? AND topic = ?
    """,
        (student_name, subject, topic),
    )
    row = c.fetchone()
    if row:
        pid, total_sessions = row
        c.execute(
            """
            UPDATE student_progress
            SET difficulty_level=?, mastery_score=?, struggle_areas=?, learning_style=?, last_session=?, total_sessions=?
            WHERE id=?
        """,
            (
                difficulty,
                mastery_score,
                struggle_areas,
                learning_style,
                datetime.now(),
                total_sessions + 1,
                pid,
            ),
        )
    else:
        c.execute(
            """
            INSERT INTO student_progress 
            (student_name, subject, topic, difficulty_level, mastery_score, struggle_areas, learning_style, last_session, total_sessions)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                student_name,
                subject,
                topic,
                difficulty,
                mastery_score,
                struggle_areas,
                learning_style,
                datetime.now(),
                1,
            ),
        )
    conn.commit()
    conn.close()


def get_student_progress(student_name, subject):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        """
        SELECT * FROM student_progress
        WHERE student_name=? AND subject=?
        ORDER BY last_session DESC
    """,
        (student_name, subject),
    )
    rows = c.fetchall()
    conn.close()
    return rows


# ---------------------- Gamification ----------------------


def parse_date(date_str):
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def update_gamification(student_name, xp=0, badge=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        """
        SELECT id, xp_points, streak, badges, last_activity, daily_interactions
        FROM gamification
        WHERE student_name=?
    """,
        (student_name,),
    )
    row = c.fetchone()

    today = datetime.now().date()

    if row:
        gid, curr_xp, curr_streak, badges_json, last_activity, daily_interactions = row
        new_xp = curr_xp + xp

        last_date = parse_date(last_activity) if last_activity else None
        if last_date:
            if last_date.date() == today:
                new_streak = curr_streak
                daily_interactions += 1
            elif last_date.date() == today - timedelta(days=1):
                new_streak = curr_streak + 1
                daily_interactions = 1
            else:
                new_streak = 1
                daily_interactions = 1
        else:
            new_streak = 1
            daily_interactions = 1

        badge_list = json.loads(badges_json) if badges_json else []
        if badge and badge not in badge_list:
            badge_list.append(badge)

        c.execute(
            """
            UPDATE gamification
            SET xp_points=?, streak=?, badges=?, last_activity=?, daily_interactions=?
            WHERE id=?
        """,
            (
                new_xp,
                new_streak,
                json.dumps(badge_list),
                datetime.now(),
                daily_interactions,
                gid,
            ),
        )
    else:
        badges_list = [badge] if badge else []
        c.execute(
            """
            INSERT INTO gamification
            (student_name, xp_points, streak, badges, last_activity, daily_interactions)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (student_name, xp, 1, json.dumps(badges_list), datetime.now(), 1),
        )

    conn.commit()
    conn.close()


def get_gamification(student_name):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        """
        SELECT xp_points, streak, badges FROM gamification
        WHERE student_name=?
    """,
        (student_name,),
    )
    row = c.fetchone()
    conn.close()
    if row:
        xp, streak, badges = row
        badge_list = json.loads(badges) if badges else []
        return {
            "xp": xp,
            "streak": streak,
            "badges": badge_list,
        }
    else:
        return {"xp": 0, "streak": 0, "badges": []}


# Auto-init DB
init_db()
