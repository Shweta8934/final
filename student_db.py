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
    c.execute("""
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
    """)

    # Student progress table
    c.execute("""
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
    """)

    # Learning patterns / adaptive learning
    c.execute("""
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
    """)

    # Gamification (XP, streaks, badges, daily interactions)
    c.execute("""
    CREATE TABLE IF NOT EXISTS gamification (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_name TEXT,
        xp_points INTEGER DEFAULT 0,
        streak INTEGER DEFAULT 0,
        badges TEXT,
        last_activity TIMESTAMP,
        daily_interactions INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()


# ---------------------- Interactions ----------------------

def log_interaction(student_name, grade, subject, question, answer, resources=""):
    conn = sqlite3.connect("student.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO interactions (student, grade, subject, question, answer, resources, created_at)
        VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
    """, (student_name, grade, subject, question, answer, resources))
    conn.commit()
    inter_id = c.lastrowid
    conn.close()
    return inter_id


def get_recent_interactions(student_name, grade, limit=10):
    conn = sqlite3.connect("student.db")
    c = conn.cursor()
    c.execute("""
        SELECT id, question, answer, resources, feedback, feedback_comment, created_at
        FROM interactions
        WHERE student = ? AND grade = ?
        ORDER BY created_at DESC
        LIMIT ?
    """, (student_name, grade, limit))
    rows = c.fetchall()
    conn.close()
    return rows


def set_feedback(inter_id, feedback_val, comment):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        UPDATE interactions
        SET feedback = ?, feedback_comment = ?
        WHERE id = ?
    """, (feedback_val, comment, inter_id))
    conn.commit()
    conn.close()


# ---------------------- Progress ----------------------

def update_student_progress(student_name, subject, topic, difficulty, mastery_score, struggle_areas, learning_style):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        SELECT id, total_sessions FROM student_progress
        WHERE student_name = ? AND subject = ? AND topic = ?
    """, (student_name, subject, topic))
    row = c.fetchone()
    if row:
        pid, total_sessions = row
        c.execute("""
            UPDATE student_progress
            SET difficulty_level=?, mastery_score=?, struggle_areas=?, learning_style=?, last_session=?, total_sessions=?
            WHERE id=?
        """, (difficulty, mastery_score, struggle_areas, learning_style, datetime.now(), total_sessions+1, pid))
    else:
        c.execute("""
            INSERT INTO student_progress 
            (student_name, subject, topic, difficulty_level, mastery_score, struggle_areas, learning_style, last_session, total_sessions)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (student_name, subject, topic, difficulty, mastery_score, struggle_areas, learning_style, datetime.now(), 1))
    conn.commit()
    conn.close()


def get_student_progress(student_name, subject):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        SELECT * FROM student_progress
        WHERE student_name=? AND subject=?
        ORDER BY last_session DESC
    """, (student_name, subject))
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
    c.execute("""
        SELECT id, xp_points, streak, badges, last_activity, daily_interactions
        FROM gamification
        WHERE student_name=?
    """, (student_name,))
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

        c.execute("""
            UPDATE gamification
            SET xp_points=?, streak=?, badges=?, last_activity=?, daily_interactions=?
            WHERE id=?
        """, (new_xp, new_streak, json.dumps(badge_list), datetime.now(), daily_interactions, gid))
    else:
        badges_list = [badge] if badge else []
        c.execute("""
            INSERT INTO gamification
            (student_name, xp_points, streak, badges, last_activity, daily_interactions)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (student_name, xp, 1, json.dumps(badges_list), datetime.now(), 1))
    
    conn.commit()
    conn.close()


def get_gamification(student_name):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        SELECT xp_points, streak, badges FROM gamification
        WHERE student_name=?
    """, (student_name,))
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




# # create current streak and week topic suggest
# import sqlite3
# import json
# from datetime import datetime, timedelta

# DB_NAME = "student.db"

# def init_db():
#     """Initialize main student database with enhanced tables"""
#     conn = sqlite3.connect(DB_NAME)
#     c = conn.cursor()

#     # Basic interactions table
#     c.execute("""
#     CREATE TABLE IF NOT EXISTS interactions (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         student TEXT NOT NULL,
#         subject TEXT,
#               grade TEXT,
#         question TEXT,
#         answer TEXT,
#         resources TEXT,
#         feedback INTEGER DEFAULT 0,
#         feedback_comment TEXT,
#         created_at TEXT DEFAULT CURRENT_TIMESTAMP
#     )
#     """)

#     # Student progress table
#     c.execute("""
#     CREATE TABLE IF NOT EXISTS student_progress (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         student_name TEXT,
#         subject TEXT,
#         topic TEXT,
#         difficulty_level INTEGER,
#         mastery_score REAL,
#         struggle_areas TEXT,
#         learning_style TEXT,
#         last_session TIMESTAMP,
#         total_sessions INTEGER DEFAULT 0,
#         success_rate REAL DEFAULT 0
#     )
#     """)

#     # Learning patterns / adaptive learning
#     c.execute("""
#     CREATE TABLE IF NOT EXISTS learning_patterns (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         student_name TEXT,
#         preferred_explanation_type TEXT,
#         response_time_average REAL,
#         common_mistakes TEXT,
#         motivation_triggers TEXT,
#         engagement_level INTEGER,
#         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#     )
#     """)

#     # Gamification (XP, streaks, badges, daily interactions)
#     c.execute("""
#     CREATE TABLE IF NOT EXISTS gamification (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         student_name TEXT,
#         xp_points INTEGER DEFAULT 0,
#         streak INTEGER DEFAULT 0,
#         badges TEXT,
#         last_activity TIMESTAMP,
#         daily_interactions INTEGER DEFAULT 0
#     )
#     """)

#     conn.commit()
#     conn.close()

# # ---------------------- Interactions ----------------------

# def log_interaction(student_name, grade, subject, question, answer, resources=""):
#     conn = sqlite3.connect("student.db")
#     c = conn.cursor()
#     c.execute("""
#         INSERT INTO interactions (student, grade, subject, question, answer, resources, created_at, updated_at)
#         VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
#     """, (student_name, grade, subject, question, answer, resources))
#     conn.commit()
#     inter_id = c.lastrowid
#     conn.close()
#     return inter_id


# # def get_recent_interactions(student, limit=10):
# #     conn = sqlite3.connect(DB_NAME)
# #     c = conn.cursor()
# #     c.execute("""
# #         SELECT id, question, answer, resources, feedback, feedback_comment, created_at
# #         FROM interactions
# #         WHERE student = ?
# #         ORDER BY created_at DESC
# #         LIMIT ?
# #     """, (student, limit))
# #     rows = c.fetchall()
# #     conn.close()
# #     return rows

# def set_feedback(inter_id, feedback_val, comment):
#     conn = sqlite3.connect(DB_NAME)
#     c = conn.cursor()
#     c.execute("""
#         UPDATE interactions
#         SET feedback = ?, feedback_comment = ?
#         WHERE id = ?
#     """, (feedback_val, comment, inter_id))
#     conn.commit()
#     conn.close()

# # ---------------------- Progress ----------------------

# def update_student_progress(student_name, subject, topic, difficulty, mastery_score, struggle_areas, learning_style):
#     conn = sqlite3.connect(DB_NAME)
#     c = conn.cursor()
#     c.execute("""
#         SELECT id, total_sessions FROM student_progress
#         WHERE student_name = ? AND subject = ? AND topic = ?
#     """, (student_name, subject, topic))
#     row = c.fetchone()
#     if row:
#         pid, total_sessions = row
#         c.execute("""
#             UPDATE student_progress
#             SET difficulty_level=?, mastery_score=?, struggle_areas=?, learning_style=?, last_session=?, total_sessions=?
#             WHERE id=?
#         """, (difficulty, mastery_score, struggle_areas, learning_style, datetime.now(), total_sessions+1, pid))
#     else:
#         c.execute("""
#             INSERT INTO student_progress 
#             (student_name, subject, topic, difficulty_level, mastery_score, struggle_areas, learning_style, last_session, total_sessions)
#             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
#         """, (student_name, subject, topic, difficulty, mastery_score, struggle_areas, learning_style, datetime.now(), 1))
#     conn.commit()
#     conn.close()

