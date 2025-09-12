# # import sqlite3

# # DB_NAME = "student.db"


# # def create_users_table():
# #     conn = sqlite3.connect(DB_NAME)
# #     c = conn.cursor()
# #     c.execute(
# #         """
# #         CREATE TABLE IF NOT EXISTS users (
# #             id INTEGER PRIMARY KEY AUTOINCREMENT,
# #             email TEXT UNIQUE,
# #             password TEXT,
# #             role TEXT,
# #             is_logged_in INTEGER DEFAULT 0
# #         )
# #     """
# #     )
# #     conn.commit()
# #     conn.close()


# # def login_user(email, password, role=None):
# #     conn = sqlite3.connect(DB_NAME)
# #     c = conn.cursor()

# #     if role:
# #         c.execute(
# #             "SELECT * FROM users WHERE email=? AND password=? AND role=?",
# #             (email, password, role),
# #         )
# #     else:
# #         c.execute(
# #             "SELECT * FROM users WHERE email=? AND password=?",
# #             (email, password),
# #         )

# #     user = c.fetchone()
# #     if user:
# #         c.execute("UPDATE users SET is_logged_in=1 WHERE id=?", (user[0],))
# #         conn.commit()
# #     conn.close()
# #     return user


# # def login_in_session(user):
# #     import streamlit as st

# #     st.session_state.logged_in = True
# #     st.session_state.user = {"id": user[0], "email": user[1], "role": user[3]}


# # def logout_session():
# #     import streamlit as st
# #     import sqlite3

# #     if st.session_state.get("user"):
# #         user_id = st.session_state.user["id"]  # Use dictionary key
# #         conn = sqlite3.connect(DB_NAME)
# #         c = conn.cursor()
# #         c.execute("UPDATE users SET is_logged_in=0 WHERE id=?", (user_id,))
# #         conn.commit()
# #         conn.close()
# #     st.session_state.logged_in = False
# #     st.session_state.user = None


# import sqlite3
# import streamlit as st

# DB_NAME = "student.db"


# # ----------------- DB SETUP -----------------
# def create_users_table():
#     conn = sqlite3.connect(DB_NAME)
#     c = conn.cursor()
#     c.execute(
#         """
#         CREATE TABLE IF NOT EXISTS users (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             email TEXT UNIQUE,
#             password TEXT,
#             role TEXT,
#             is_logged_in INTEGER DEFAULT 0
#         )
#         """
#     )
#     conn.commit()
#     conn.close()


# # ----------------- LOGIN -----------------
# def login_user(email, password, role):
#     conn = sqlite3.connect(DB_NAME)
#     c = conn.cursor()
#     c.execute(
#         "SELECT * FROM users WHERE email=? AND password=? AND role=?",
#         (email, password, role),
#     )
#     user = c.fetchone()
#     if user:
#         c.execute("UPDATE users SET is_logged_in=1 WHERE id=?", (user[0],))
#         conn.commit()
#     conn.close()
#     return user


# def login_in_session(user):
#     """
#     Initialize Streamlit session_state from user object.
#     Handles both dict (from signup) and tuple (from DB query).
#     """
#     if isinstance(user, dict):
#         st.session_state.logged_in = True
#         st.session_state.user = {
#             "id": user["id"],
#             "email": user["email"],
#             "role": user["role"],
#         }
#     elif isinstance(user, tuple):
#         st.session_state.logged_in = True
#         st.session_state.user = {"id": user[0], "email": user[1], "role": user[3]}
#     else:
#         st.error("❌ Invalid user data format")


# # ----------------- SIGNUP -----------------
# def signup_user(email, password, role):
#     conn = sqlite3.connect(DB_NAME)
#     c = conn.cursor()
#     try:
#         c.execute(
#             "INSERT INTO users (email, password, role) VALUES (?, ?, ?)",
#             (email, password, role),
#         )
#         conn.commit()
#         user_id = c.lastrowid
#         conn.close()
#         return {"id": user_id, "email": email, "role": role}
#     except sqlite3.IntegrityError:
#         conn.close()
#         return None  # Email already exists


# # ----------------- LOGOUT -----------------
# def logout_session():
#     if st.session_state.get("user"):
#         user_id = st.session_state.user["id"]
#         conn = sqlite3.connect(DB_NAME)
#         c = conn.cursor()
#         c.execute("UPDATE users SET is_logged_in=0 WHERE id=?", (user_id,))
#         conn.commit()
#         conn.close()
#     st.session_state.logged_in = False
#     st.session_state.user = None


# # ----------------- PERSISTENT LOGIN -----------------
# def persistent_login():
#     conn = sqlite3.connect(DB_NAME)
#     c = conn.cursor()
#     c.execute("SELECT * FROM users WHERE is_logged_in=1")
#     user = c.fetchone()
#     conn.close()
#     if user:
#         login_in_session(user)
import sqlite3
import streamlit as st

DB_NAME = "student.db"


# ----------------- DB SETUP -----------------
def create_users_table():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            password TEXT,
            role TEXT,
            is_logged_in INTEGER DEFAULT 0
        )
        """
    )
    conn.commit()
    conn.close()


# ----------------- LOGIN -----------------
def login_user(email, password, role):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "SELECT * FROM users WHERE email=? AND password=? AND role=?",
        (email, password, role),
    )
    user = c.fetchone()
    conn.close()
    return user


def login_in_session(user):
    """Initialize Streamlit session_state from user object."""
    if isinstance(user, dict):
        st.session_state.logged_in = True
        st.session_state.user = {
            "id": user["id"],
            "email": user["email"],
            "role": user["role"],
        }
    elif isinstance(user, tuple):
        st.session_state.logged_in = True
        st.session_state.user = {"id": user[0], "email": user[1], "role": user[3]}
    else:
        st.error("❌ Invalid user data format")


# ----------------- SIGNUP -----------------
def signup_user(email, password, role):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO users (email, password, role) VALUES (?, ?, ?)",
            (email, password, role),
        )
        conn.commit()
        user_id = c.lastrowid
        conn.close()
        return {"id": user_id, "email": email, "role": role}
    except sqlite3.IntegrityError:
        conn.close()
        return None  # Email already exists


# ----------------- LOGOUT -----------------
def logout_session():
    if st.session_state.get("user"):
        user_id = st.session_state.user["id"]
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("UPDATE users SET is_logged_in=0 WHERE id=?", (user_id,))
        conn.commit()
        conn.close()
    st.session_state.logged_in = False
    st.session_state.user = None


# ----------------- PERSISTENT LOGIN -----------------
def persistent_login():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE is_logged_in=1")
    user = c.fetchone()
    conn.close()
    if user:
        login_in_session(user)