# # def get_student_progress(student_name, subject):
# #     conn = sqlite3.connect(DB_NAME)
# #     c = conn.cursor()
# #     c.execute("""
# #         SELECT * FROM student_progress
# #         WHERE student_name=? AND subject=?
# #         ORDER BY last_session DESC
# #     """, (student_name, subject))
# #     rows = c.fetchall()
# #     conn.close()
# #     return rows
# # ... existing code ...
# def get_recent_interactions(student_name, grade, limit=10):
#     conn = sqlite3.connect("student.db")
#     c = conn.cursor()
#     c.execute("""
#         SELECT id, question, answer, resources, feedback, feedback_comment, created_at
#         FROM interactions
#         WHERE student = ? AND grade = ?
#         ORDER BY created_at DESC
#         LIMIT ?
#     """, (student_name, grade, limit))
#     rows = c.fetchall()
#     conn.close()
#     return rows



# # ... existing code ...
# def get_student_progress(student_name, subject):
#     conn = sqlite3.connect(DB_NAME)
#     c = conn.cursor()
#     c.execute("""
#         SELECT * FROM student_progress
#         WHERE student_name=? AND subject=?
#         ORDER BY last_session DESC
#     """, (student_name, subject))
#     rows = c.fetchall()
#     conn.close()
#     return rows
# # ... existing code ...
# # ---------------------- Gamification ----------------------

# def parse_date(date_str):
#     """Helper to safely parse SQLite timestamp strings"""
#     if not date_str:
#         return None
#     for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
#         try:
#             return datetime.strptime(date_str, fmt)
#         except ValueError:
#             continue
#     return None
# def update_gamification(student_name, xp=0, badge=None):
#     conn = sqlite3.connect(DB_NAME)
#     c = conn.cursor()
#     c.execute("""
#         SELECT id, xp_points, streak, badges, last_activity, daily_interactions
#         FROM gamification
#         WHERE student_name=?
#     """, (student_name,))
#     row = c.fetchone()
    
#     today = datetime.now().date()
    
#     if row:
#         gid, curr_xp, curr_streak, badges_json, last_activity, daily_interactions = row
#         new_xp = curr_xp + xp

#         last_date = parse_date(last_activity) if last_activity else None
#         if last_date:
#             if last_date.date() == today:
#                 # same day → count only one interaction per log call
#                 new_streak = curr_streak
#                 daily_interactions += 1
#             elif last_date.date() == today - timedelta(days=1):
#                 # streak continues
#                 new_streak = curr_streak + 1
#                 daily_interactions = 1
#             else:
#                 # missed → reset streak
#                 new_streak = 1
#                 daily_interactions = 1
#         else:
#             new_streak = 1
#             daily_interactions = 1

#         badge_list = json.loads(badges_json) if badges_json else []
#         if badge and badge not in badge_list:
#             badge_list.append(badge)

#         # ✅ Include daily_interactions in the UPDATE
#         c.execute("""
#             UPDATE gamification
#             SET xp_points=?, streak=?, badges=?, last_activity=?, daily_interactions=?
#             WHERE id=?
#         """, (new_xp, new_streak, json.dumps(badge_list), datetime.now(), daily_interactions, gid))
#     else:
#         badges_list = [badge] if badge else []
#         c.execute("""
#             INSERT INTO gamification
#             (student_name, xp_points, streak, badges, last_activity, daily_interactions)
#             VALUES (?, ?, ?, ?, ?, ?)
#         """, (student_name, xp, 1, json.dumps(badges_list), datetime.now(), 1))
    
#     conn.commit()
#     conn.close()


# def get_gamification(student_name):
#     conn = sqlite3.connect(DB_NAME)
#     c = conn.cursor()
#     c.execute("""
#         SELECT xp_points, streak, badges FROM gamification
#         WHERE student_name=?
#     """, (student_name,))
#     row = c.fetchone()
#     conn.close()
#     if row:
#         xp, streak, badges = row
#         badge_list = json.loads(badges) if badges else []
#         return {
#             "xp": xp,
#             "streak": streak,
#             "badges": badge_list,
            
#         }
#     else:
#         return {"xp": 0, "streak": 0, "badges": []}

# # Auto-init DB
# init_db()





# # # student_db.py
# # # Enhanced with grade tracking + existing streak/weak topic support

# # import sqlite3
# # import json
# # from datetime import datetime, timedelta

# # DB_NAME = "student.db"

# # def init_db():
# #     """Initialize main student database with enhanced tables"""
# #     conn = sqlite3.connect(DB_NAME)
# #     c = conn.cursor()

# #     # Basic interactions table (now with grade)
# #     c.execute("""
# #     CREATE TABLE IF NOT EXISTS interactions (
# #         id INTEGER PRIMARY KEY AUTOINCREMENT,
# #         student TEXT NOT NULL,
# #         grade TEXT, 
# #         subject TEXT,
# #         question TEXT,
# #         answer TEXT,
# #         resources TEXT,
# #         feedback INTEGER DEFAULT 0,
# #         feedback_comment TEXT,
# #         created_at TEXT DEFAULT CURRENT_TIMESTAMP
# #     )
# #     """)

# #     # Student progress table
# #     c.execute("""
# #     CREATE TABLE IF NOT EXISTS student_progress (
# #         id INTEGER PRIMARY KEY AUTOINCREMENT,
# #         student_name TEXT,
# #         subject TEXT,
# #         topic TEXT,
# #         difficulty_level INTEGER,
# #         mastery_score REAL,
# #         struggle_areas TEXT,
# #         learning_style TEXT,
# #         last_session TIMESTAMP,
# #         total_sessions INTEGER DEFAULT 0,
# #         success_rate REAL DEFAULT 0
# #     )
# #     """)

# #     # Learning patterns / adaptive learning
# #     c.execute("""
# #     CREATE TABLE IF NOT EXISTS learning_patterns (
# #         id INTEGER PRIMARY KEY AUTOINCREMENT,
# #         student_name TEXT,
# #         preferred_explanation_type TEXT,
# #         response_time_average REAL,
# #         common_mistakes TEXT,
# #         motivation_triggers TEXT,
# #         engagement_level INTEGER,
# #         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
# #     )
# #     """)

# #     # Gamification (XP, streaks, badges, daily interactions)
# #     c.execute("""
# #     CREATE TABLE IF NOT EXISTS gamification (
# #         id INTEGER PRIMARY KEY AUTOINCREMENT,
# #         student_name TEXT,
# #         xp_points INTEGER DEFAULT 0,
# #         streak INTEGER DEFAULT 0,
# #         badges TEXT,
# #         last_activity TIMESTAMP,
# #         daily_interactions INTEGER DEFAULT 0
# #     )
# #     """)

# #     conn.commit()
# #     conn.close()

# # # ---------------------- Interactions ----------------------

# # def log_interaction(student, subject, question, answer, resources):
# #     """Log a new student interaction with grade included"""
# #     conn = sqlite3.connect(DB_NAME)
# #     c = conn.cursor()
# #     c.execute("""
# #         INSERT INTO interactions (student,  subject, question, answer, resources)
# #         VALUES (?, ?, ?, ?, ?, ?)
# #     """, (student,  subject, question, answer, resources))
# #     conn.commit()
# #     inter_id = c.lastrowid
# #     conn.close()
# #     return inter_id

# # def get_recent_interactions(student, limit=10):
# #     conn = sqlite3.connect(DB_NAME)
# #     c = conn.cursor()
# #     c.execute("""
# #         SELECT id,  question, answer, resources, feedback, feedback_comment, created_at
# #         FROM interactions
# #         WHERE student = ?
# #         ORDER BY created_at DESC
# #         LIMIT ?
# #     """, (student, limit))
# #     rows = c.fetchall()
# #     conn.close()
# #     return rows

# # def set_feedback(inter_id, feedback_val, comment):
# #     conn = sqlite3.connect(DB_NAME)
# #     c = conn.cursor()
# #     c.execute("""
# #         UPDATE interactions
# #         SET feedback = ?, feedback_comment = ?
# #         WHERE id = ?
# #     """, (feedback_val, comment, inter_id))
# #     conn.commit()
# #     conn.close()

# # def get_grade_wise_stats(student):
# #     """Return grade-wise accuracy and counts for progression tracking"""
# #     conn = sqlite3.connect(DB_NAME)
# #     c = conn.cursor()
# #     c.execute("""
# #         SELECT grade, 
# #                COUNT(*) as total,
# #                SUM(CASE WHEN feedback = 1 THEN 1 ELSE 0 END) as correct,
# #                SUM(CASE WHEN feedback = -1 THEN 1 ELSE 0 END) as wrong
# #         FROM interactions
# #         WHERE student = ?
# #         GROUP BY grade
# #         ORDER BY grade
# #     """, (student,))
# #     rows = c.fetchall()
# #     conn.close()
# #     return rows

# # # ---------------------- Progress ----------------------

# # def update_student_progress(student_name, subject, topic, difficulty, mastery_score, struggle_areas, learning_style):
# #     conn = sqlite3.connect(DB_NAME)
# #     c = conn.cursor()
# #     c.execute("""
# #         SELECT id, total_sessions FROM student_progress
# #         WHERE student_name = ? AND subject = ? AND topic = ?
# #     """, (student_name, subject, topic))
# #     row = c.fetchone()
# #     if row:
# #         pid, total_sessions = row
# #         c.execute("""
# #             UPDATE student_progress
# #             SET difficulty_level=?, mastery_score=?, struggle_areas=?, learning_style=?, last_session=?, total_sessions=?
# #             WHERE id=?
# #         """, (difficulty, mastery_score, struggle_areas, learning_style, datetime.now(), total_sessions+1, pid))
# #     else:
# #         c.execute("""
# #             INSERT INTO student_progress 
# #             (student_name, subject, topic, difficulty_level, mastery_score, struggle_areas, learning_style, last_session, total_sessions)
# #             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
# #         """, (student_name, subject, topic, difficulty, mastery_score, struggle_areas, learning_style, datetime.now(), 1))
# #     conn.commit()
# #     conn.close()

# # def get_student_progress(student_name, subject):
# #     conn = sqlite3.connect(DB_NAME)
# #     c = conn.cursor()
# #     c.execute("""
# #         SELECT * FROM student_progress
# #         WHERE student_name=? AND subject=?
# #         ORDER BY last_session DESC
# #     """, (student_name, subject))
# #     rows = c.fetchall()
# #     conn.close()
# #     return rows

# # # ---------------------- Gamification ----------------------

# # def parse_date(date_str):
# #     """Helper to safely parse SQLite timestamp strings"""
# #     if not date_str:
# #         return None
# #     for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
# #         try:
# #             return datetime.strptime(date_str, fmt)
# #         except ValueError:
# #             continue
# #     return None

# # def update_gamification(student_name, xp=0, badge=None):
# #     conn = sqlite3.connect(DB_NAME)
# #     c = conn.cursor()
# #     c.execute("""
# #         SELECT id, xp_points, streak, badges, last_activity, daily_interactions
# #         FROM gamification
# #         WHERE student_name=?
# #     """, (student_name,))
# #     row = c.fetchone()
    
# #     today = datetime.now().date()
    
# #     if row:
# #         gid, curr_xp, curr_streak, badges_json, last_activity, daily_interactions = row
# #         new_xp = curr_xp + xp

# #         last_date = parse_date(last_activity) if last_activity else None
# #         if last_date:
# #             if last_date.date() == today:
# #                 new_streak = curr_streak
# #                 daily_interactions += 1
# #             elif last_date.date() == today - timedelta(days=1):
# #                 new_streak = curr_streak + 1
# #                 daily_interactions = 1
# #             else:
# #                 new_streak = 1
# #                 daily_interactions = 1
# #         else:
# #             new_streak = 1
# #             daily_interactions = 1

# #         badge_list = json.loads(badges_json) if badges_json else []
# #         if badge and badge not in badge_list:
# #             badge_list.append(badge)

# #         c.execute("""
# #             UPDATE gamification
# #             SET xp_points=?, streak=?, badges=?, last_activity=?, daily_interactions=?
# #             WHERE id=?
# #         """, (new_xp, new_streak, json.dumps(badge_list), datetime.now(), daily_interactions, gid))
# #     else:
# #         badges_list = [badge] if badge else []
# #         c.execute("""
# #             INSERT INTO gamification
# #             (student_name, xp_points, streak, badges, last_activity, daily_interactions)
# #             VALUES (?, ?, ?, ?, ?, ?)
# #         """, (student_name, xp, 1, json.dumps(badges_list), datetime.now(), 1))
    
# #     conn.commit()
# #     conn.close()

# # def get_gamification(student_name):
# #     conn = sqlite3.connect(DB_NAME)
# #     c = conn.cursor()
# #     c.execute("""
# #         SELECT xp_points, streak, badges FROM gamification
# #         WHERE student_name=?
# #     """, (student_name,))
# #     row = c.fetchone()
# #     conn.close()
# #     if row:
# #         xp, streak, badges = row
# #         badge_list = json.loads(badges) if badges else []
# #         return {"xp": xp, "streak": streak, "badges": badge_list}
# #     else:
# #         return {"xp": 0, "streak": 0, "badges": []}

# # # Auto-init DB
# # init_db()



# # # # create current streak and week topic suggest , quiz, daily interaction countionions
# # # import sqlite3
# # # import json
# # # from datetime import datetime, timedelta

# # # DB_NAME = "student.db"

# # # def init_db():
# # #     """Initialize main student database with enhanced tables"""
# # #     conn = sqlite3.connect(DB_NAME)
# # #     c = conn.cursor()

# # #     # Basic interactions table
# # #     c.execute("""
# # #     CREATE TABLE IF NOT EXISTS interactions (
# # #         id INTEGER PRIMARY KEY AUTOINCREMENT,
# # #         student TEXT NOT NULL,
# # #         subject TEXT,
# # #         question TEXT,
# # #         answer TEXT,
# # #         resources TEXT,
# # #         feedback INTEGER DEFAULT 0,
# # #         feedback_comment TEXT,
# # #         created_at TEXT DEFAULT CURRENT_TIMESTAMP
# # #     )
# # #     """)

# # #     # Student progress table
# # #     c.execute("""
# # #     CREATE TABLE IF NOT EXISTS student_progress (
# # #         id INTEGER PRIMARY KEY AUTOINCREMENT,
# # #         student_name TEXT,
# # #         subject TEXT,
# # #         topic TEXT,
# # #         difficulty_level INTEGER,
# # #         mastery_score REAL,
# # #         struggle_areas TEXT,
# # #         learning_style TEXT,
# # #         last_session TIMESTAMP,
# # #         total_sessions INTEGER DEFAULT 0,
# # #         success_rate REAL DEFAULT 0
# # #     )
# # #     """)

# # #     # Learning patterns / adaptive learning
# # #     c.execute("""
# # #     CREATE TABLE IF NOT EXISTS learning_patterns (
# # #         id INTEGER PRIMARY KEY AUTOINCREMENT,
# # #         student_name TEXT,
# # #         preferred_explanation_type TEXT,
# # #         response_time_average REAL,
# # #         common_mistakes TEXT,
# # #         motivation_triggers TEXT,
# # #         engagement_level INTEGER,
# # #         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
# # #     )
# # #     """)

# # #     # Gamification (XP, streaks, badges, daily interactions)
# # #     c.execute("""
# # #     CREATE TABLE IF NOT EXISTS gamification (
# # #         id INTEGER PRIMARY KEY AUTOINCREMENT,
# # #         student_name TEXT,
# # #         xp_points INTEGER DEFAULT 0,
# # #         streak INTEGER DEFAULT 0,
# # #         badges TEXT,
# # #         last_activity TIMESTAMP,
# # #         daily_interactions INTEGER DEFAULT 0
# # #     )
# # #     """)

# # #     conn.commit()
# # #     conn.close()

# # # # ---------------------- Interactions ----------------------

# # # def log_interaction(student, subject, question, answer, resources):
# # #     conn = sqlite3.connect(DB_NAME)
# # #     c = conn.cursor()
# # #     c.execute("""
# # #         INSERT INTO interactions (student, subject, question, answer, resources)
# # #         VALUES (?, ?, ?, ?, ?)
# # #     """, (student, subject, question, answer, resources))
# # #     conn.commit()
# # #     inter_id = c.lastrowid
# # #     conn.close()
# # #     return inter_id

# # # def get_recent_interactions(student, limit=10):
# # #     conn = sqlite3.connect(DB_NAME)
# # #     c = conn.cursor()
# # #     c.execute("""
# # #         SELECT id, question, answer, resources, feedback, feedback_comment, created_at
# # #         FROM interactions
# # #         WHERE student = ?
# # #         ORDER BY created_at DESC
# # #         LIMIT ?
# # #     """, (student, limit))
# # #     rows = c.fetchall()
# # #     conn.close()
# # #     return rows

# # # def set_feedback(inter_id, feedback_val, comment):
# # #     conn = sqlite3.connect(DB_NAME)
# # #     c = conn.cursor()
# # #     c.execute("""
# # #         UPDATE interactions
# # #         SET feedback = ?, feedback_comment = ?
# # #         WHERE id = ?
# # #     """, (feedback_val, comment, inter_id))
# # #     conn.commit()
# # #     conn.close()

# # # # ---------------------- Progress ----------------------

# # # def update_student_progress(student_name, subject, topic, difficulty, mastery_score, struggle_areas, learning_style):
# # #     conn = sqlite3.connect(DB_NAME)
# # #     c = conn.cursor()
# # #     c.execute("""
# # #         SELECT id, total_sessions FROM student_progress
# # #         WHERE student_name = ? AND subject = ? AND topic = ?
# # #     """, (student_name, subject, topic))
# # #     row = c.fetchone()
# # #     if row:
# # #         pid, total_sessions = row
# # #         c.execute("""
# # #             UPDATE student_progress
# # #             SET difficulty_level=?, mastery_score=?, struggle_areas=?, learning_style=?, last_session=?, total_sessions=?
# # #             WHERE id=?
# # #         """, (difficulty, mastery_score, struggle_areas, learning_style, datetime.now(), total_sessions+1, pid))
# # #     else:
# # #         c.execute("""
# # #             INSERT INTO student_progress 
# # #             (student_name, subject, topic, difficulty_level, mastery_score, struggle_areas, learning_style, last_session, total_sessions)
# # #             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
# # #         """, (student_name, subject, topic, difficulty, mastery_score, struggle_areas, learning_style, datetime.now(), 1))
# # #     conn.commit()
# # #     conn.close()

# # # def get_student_progress(student_name, subject):
# # #     conn = sqlite3.connect(DB_NAME)
# # #     c = conn.cursor()
# # #     c.execute("""
# # #         SELECT * FROM student_progress
# # #         WHERE student_name=? AND subject=?
# # #         ORDER BY last_session DESC
# # #     """, (student_name, subject))
# # #     rows = c.fetchall()
# # #     conn.close()
# # #     return rows

# # # # ---------------------- Gamification ----------------------

# # # def parse_date(date_str):
# # #     """Helper to safely parse SQLite timestamp strings"""
# # #     if not date_str:
# # #         return None
# # #     for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
# # #         try:
# # #             return datetime.strptime(date_str, fmt)
# # #         except ValueError:
# # #             continue
# # #     return None
# # # def update_gamification(student_name, xp=0, badge=None):
# # #     conn = sqlite3.connect(DB_NAME)
# # #     c = conn.cursor()
# # #     c.execute("""
# # #         SELECT id, xp_points, streak, badges, last_activity, daily_interactions
# # #         FROM gamification
# # #         WHERE student_name=?
# # #     """, (student_name,))
# # #     row = c.fetchone()
    
# # #     today = datetime.now().date()
    
# # #     if row:
# # #         gid, curr_xp, curr_streak, badges_json, last_activity, daily_interactions = row
# # #         new_xp = curr_xp + xp

# # #         last_date = parse_date(last_activity) if last_activity else None
# # #         if last_date:
# # #             if last_date.date() == today:
# # #                 # same day → count only one interaction per log call
# # #                 new_streak = curr_streak
# # #                 daily_interactions += 1
# # #             elif last_date.date() == today - timedelta(days=1):
# # #                 # streak continues
# # #                 new_streak = curr_streak + 1
# # #                 daily_interactions = 1
# # #             else:
# # #                 # missed → reset streak
# # #                 new_streak = 1
# # #                 daily_interactions = 1
# # #         else:
# # #             new_streak = 1
# # #             daily_interactions = 1

# # #         badge_list = json.loads(badges_json) if badges_json else []
# # #         if badge and badge not in badge_list:
# # #             badge_list.append(badge)

# # #         # ✅ Include daily_interactions in the UPDATE
# # #         c.execute("""
# # #             UPDATE gamification
# # #             SET xp_points=?, streak=?, badges=?, last_activity=?, daily_interactions=?
# # #             WHERE id=?
# # #         """, (new_xp, new_streak, json.dumps(badge_list), datetime.now(), daily_interactions, gid))
# # #     else:
# # #         badges_list = [badge] if badge else []
# # #         c.execute("""
# # #             INSERT INTO gamification
# # #             (student_name, xp_points, streak, badges, last_activity, daily_interactions)
# # #             VALUES (?, ?, ?, ?, ?, ?)
# # #         """, (student_name, xp, 1, json.dumps(badges_list), datetime.now(), 1))
    
# # #     conn.commit()
# # #     conn.close()


# # # def get_gamification(student_name):
# # #     conn = sqlite3.connect(DB_NAME)
# # #     c = conn.cursor()
# # #     c.execute("""
# # #         SELECT xp_points, streak, badges FROM gamification
# # #         WHERE student_name=?
# # #     """, (student_name,))
# # #     row = c.fetchone()
# # #     conn.close()
# # #     if row:
# # #         xp, streak, badges = row
# # #         badge_list = json.loads(badges) if badges else []
# # #         return {
# # #             "xp": xp,
# # #             "streak": streak,
# # #             "badges": badge_list,
            
# # #         }
# # #     else:
# # #         return {"xp": 0, "streak": 0, "badges": []}

# # # # Auto-init DB
# # # init_db()




# # # # # import sqlite3
# # # # # import json
# # # # # from datetime import datetime, timedelta

# # # # # DB_NAME = "student.db"

# # # # # def init_db():
# # # # #     """Initialize main student database with enhanced tables"""
# # # # #     conn = sqlite3.connect(DB_NAME)
# # # # #     c = conn.cursor()

# # # # #     # Basic interactions table
# # # # #     c.execute("""
# # # # #     CREATE TABLE IF NOT EXISTS interactions (
# # # # #         id INTEGER PRIMARY KEY AUTOINCREMENT,
# # # # #         student TEXT NOT NULL,
# # # # #         subject TEXT,
# # # # #         question TEXT,
# # # # #         answer TEXT,
# # # # #         resources TEXT,
# # # # #         feedback INTEGER DEFAULT 0,
# # # # #         feedback_comment TEXT,
# # # # #         created_at TEXT DEFAULT CURRENT_TIMESTAMP
# # # # #     )
# # # # #     """)

# # # # #     # Student progress table
# # # # #     c.execute("""
# # # # #     CREATE TABLE IF NOT EXISTS student_progress (
# # # # #         id INTEGER PRIMARY KEY AUTOINCREMENT,
# # # # #         student_name TEXT,
# # # # #         subject TEXT,
# # # # #         topic TEXT,
# # # # #         difficulty_level INTEGER,
# # # # #         mastery_score REAL,
# # # # #         struggle_areas TEXT,
# # # # #         learning_style TEXT,
# # # # #         last_session TIMESTAMP,
# # # # #         total_sessions INTEGER DEFAULT 0,
# # # # #         success_rate REAL DEFAULT 0
# # # # #     )
# # # # #     """)

# # # # #     # Learning patterns / adaptive learning
# # # # #     c.execute("""
# # # # #     CREATE TABLE IF NOT EXISTS learning_patterns (
# # # # #         id INTEGER PRIMARY KEY AUTOINCREMENT,
# # # # #         student_name TEXT,
# # # # #         preferred_explanation_type TEXT,
# # # # #         response_time_average REAL,
# # # # #         common_mistakes TEXT,
# # # # #         motivation_triggers TEXT,
# # # # #         engagement_level INTEGER,
# # # # #         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
# # # # #     )
# # # # #     """)

# # # # #     # Gamification (XP, streaks, badges, daily interactions)
# # # # #     c.execute("""
# # # # #     CREATE TABLE IF NOT EXISTS gamification (
# # # # #         id INTEGER PRIMARY KEY AUTOINCREMENT,
# # # # #         student_name TEXT,
# # # # #         xp_points INTEGER DEFAULT 0,
# # # # #         streak INTEGER DEFAULT 0,
# # # # #         badges TEXT,
# # # # #         last_activity TIMESTAMP,
# # # # #         daily_interactions INTEGER DEFAULT 0
# # # # #     )
# # # # #     """)

# # # # #     conn.commit()
# # # # #     conn.close()

# # # # # def log_interaction(student, subject, question, answer, resources):
# # # # #     conn = sqlite3.connect(DB_NAME)
# # # # #     c = conn.cursor()
# # # # #     c.execute("""
# # # # #         INSERT INTO interactions (student, subject, question, answer, resources)
# # # # #         VALUES (?, ?, ?, ?, ?)
# # # # #     """, (student, subject, question, answer, resources))
# # # # #     conn.commit()
# # # # #     inter_id = c.lastrowid
# # # # #     conn.close()
# # # # #     return inter_id

# # # # # def get_recent_interactions(student, limit=10):
# # # # #     conn = sqlite3.connect(DB_NAME)
# # # # #     c = conn.cursor()
# # # # #     c.execute("""
# # # # #         SELECT id, question, answer, resources, feedback, feedback_comment, created_at
# # # # #         FROM interactions
# # # # #         WHERE student = ?
# # # # #         ORDER BY created_at DESC
# # # # #         LIMIT ?
# # # # #     """, (student, limit))
# # # # #     rows = c.fetchall()
# # # # #     conn.close()
# # # # #     return rows

# # # # # def set_feedback(inter_id, feedback_val, comment):
# # # # #     conn = sqlite3.connect(DB_NAME)
# # # # #     c = conn.cursor()
# # # # #     c.execute("""
# # # # #         UPDATE interactions
# # # # #         SET feedback = ?, feedback_comment = ?
# # # # #         WHERE id = ?
# # # # #     """, (feedback_val, comment, inter_id))
# # # # #     conn.commit()
# # # # #     conn.close()

# # # # # def update_student_progress(student_name, subject, topic, difficulty, mastery_score, struggle_areas, learning_style):
# # # # #     conn = sqlite3.connect(DB_NAME)
# # # # #     c = conn.cursor()
# # # # #     c.execute("""
# # # # #         SELECT id, total_sessions FROM student_progress
# # # # #         WHERE student_name = ? AND subject = ? AND topic = ?
# # # # #     """, (student_name, subject, topic))
# # # # #     row = c.fetchone()
# # # # #     if row:
# # # # #         pid, total_sessions = row
# # # # #         c.execute("""
# # # # #             UPDATE student_progress
# # # # #             SET difficulty_level=?, mastery_score=?, struggle_areas=?, learning_style=?, last_session=?, total_sessions=?
# # # # #             WHERE id=?
# # # # #         """, (difficulty, mastery_score, struggle_areas, learning_style, datetime.now(), total_sessions+1, pid))
# # # # #     else:
# # # # #         c.execute("""
# # # # #             INSERT INTO student_progress 
# # # # #             (student_name, subject, topic, difficulty_level, mastery_score, struggle_areas, learning_style, last_session, total_sessions)
# # # # #             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
# # # # #         """, (student_name, subject, topic, difficulty, mastery_score, struggle_areas, learning_style, datetime.now(), 1))
# # # # #     conn.commit()
# # # # #     conn.close()

# # # # # def get_student_progress(student_name, subject):
# # # # #     conn = sqlite3.connect(DB_NAME)
# # # # #     c = conn.cursor()
# # # # #     c.execute("""
# # # # #         SELECT * FROM student_progress
# # # # #         WHERE student_name=? AND subject=?
# # # # #         ORDER BY last_session DESC
# # # # #     """, (student_name, subject))
# # # # #     rows = c.fetchall()
# # # # #     conn.close()
# # # # #     return rows

# # # # # def update_gamification(student_name, xp=0, badge=None):
# # # # #     conn = sqlite3.connect(DB_NAME)
# # # # #     c = conn.cursor()
# # # # #     c.execute("""
# # # # #         SELECT id, xp_points, streak, badges, last_activity, daily_interactions
# # # # #         FROM gamification
# # # # #         WHERE student_name=?
# # # # #     """, (student_name,))
# # # # #     row = c.fetchone()
    
# # # # #     today = datetime.now().date()
    
# # # # #     if row:
# # # # #         gid, curr_xp, curr_streak, badges_json, last_activity, daily_interactions = row
# # # # #         new_xp = curr_xp + xp

# # # # #         if last_activity:
# # # # #             last_date = datetime.strptime(last_activity, "%Y-%m-%d %H:%M:%S.%f").date()
# # # # #             if last_date == today:
# # # # #                 # same day → increment daily interactions
# # # # #                 new_streak = curr_streak
# # # # #                 daily_interactions += 1
# # # # #             elif last_date == today - timedelta(days=1):
# # # # #                 # yesterday activity → streak continues
# # # # #                 new_streak = curr_streak + 1
# # # # #                 daily_interactions = 1
# # # # #             else:
# # # # #                 # missed gap → reset streak
# # # # #                 new_streak = 1
# # # # #                 daily_interactions = 1
# # # # #         else:
# # # # #             new_streak = 1
# # # # #             daily_interactions = 1

# # # # #         badge_list = json.loads(badges_json) if badges_json else []
# # # # #         if badge and badge not in badge_list:
# # # # #             badge_list.append(badge)

# # # # #         c.execute("""
# # # # #             UPDATE gamification
# # # # #             SET xp_points=?, streak=?, badges=?, last_activity=?, daily_interactions=?
# # # # #             WHERE id=?
# # # # #         """, (new_xp, new_streak, json.dumps(badge_list), datetime.now(), daily_interactions, gid))
# # # # #     else:
# # # # #         badges_list = [badge] if badge else []
# # # # #         c.execute("""
# # # # #             INSERT INTO gamification
# # # # #             (student_name, xp_points, streak, badges, last_activity, daily_interactions)
# # # # #             VALUES (?, ?, ?, ?, ?, ?)
# # # # #         """, (student_name, xp, 1, json.dumps(badges_list), datetime.now(), 1))
    
# # # # #     conn.commit()
# # # # #     conn.close()

# # # # # def get_gamification(student_name):
# # # # #     conn = sqlite3.connect(DB_NAME)
# # # # #     c = conn.cursor()
# # # # #     c.execute("""
# # # # #         SELECT xp_points, streak, badges, daily_interactions FROM gamification
# # # # #         WHERE student_name=?
# # # # #     """, (student_name,))
# # # # #     row = c.fetchone()
# # # # #     conn.close()
# # # # #     if row:
# # # # #         xp, streak, badges, daily_interactions = row
# # # # #         badge_list = json.loads(badges) if badges else []
# # # # #         return {"xp": xp, "streak": streak, "badges": badge_list, "daily_interactions": daily_interactions}
# # # # #     else:
# # # # #         return {"xp": 0, "streak": 0, "badges": [], "daily_interactions": 0}

# # # # # # Auto-init DB
# # # # # init_db()







# # # # # # import sqlite3
# # # # # # import json
# # # # # # from datetime import datetime

# # # # # # DB_NAME = "student.db"

# # # # # # def init_db():
# # # # # #     """Initialize main student database with enhanced tables"""
# # # # # #     conn = sqlite3.connect(DB_NAME)
# # # # # #     c = conn.cursor()

# # # # # #     # Basic interactions table
# # # # # #     c.execute("""
# # # # # #     CREATE TABLE IF NOT EXISTS interactions (
# # # # # #         id INTEGER PRIMARY KEY AUTOINCREMENT,
# # # # # #         student TEXT NOT NULL,
# # # # # #         subject TEXT,
# # # # # #         question TEXT,
# # # # # #         answer TEXT,
# # # # # #         resources TEXT,
# # # # # #         feedback INTEGER DEFAULT 0,
# # # # # #         feedback_comment TEXT,
# # # # # #         created_at TEXT DEFAULT CURRENT_TIMESTAMP
# # # # # #     )
# # # # # #     """)

# # # # # #     # Student progress table
# # # # # #     c.execute("""
# # # # # #     CREATE TABLE IF NOT EXISTS student_progress (
# # # # # #         id INTEGER PRIMARY KEY AUTOINCREMENT,
# # # # # #         student_name TEXT,
# # # # # #         subject TEXT,
# # # # # #         topic TEXT,
# # # # # #         difficulty_level INTEGER,
# # # # # #         mastery_score REAL,
# # # # # #         struggle_areas TEXT,
# # # # # #         learning_style TEXT,
# # # # # #         last_session TIMESTAMP,
# # # # # #         total_sessions INTEGER DEFAULT 0,
# # # # # #         success_rate REAL DEFAULT 0
# # # # # #     )
# # # # # #     """)

# # # # # #     # Learning patterns / adaptive learning
# # # # # #     c.execute("""
# # # # # #     CREATE TABLE IF NOT EXISTS learning_patterns (
# # # # # #         id INTEGER PRIMARY KEY AUTOINCREMENT,
# # # # # #         student_name TEXT,
# # # # # #         preferred_explanation_type TEXT,
# # # # # #         response_time_average REAL,
# # # # # #         common_mistakes TEXT,
# # # # # #         motivation_triggers TEXT,
# # # # # #         engagement_level INTEGER,
# # # # # #         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
# # # # # #     )
# # # # # #     """)

# # # # # #     # Gamification (XP, streaks, badges)
# # # # # #     c.execute("""
# # # # # #     CREATE TABLE IF NOT EXISTS gamification (
# # # # # #         id INTEGER PRIMARY KEY AUTOINCREMENT,
# # # # # #         student_name TEXT,
# # # # # #         xp_points INTEGER DEFAULT 0,
# # # # # #         streak INTEGER DEFAULT 0,
# # # # # #         badges TEXT,
# # # # # #         last_activity TIMESTAMP
# # # # # #     )
# # # # # #     """)

# # # # # #     conn.commit()
# # # # # #     conn.close()

# # # # # # def log_interaction(student, subject, question, answer, resources):
# # # # # #     conn = sqlite3.connect(DB_NAME)
# # # # # #     c = conn.cursor()
# # # # # #     c.execute("""
# # # # # #         INSERT INTO interactions (student, subject, question, answer, resources)
# # # # # #         VALUES (?, ?, ?, ?, ?)
# # # # # #     """, (student, subject, question, answer, resources))
# # # # # #     conn.commit()
# # # # # #     inter_id = c.lastrowid
# # # # # #     conn.close()
# # # # # #     return inter_id

# # # # # # def get_recent_interactions(student, limit=10):
# # # # # #     conn = sqlite3.connect(DB_NAME)
# # # # # #     c = conn.cursor()
# # # # # #     c.execute("""
# # # # # #         SELECT id, question, answer, resources, feedback, feedback_comment, created_at
# # # # # #         FROM interactions
# # # # # #         WHERE student = ?
# # # # # #         ORDER BY created_at DESC
# # # # # #         LIMIT ?
# # # # # #     """, (student, limit))
# # # # # #     rows = c.fetchall()
# # # # # #     conn.close()
# # # # # #     return rows

# # # # # # def set_feedback(inter_id, feedback_val, comment):
# # # # # #     conn = sqlite3.connect(DB_NAME)
# # # # # #     c = conn.cursor()
# # # # # #     c.execute("""
# # # # # #         UPDATE interactions
# # # # # #         SET feedback = ?, feedback_comment = ?
# # # # # #         WHERE id = ?
# # # # # #     """, (feedback_val, comment, inter_id))
# # # # # #     conn.commit()
# # # # # #     conn.close()

# # # # # # def update_student_progress(student_name, subject, topic, difficulty, mastery_score, struggle_areas, learning_style):
# # # # # #     conn = sqlite3.connect(DB_NAME)
# # # # # #     c = conn.cursor()
# # # # # #     # Check if progress exists
# # # # # #     c.execute("""
# # # # # #         SELECT id, total_sessions FROM student_progress
# # # # # #         WHERE student_name = ? AND subject = ? AND topic = ?
# # # # # #     """, (student_name, subject, topic))
# # # # # #     row = c.fetchone()
# # # # # #     if row:
# # # # # #         pid, total_sessions = row
# # # # # #         c.execute("""
# # # # # #             UPDATE student_progress
# # # # # #             SET difficulty_level=?, mastery_score=?, struggle_areas=?, learning_style=?, last_session=?, total_sessions=?
# # # # # #             WHERE id=?
# # # # # #         """, (difficulty, mastery_score, struggle_areas, learning_style, datetime.now(), total_sessions+1, pid))
# # # # # #     else:
# # # # # #         c.execute("""
# # # # # #             INSERT INTO student_progress 
# # # # # #             (student_name, subject, topic, difficulty_level, mastery_score, struggle_areas, learning_style, last_session, total_sessions)
# # # # # #             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
# # # # # #         """, (student_name, subject, topic, difficulty, mastery_score, struggle_areas, learning_style, datetime.now(), 1))
# # # # # #     conn.commit()
# # # # # #     conn.close()

# # # # # # def get_student_progress(student_name, subject):
# # # # # #     conn = sqlite3.connect(DB_NAME)
# # # # # #     c = conn.cursor()
# # # # # #     c.execute("""
# # # # # #         SELECT * FROM student_progress
# # # # # #         WHERE student_name=? AND subject=?
# # # # # #         ORDER BY last_session DESC
# # # # # #     """, (student_name, subject))
# # # # # #     rows = c.fetchall()
# # # # # #     conn.close()
# # # # # #     return rows

# # # # # # def update_gamification(student_name, xp=0, badge=None):
# # # # # #     conn = sqlite3.connect(DB_NAME)
# # # # # #     c = conn.cursor()
# # # # # #     c.execute("""
# # # # # #         SELECT id, xp_points, streak, badges, last_activity 
# # # # # #         FROM gamification
# # # # # #         WHERE student_name=?
# # # # # #     """, (student_name,))
# # # # # #     row = c.fetchone()
    
# # # # # #     today = datetime.now().date()
    
# # # # # #     if row:
# # # # # #         gid, curr_xp, curr_streak, badges_json, last_activity = row
# # # # # #         new_xp = curr_xp + xp
        
# # # # # #         # Calculate streak increment
# # # # # #         if last_activity:
# # # # # #             last_date = datetime.strptime(last_activity, "%Y-%m-%d %H:%M:%S.%f").date()
# # # # # #             if last_date == today - timedelta(days=1):
# # # # # #                 new_streak = curr_streak + 1  # consecutive day, increment
# # # # # #             elif last_date == today:
# # # # # #                 new_streak = curr_streak  # already interacted today, no increment
# # # # # #             else:
# # # # # #                 new_streak = 1  # missed a day, reset streak
# # # # # #         else:
# # # # # #             new_streak = 1  # first activity ever
        
# # # # # #         badge_list = json.loads(badges_json) if badges_json else []
# # # # # #         if badge and badge not in badge_list:
# # # # # #             badge_list.append(badge)
        
# # # # # #         c.execute("""
# # # # # #             UPDATE gamification
# # # # # #             SET xp_points=?, streak=?, badges=?, last_activity=?
# # # # # #             WHERE id=?
# # # # # #         """, (new_xp, new_streak, json.dumps(badge_list), datetime.now(), gid))
        
# # # # # #     else:
# # # # # #         # first time gamification record
# # # # # #         badges_list = [badge] if badge else []
# # # # # #         c.execute("""
# # # # # #             INSERT INTO gamification
# # # # # #             (student_name, xp_points, streak, badges, last_activity)
# # # # # #             VALUES (?, ?, ?, ?, ?)
# # # # # #         """, (student_name, xp, 1, json.dumps(badges_list), datetime.now()))
    
# # # # # #     conn.commit()
# # # # # #     conn.close()
# # # # # # # def update_gamification(student_name, xp=0, streak_increment=True, badge=None):
# # # # # # #     conn = sqlite3.connect(DB_NAME)
# # # # # # #     c = conn.cursor()
# # # # # # #     c.execute("""
# # # # # # #         SELECT id, xp_points, streak, badges FROM gamification
# # # # # # #         WHERE student_name=?
# # # # # # #     """, (student_name,))
# # # # # # #     row = c.fetchone()
# # # # # # #     if row:
# # # # # # #         gid, curr_xp, curr_streak, badges = row
# # # # # # #         new_xp = curr_xp + xp
# # # # # # #         new_streak = curr_streak + 1 if streak_increment else curr_streak
# # # # # # #         badge_list = json.loads(badges) if badges else []
# # # # # # #         if badge and badge not in badge_list:
# # # # # # #             badge_list.append(badge)
# # # # # # #         c.execute("""
# # # # # # #             UPDATE gamification
# # # # # # #             SET xp_points=?, streak=?, badges=?, last_activity=?
# # # # # # #             WHERE id=?
# # # # # # #         """, (new_xp, new_streak, json.dumps(badge_list), datetime.now(), gid))
# # # # # # #     else:
# # # # # # #         badges_list = [badge] if badge else []
# # # # # # #         c.execute("""
# # # # # # #             INSERT INTO gamification
# # # # # # #             (student_name, xp_points, streak, badges, last_activity)
# # # # # # #             VALUES (?, ?, ?, ?, ?)
# # # # # # #         """, (student_name, xp, 1 if streak_increment else 0, json.dumps(badges_list), datetime.now()))
# # # # # # #     conn.commit()
# # # # # # #     conn.close()

# # # # # # # --- NEW HELPER: get current gamification for display ---
# # # # # # def get_gamification(student_name):
# # # # # #     conn = sqlite3.connect(DB_NAME)
# # # # # #     c = conn.cursor()
# # # # # #     c.execute("""
# # # # # #         SELECT xp_points, streak, badges FROM gamification
# # # # # #         WHERE student_name=?
# # # # # #     """, (student_name,))
# # # # # #     row = c.fetchone()
# # # # # #     conn.close()
# # # # # #     if row:
# # # # # #         xp, streak, badges = row
# # # # # #         badge_list = json.loads(badges) if badges else []
# # # # # #         return {"xp": xp, "streak": streak, "badges": badge_list}
# # # # # #     else:
# # # # # #         return {"xp": 0, "streak": 0, "badges": []}

# # # # # # # Auto-init DB
# # # # # # init_db()





# # # # # # # import sqlite3
# # # # # # # import json
# # # # # # # from datetime import datetime

# # # # # # # DB_NAME = "student.db"

# # # # # # # def init_db():
# # # # # # #     """Initialize main student database with enhanced tables"""
# # # # # # #     conn = sqlite3.connect(DB_NAME)
# # # # # # #     c = conn.cursor()

# # # # # # #     # Basic interactions table
# # # # # # #     c.execute("""
# # # # # # #     CREATE TABLE IF NOT EXISTS interactions (
# # # # # # #         id INTEGER PRIMARY KEY AUTOINCREMENT,
# # # # # # #         student TEXT NOT NULL,
# # # # # # #         subject TEXT,
# # # # # # #         question TEXT,
# # # # # # #         answer TEXT,
# # # # # # #         resources TEXT,
# # # # # # #         feedback INTEGER DEFAULT 0,
# # # # # # #         feedback_comment TEXT,
# # # # # # #         created_at TEXT DEFAULT CURRENT_TIMESTAMP
# # # # # # #     )
# # # # # # #     """)

# # # # # # #     # Student progress table
# # # # # # #     c.execute("""
# # # # # # #     CREATE TABLE IF NOT EXISTS student_progress (
# # # # # # #         id INTEGER PRIMARY KEY AUTOINCREMENT,
# # # # # # #         student_name TEXT,
# # # # # # #         subject TEXT,
# # # # # # #         topic TEXT,
# # # # # # #         difficulty_level INTEGER,
# # # # # # #         mastery_score REAL,
# # # # # # #         struggle_areas TEXT,
# # # # # # #         learning_style TEXT,
# # # # # # #         last_session TIMESTAMP,
# # # # # # #         total_sessions INTEGER DEFAULT 0,
# # # # # # #         success_rate REAL DEFAULT 0
# # # # # # #     )
# # # # # # #     """)

# # # # # # #     # Learning patterns / adaptive learning
# # # # # # #     c.execute("""
# # # # # # #     CREATE TABLE IF NOT EXISTS learning_patterns (
# # # # # # #         id INTEGER PRIMARY KEY AUTOINCREMENT,
# # # # # # #         student_name TEXT,
# # # # # # #         preferred_explanation_type TEXT,
# # # # # # #         response_time_average REAL,
# # # # # # #         common_mistakes TEXT,
# # # # # # #         motivation_triggers TEXT,
# # # # # # #         engagement_level INTEGER,
# # # # # # #         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
# # # # # # #     )
# # # # # # #     """)

# # # # # # #     # Gamification (XP, streaks, badges)
# # # # # # #     c.execute("""
# # # # # # #     CREATE TABLE IF NOT EXISTS gamification (
# # # # # # #         id INTEGER PRIMARY KEY AUTOINCREMENT,
# # # # # # #         student_name TEXT,
# # # # # # #         xp_points INTEGER DEFAULT 0,
# # # # # # #         streak INTEGER DEFAULT 0,
# # # # # # #         badges TEXT,
# # # # # # #         last_activity TIMESTAMP
# # # # # # #     )
# # # # # # #     """)

# # # # # # #     conn.commit()
# # # # # # #     conn.close()

# # # # # # # def log_interaction(student, subject, question, answer, resources):
# # # # # # #     conn = sqlite3.connect(DB_NAME)
# # # # # # #     c = conn.cursor()
# # # # # # #     c.execute("""
# # # # # # #         INSERT INTO interactions (student, subject, question, answer, resources)
# # # # # # #         VALUES (?, ?, ?, ?, ?)
# # # # # # #     """, (student, subject, question, answer, resources))
# # # # # # #     conn.commit()
# # # # # # #     inter_id = c.lastrowid
# # # # # # #     conn.close()
# # # # # # #     return inter_id

# # # # # # # def get_recent_interactions(student, limit=10):
# # # # # # #     conn = sqlite3.connect(DB_NAME)
# # # # # # #     c = conn.cursor()
# # # # # # #     c.execute("""
# # # # # # #         SELECT id, question, answer, resources, feedback, feedback_comment, created_at
# # # # # # #         FROM interactions
# # # # # # #         WHERE student = ?
# # # # # # #         ORDER BY created_at DESC
# # # # # # #         LIMIT ?
# # # # # # #     """, (student, limit))
# # # # # # #     rows = c.fetchall()
# # # # # # #     conn.close()
# # # # # # #     return rows

# # # # # # # def set_feedback(inter_id, feedback_val, comment):
# # # # # # #     conn = sqlite3.connect(DB_NAME)
# # # # # # #     c = conn.cursor()
# # # # # # #     c.execute("""
# # # # # # #         UPDATE interactions
# # # # # # #         SET feedback = ?, feedback_comment = ?
# # # # # # #         WHERE id = ?
# # # # # # #     """, (feedback_val, comment, inter_id))
# # # # # # #     conn.commit()
# # # # # # #     conn.close()

# # # # # # # def update_student_progress(student_name, subject, topic, difficulty, mastery_score, struggle_areas, learning_style):
# # # # # # #     conn = sqlite3.connect(DB_NAME)
# # # # # # #     c = conn.cursor()
# # # # # # #     # Check if progress exists
# # # # # # #     c.execute("""
# # # # # # #         SELECT id, total_sessions FROM student_progress
# # # # # # #         WHERE student_name = ? AND subject = ? AND topic = ?
# # # # # # #     """, (student_name, subject, topic))
# # # # # # #     row = c.fetchone()
# # # # # # #     if row:
# # # # # # #         pid, total_sessions = row
# # # # # # #         c.execute("""
# # # # # # #             UPDATE student_progress
# # # # # # #             SET difficulty_level=?, mastery_score=?, struggle_areas=?, learning_style=?, last_session=?, total_sessions=?
# # # # # # #             WHERE id=?
# # # # # # #         """, (difficulty, mastery_score, struggle_areas, learning_style, datetime.now(), total_sessions+1, pid))
# # # # # # #     else:
# # # # # # #         c.execute("""
# # # # # # #             INSERT INTO student_progress 
# # # # # # #             (student_name, subject, topic, difficulty_level, mastery_score, struggle_areas, learning_style, last_session, total_sessions)
# # # # # # #             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
# # # # # # #         """, (student_name, subject, topic, difficulty, mastery_score, struggle_areas, learning_style, datetime.now(), 1))
# # # # # # #     conn.commit()
# # # # # # #     conn.close()

# # # # # # # def get_student_progress(student_name, subject):
# # # # # # #     conn = sqlite3.connect(DB_NAME)
# # # # # # #     c = conn.cursor()
# # # # # # #     c.execute("""
# # # # # # #         SELECT * FROM student_progress
# # # # # # #         WHERE student_name=? AND subject=?
# # # # # # #         ORDER BY last_session DESC
# # # # # # #     """, (student_name, subject))
# # # # # # #     rows = c.fetchall()
# # # # # # #     conn.close()
# # # # # # #     return rows

# # # # # # # def update_gamification(student_name, xp=0, streak_increment=True, badge=None):
# # # # # # #     conn = sqlite3.connect(DB_NAME)
# # # # # # #     c = conn.cursor()
# # # # # # #     c.execute("""
# # # # # # #         SELECT id, xp_points, streak, badges FROM gamification
# # # # # # #         WHERE student_name=?
# # # # # # #     """, (student_name,))
# # # # # # #     row = c.fetchone()
# # # # # # #     if row:
# # # # # # #         gid, curr_xp, curr_streak, badges = row
# # # # # # #         new_xp = curr_xp + xp
# # # # # # #         new_streak = curr_streak + 1 if streak_increment else curr_streak
# # # # # # #         badge_list = json.loads(badges) if badges else []
# # # # # # #         if badge and badge not in badge_list:
# # # # # # #             badge_list.append(badge)
# # # # # # #         c.execute("""
# # # # # # #             UPDATE gamification
# # # # # # #             SET xp_points=?, streak=?, badges=?, last_activity=?
# # # # # # #             WHERE id=?
# # # # # # #         """, (new_xp, new_streak, json.dumps(badge_list), datetime.now(), gid))
# # # # # # #     else:
# # # # # # #         badges_list = [badge] if badge else []
# # # # # # #         c.execute("""
# # # # # # #             INSERT INTO gamification
# # # # # # #             (student_name, xp_points, streak, badges, last_activity)
# # # # # # #             VALUES (?, ?, ?, ?, ?)
# # # # # # #         """, (student_name, xp, 1 if streak_increment else 0, json.dumps(badges_list), datetime.now()))
# # # # # # #     conn.commit()
# # # # # # #     conn.close()

# # # # # # # # Auto-init DB
# # # # # # # init_db()






# # # # # # # # ************************************final code for me 
# # # # # # # import sqlite3
# # # # # # # import json
# # # # # # # from datetime import datetime

# # # # # # # DB_NAME = "student.db"

# # # # # # # def init_db():
# # # # # # #     conn = sqlite3.connect(DB_NAME)
# # # # # # #     c = conn.cursor()
# # # # # # #     c.execute("""
# # # # # # #     CREATE TABLE IF NOT EXISTS interactions (
# # # # # # #         id INTEGER PRIMARY KEY AUTOINCREMENT,
# # # # # # #         student TEXT NOT NULL,
# # # # # # #         subject TEXT,
# # # # # # #         question TEXT,
# # # # # # #         answer TEXT,
# # # # # # #         resources TEXT,
# # # # # # #         feedback INTEGER DEFAULT 0,
# # # # # # #         feedback_comment TEXT,
# # # # # # #         created_at TEXT DEFAULT CURRENT_TIMESTAMP
# # # # # # #     )
# # # # # # #     """)
# # # # # # #     conn.commit()
# # # # # # #     conn.close()

# # # # # # # def log_interaction(student, subject, question, answer, resources):
# # # # # # #     conn = sqlite3.connect(DB_NAME)
# # # # # # #     c = conn.cursor()
# # # # # # #     c.execute("""
# # # # # # #         INSERT INTO interactions (student, subject, question, answer, resources)
# # # # # # #         VALUES (?, ?, ?, ?, ?)
# # # # # # #     """, (student, subject, question, answer, resources))
# # # # # # #     conn.commit()
# # # # # # #     inter_id = c.lastrowid
# # # # # # #     conn.close()
# # # # # # #     return inter_id

# # # # # # # def get_recent_interactions(student, limit=10):
# # # # # # #     conn = sqlite3.connect(DB_NAME)
# # # # # # #     c = conn.cursor()
# # # # # # #     c.execute("""
# # # # # # #         SELECT id, question, answer, resources, feedback, feedback_comment, created_at
# # # # # # #         FROM interactions
# # # # # # #         WHERE student = ?
# # # # # # #         ORDER BY created_at DESC
# # # # # # #         LIMIT ?
# # # # # # #     """, (student, limit))
# # # # # # #     rows = c.fetchall()
# # # # # # #     conn.close()
# # # # # # #     return rows

# # # # # # # def set_feedback(inter_id, feedback_val, comment):
# # # # # # #     conn = sqlite3.connect(DB_NAME)
# # # # # # #     c = conn.cursor()
# # # # # # #     c.execute("""
# # # # # # #         UPDATE interactions
# # # # # # #         SET feedback = ?, feedback_comment = ?
# # # # # # #         WHERE id = ?
# # # # # # #     """, (feedback_val, comment, inter_id))
# # # # # # #     conn.commit()
# # # # # # #     conn.close()
# # # # # # # def get_report(student):
# # # # # # #     conn = sqlite3.connect(DB_NAME)
# # # # # # #     c = conn.cursor()
# # # # # # #     c.execute("""
# # # # # # #         SELECT id, subject, question, answer, resources, feedback, feedback_comment, created_at
# # # # # # #         FROM interactions
# # # # # # #         WHERE student = ?
# # # # # # #         ORDER BY created_at ASC
# # # # # # #     """, (student,))
# # # # # # #     rows = c.fetchall()
# # # # # # #     conn.close()
# # # # # # #     return rows
# # # # # # # # Initialize DB automatically
# # # # # # # init_db()


# # # # # # # # **************final code end here for me 