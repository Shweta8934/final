#

import sqlite3
import json
from datetime import datetime, timedelta
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import re
from quiz_logic import quiz_component
from student_utils import get_student_weak_topics
from tutor_engine import ask_tutor_sync
from auth import logout_session
from auth import (
    create_users_table,
    login_user,
    signup_user,
    login_in_session,
    logout_session,
    persistent_login,
)
from student_db import (
    log_interaction,
    get_recent_interactions,
    set_feedback,
    init_db,
    get_gamification,
    update_gamification,
)
from file_handler import render_file_upload_section, get_file_analysis_prompt
from weekly_email import send_weekly_email, get_weekly_summary

# ----------------- DATABASE SETUP -----------------
DB_NAME = "student.db"


def get_feedback_summary(student_name, grade):
    """
    Returns feedback counts for Plotly chart.
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        """
        SELECT feedback, COUNT(*) 
        FROM interactions 
        WHERE student = ? AND grade = ?
        GROUP BY feedback
    """,
        (student_name, grade),
    )
    rows = c.fetchall()
    conn.close()
    return rows


def parse_date(date_str):
    """Helper to safely parse SQLite timestamp strings"""
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


import streamlit as st
from auth import (
    create_users_table,
    login_user,
    signup_user,
    login_in_session,
    logout_session,
    persistent_login,
)

# ----------------- INIT -----------------
create_users_table()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None

persistent_login()

# ----------------- LOGIN / SIGNUP UI -----------------
if not st.session_state.logged_in:
    st.title("🔐 Welcome to AI Tutor")
    action = st.radio("Choose action:", ["Login", "Signup"])
    role = st.selectbox("I am a:", ["Student", "Parent/Teacher"])
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if action == "Login" and st.button("Login"):
        user = login_user(email, password, role)
        if user:
            # Mark user as logged in
            conn = sqlite3.connect("student.db")
            c = conn.cursor()
            c.execute("UPDATE users SET is_logged_in=1 WHERE id=?", (user[0],))
            conn.commit()
            conn.close()

            login_in_session(user)
            st.success("✅ Login successful! Redirecting...")
            st.rerun()
        else:
            st.error(
                "❌ Invalid email, password, or role. Please check your credentials."
            )

    elif action == "Signup" and st.button("Signup"):
        user = signup_user(email, password, role)
        if user:
            st.success("✅ Signup successful! Please login to continue.")
            st.info("Go to Login and enter your credentials.")
        else:
            st.error("❌ Email already exists. Try logging in.")

    st.stop()  # Stop execution until login

# ----------------- DASHBOARD -----------------
# st.sidebar.title(f"Logged in as: {st.session_state.user['email']}")
if st.sidebar.button("Logout"):
    logout_session()
    st.success("✅ Logged out successfully! Reloading...")
    st.rerun()

user_role = st.session_state.user.get("role")


# ----------------- SUBJECT COMPLIANCE -----------------
def check_subject_compliance(question_text, selected_subject):
    """
    Validate that a question belongs to the selected subject.
    Only allow questions related to the selected subject.
    """
    q = question_text.lower()

    subject_keywords = {
        "Math": [
            "solve",
            "equation",
            "algebra",
            "geometry",
            "numbers",
            "calculate",
            "formula",
            "fraction",
            "integral",
            "derivative",
            "limit",
            "function",
            "graph",
            "polynomial",
            "quadratic",
            "linear",
            "logarithm",
            "trigonometry",
            "sine",
            "cosine",
            "tangent",
            "statistics",
            "probability",
            "mean",
            "median",
            "mode",
            "matrix",
            "vector",
            "coordinate",
            "angle",
            "triangle",
            "circle",
            "rectangle",
            "square",
            "area",
            "perimeter",
            "volume",
            "surface area",
            "pythagorean",
            "arithmetic",
            "multiplication",
            "division",
            "addition",
            "subtraction",
            "percentage",
            "ratio",
            "proportion",
            "decimal",
            "integer",
            "prime",
            "composite",
            "factor",
            "multiple",
            "gcd",
            "lcm",
            "inequality",
            "complex number",
            "+",
            "-",
            "*",
            "/",
            "=",
            "<",
            ">",
            "≤",
            "≥",
            "∑",
            "∏",
            "∫",
            "∆",
        ],
        "Science": [
            "force",
            "energy",
            "motion",
            "velocity",
            "acceleration",
            "gravity",
            "friction",
            "momentum",
            "pressure",
            "temperature",
            "heat",
            "light",
            "sound",
            "wave",
            "electricity",
            "magnetism",
            "current",
            "voltage",
            "resistance",
            "circuit",
            "newton",
            "law of motion",
            "first law",
            "second law",
            "third law",
            "atom",
            "molecule",
            "chemical",
            "reaction",
            "element",
            "compound",
            "mixture",
            "acid",
            "base",
            "ph",
            "bond",
            "periodic table",
            "cell",
            "organism",
            "dna",
            "rna",
            "gene",
            "photosynthesis",
            "ecosystem",
            "enzyme",
            "protein",
            "chromosome",
            "evolution",
            "bacteria",
            "virus",
            "earthquake",
            "volcano",
            "rock",
            "mineral",
            "fossil",
            "weather",
            "climate",
            "atmosphere",
        ],
        "English": [
            "grammar",
            "syntax",
            "sentence",
            "paragraph",
            "noun",
            "verb",
            "adjective",
            "adverb",
            "pronoun",
            "preposition",
            "conjunction",
            "interjection",
            "subject",
            "predicate",
            "object",
            "clause",
            "phrase",
            "tense",
            "punctuation",
            "comma",
            "period",
            "semicolon",
            "apostrophe",
            "quotation",
            "essay",
            "write",
            "writing",
            "composition",
            "introduction",
            "conclusion",
            "thesis",
            "argument",
            "narrative",
            "descriptive",
            "persuasive",
            "expository",
            "literature",
            "poem",
            "novel",
            "story",
            "character",
            "plot",
            "theme",
            "metaphor",
            "simile",
            "alliteration",
            "rhyme",
            "vocabulary",
            "synonym",
            "antonym",
        ],
        "General": [],
    }

    math_patterns = [
        r"\d+x",
        r"x[\+\-\*/]\d+",
        r"\d+x\^\d+",
        r"f\(x\)",
        r"[a-z]\^2",
        r"\d+/\d+",
        r"√\d+",
        r"\d+%",
    ]

    detected_subjects = []

    for subject, keywords in subject_keywords.items():
        if subject == "General":
            continue
        for kw in keywords:
            if kw in q:
                detected_subjects.append(subject)

    for pat in math_patterns:
        if re.search(pat, question_text):
            detected_subjects.append("Math")

    detected_subjects = list(set(detected_subjects))

    if selected_subject == "General":
        return True, detected_subjects

    if selected_subject in detected_subjects:
        return True, detected_subjects

    return False, detected_subjects


# ----------------- STREAMLIT SETUP -----------------
st.set_page_config(layout="wide", page_title="AI Tutor Prototype")

st.sidebar.title("AI Tutor Prototype")
role = st.sidebar.selectbox("Mode", ["Student", "Teacher / Parent"])
student_name = st.sidebar.text_input("Student name", "Alex")
grade = st.sidebar.selectbox("Grade", ["Grade 6", "Grade 7", "Grade 8"])
subject = st.sidebar.selectbox("Subject", ["Math", "Science", "English", "General"])

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.title("📚 AI Tutor")


# ----------------- STUDENT VIEW -----------------

if user_role == "Student":
    st.subheader(f"Student: {student_name} | {grade} | {subject}")

    subject_guidance = {
        "Math": "Ask questions about equations, geometry, algebra, calculus, statistics, or any mathematical concepts.",
        "Science": "Ask questions about physics, chemistry, biology, earth science, or scientific experiments.",
        "English": "Ask questions about grammar, literature, writing, vocabulary, or language skills.",
        "General": "You can ask questions from any subject - Math, Science, English, or general topics.",
    }

    st.info(f"📝 **{subject} Mode**: {subject_guidance.get(subject, '')}")

    extracted_text, file_info, question = render_file_upload_section(subject)

    combined_question = ""
    if extracted_text and question.strip():
        combined_question = f"""I have uploaded a file with the following content:

{extracted_text}

My specific question about this content is:
{question.strip()}"""
    elif extracted_text and not question.strip():
        combined_question = f"""I have uploaded a file with the following content:

{extracted_text}

Please analyze this content and provide insights, explanations, or answer any questions you think might be relevant to this material."""
    elif question.strip() and not extracted_text:
        combined_question = question.strip()

    if st.button("Send", type="primary"):
        if not combined_question:
            st.warning("Please type a question or upload a file.")
        else:
            analysis_text = combined_question
            if extracted_text:
                is_compliant = True
                detected_subjects = [subject]
            else:
                is_compliant, detected_subjects = check_subject_compliance(
                    analysis_text, subject
                )

            if not is_compliant:
                st.error(f"🚫 **Question Not Allowed!**")
                if detected_subjects and detected_subjects != ["Unknown/General"]:
                    other_subjects = [s for s in detected_subjects if s != subject]
                    if other_subjects:
                        st.warning(
                            f"Your question is about: **{', '.join(other_subjects)}**"
                        )
                        st.error(
                            f"You are in **{subject}** mode. Only **{subject}** questions are allowed!"
                        )
                    else:
                        st.warning(
                            f"Your question contains multiple subjects including **{', '.join(detected_subjects)}**"
                        )
                        st.error(
                            f"You are in **{subject}** mode. Only pure **{subject}** questions are allowed!"
                        )
                else:
                    st.warning(
                        "Your question doesn't appear to be clearly about any specific subject."
                    )
                    st.error(
                        f"You are in **{subject}** mode. Only **{subject}** questions are allowed!"
                    )
            else:
                placeholder = st.empty()
                with placeholder.container():
                    if extracted_text:
                        st.info("🤔 Analyzing your file and question...")
                    else:
                        st.info("🤔 Tutor is thinking...")

                try:
                    answer_text, hints, resources_json = ask_tutor_sync(
                        combined_question, subject, grade, student_name
                    )
                    resources = json.loads(resources_json) if resources_json else []

                    with placeholder.container():
                        if extracted_text:
                            st.success(
                                "✅ Here's the analysis of your file and answer to your question:"
                            )
                        else:
                            st.success("✅ Here's your answer:")

                        st.write(answer_text)

                        if hints:
                            st.markdown("### 💡 Hints / Next Steps")
                            for i, h in enumerate(hints, 1):
                                st.write(f"{i}. {h}")

                        if resources:
                            st.markdown("### 📚 Recommended Resources")
                            for r in resources:
                                st.write(
                                    f"- [{r.get('title','Resource')}]({r.get('link','#')})"
                                )

                    inter_id = log_interaction(
                        student_name,
                        grade,
                        subject,
                        combined_question,
                        answer_text,
                        json.dumps(resources),
                    )

                    st.session_state.chat_history.insert(
                        0, {"id": inter_id, "q": combined_question, "a": answer_text}
                    )

                except Exception as e:
                    st.error(
                        f"❌ An error occurred while processing your question: {str(e)}"
                    )
                    st.info(
                        "Please try again or contact support if the problem persists."
                    )

    # ----------------- Recent interactions -----------------
    st.markdown("---")
    st.markdown("### 📊 Recent Interactions")
    with st.spinner("Loading recent interactions..."):
        recent = get_recent_interactions(student_name, grade, limit=10)
    if not recent:
        st.info("No previous interactions yet. Ask your first question above!")
    else:
        for row in recent:
            inter_id, q, a, resources, feedback, feedback_comment, created_at = row[:7]
            with st.expander(
                f"🕒 {created_at} — Q: {q[:60]}{'...' if len(q) > 60 else ''}"
            ):
                st.markdown("**Answer:**")
                st.write(a)

                try:
                    res_list = json.loads(resources) if resources else []
                    if res_list:
                        st.markdown("**📚 Resources:**")
                        for r in res_list:
                            st.write(
                                f"- [{r.get('title','Resource')}]({r.get('link','#')})"
                            )
                except Exception:
                    pass

                st.markdown("**👍👎 Feedback:**")
                with st.form(key=f"feedback_form_{inter_id}"):
                    feedback_val = st.radio(
                        "Was this answer helpful?",
                        ("👍 Helpful", "👎 Not Helpful", "No Feedback"),
                        index=2 if feedback == 0 else 0 if feedback == 1 else 1,
                        key=f"radio_{inter_id}",
                    )
                    comment = st.text_input(
                        "Optional comment",
                        value=feedback_comment if feedback_comment else "",
                        key=f"comment_{inter_id}",
                    )
                    if st.form_submit_button("Submit Feedback"):
                        feedback_score = (
                            1
                            if feedback_val == "👍 Helpful"
                            else -1 if feedback_val == "👎 Not Helpful" else 0
                        )
                        set_feedback(inter_id, feedback_score, comment)
                        st.success("✅ Feedback saved!")

    # ----------------- Quiz Section -----------------
    # Call the quiz component
    quiz_component()
    # get_quiz_questions(grade=grade, subject=subject)

    # ----------------- Gamification -----------------
    update_gamification(student_name, xp=0)
    gamification = get_gamification(student_name)
    badge_display = (
        ", ".join(gamification["badges"]) if gamification["badges"] else "No badges yet"
    )

    st.info(
        f"🏆 XP: {gamification['xp']} | "
        f"🔥 Current Streak: {gamification['streak']} days | "
        f"🎖 Badge(s): {badge_display}"
    )
    st.progress(min(gamification["xp"], 100) / 100)

    # ----------------- Progress charts -----------------
    st.markdown("### 📈 Your Progress Overview")
    df_student = pd.DataFrame(
        recent,
        columns=[
            "id",
            "question",
            "answer",
            "resources",
            "feedback",
            "comment",
            "created_at",
        ],
    )

    if not df_student.empty:
        feedback_counts = (
            df_student.groupby("feedback").size().reset_index(name="count")
        )
        feedback_counts["feedback_text"] = feedback_counts["feedback"].replace(
            {1: "👍 Helpful", 0: "😐 Medium", -1: "👎 Not Helpful"}
        )
        fig_student = px.pie(
            feedback_counts,
            names="feedback_text",
            values="count",
            title="Feedback Distribution for Your Questions",
            hole=0.4,
        )
        st.plotly_chart(fig_student, use_container_width=True)

        df_student["created_at"] = pd.to_datetime(df_student["created_at"])
        df_student_sorted = (
            df_student.groupby(df_student["created_at"].dt.date)
            .size()
            .reset_index(name="Questions")
        )
        fig_bar = px.bar(
            df_student_sorted,
            x="created_at",
            y="Questions",
            title="Questions Asked Over Time",
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    weak_topics, topic_details = get_student_weak_topics(student_name, grade)
    st.markdown("### ⚠️ Weak Topics & Suggested Practice")
    if weak_topics:
        st.warning(f"You are struggling with: {', '.join(weak_topics)}")
        st.info("💡 Suggested: Review these topics with extra practice and resources.")
        for topic in weak_topics:
            st.markdown(f"#### 🔹 {topic} Examples & Resources")
            for ex in topic_details[topic]:
                st.markdown(f"- ❌ Q: {ex['question'][:80]}...")
                st.markdown(f"  ✅ A: {ex['answer'][:80]}...")
                if ex["resources"]:
                    st.markdown("  📚 Resources:")
                    for r in ex["resources"]:
                        st.markdown(
                            f"    - [{r.get('title','Resource')}]({r.get('link','#')})"
                        )
    else:
        st.success("🎉 No weak topics detected. Keep up the good work!")

# ----------------- TEACHER / PARENT DASHBOARD -----------------
elif user_role == "Parent/Teacher":
    st.subheader("👨‍🏫 Teacher / Parent Dashboard")

    # Initialize variables
    selected_student = None
    selected_grade = None

    # --- Fetch all students ---
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT DISTINCT student, grade FROM interactions ORDER BY student")
    all_students = c.fetchall()
    conn.close()

    if all_students:
        # Select student + grade
        student_grade_options = [f"{s[0]} (Grade {s[1]})" for s in all_students]
        selected = st.selectbox("Select a Student", student_grade_options)
        selected_student = selected.split(" (Grade ")[0]
        selected_grade = selected.split(" (Grade ")[1][:-1]

        st.write(
            f"Viewing student: **{selected_student}** in **Grade {selected_grade}**"
        )
        # # ---------------- email sent ----------------

        if st.button("Send Weekly Email Summary to Parent"):
            if selected_student:
                try:
                    summary_df = get_weekly_summary(selected_student, selected_grade)
                    if summary_df is None or summary_df.empty:
                        st.warning(
                            f"No interactions found for {selected_student} this week."
                        )
                    else:
                        # Call the email function with the student name
                        send_weekly_email(selected_student)
                        st.success(
                            f"✅ Weekly email summary sent successfully for {selected_student}!"
                        )
                except Exception as e:
                    st.error(f"❌ Error sending email: {e}")
            else:
                st.warning("⚠️ Please select a student first.")

        # --- Activity by subject ---
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute(
            """
            SELECT subject, COUNT(*) 
            FROM interactions
            WHERE student = ? AND grade = ?
            GROUP BY subject
        """,
            (selected_student, selected_grade),
        )
        data = c.fetchall()
        conn.close()

        if data:
            df = pd.DataFrame(data, columns=["subject", "count"])
            df["count"] = df["count"].astype(int)
            fig = px.bar(
                df,
                x="subject",
                y="count",
                title=f"📊 {selected_student}'s Learning Activity by Subject",
                labels={"count": "Number of Questions", "subject": "Subject"},
                color="count",
                color_continuous_scale="Blues",
            )
            fig.update_layout(yaxis=dict(dtick=1))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📈 No interactions recorded for this student yet.")

        # --- Fetch recent interactions ---
        recent_interactions = get_recent_interactions(
            selected_student, selected_grade, limit=10
        )

        if recent_interactions:
            st.markdown("### 📝 Recent Interactions")
            for row in recent_interactions:
                inter_id, q, a, resources, feedback, feedback_comment, created_at = row[
                    :7
                ]
                with st.expander(
                    f"🕒 {created_at} — Q: {q[:60]}{'...' if len(q) > 60 else ''}"
                ):
                    st.markdown("**Answer:**")
                    st.write(a)

                    # Display resources
                    try:
                        res_list = json.loads(resources) if resources else []
                        if res_list:
                            st.markdown("**📚 Resources:**")
                            for r in res_list:
                                st.write(
                                    f"- [{r.get('title','Resource')}]({r.get('link','#')})"
                                )
                    except Exception:
                        pass

                    # Display student feedback (read-only)
                    feedback_mapping = {
                        1: "👍 Helpful",
                        -1: "👎 Not Helpful",
                        0: "No Feedback",
                    }
                    st.markdown("**👍👎 Feedback (by student):**")
                    st.write(f"{feedback_mapping.get(feedback, 'No Feedback')}")
                    if feedback_comment:
                        st.markdown(f"**Comment:** {feedback_comment}")

        else:
            st.info("📋 No recent interactions for this student.")

        # --- Feedback summary ---
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute(
            """
            SELECT feedback, COUNT(*)
            FROM interactions
            WHERE student = ? AND grade = ?
            GROUP BY feedback
        """,
            (selected_student, selected_grade),
        )
        feedback_data = c.fetchall()
        conn.close()

        if feedback_data:
            feedback_mapping = {1: "Helpful", -1: "Not Helpful", 0: "Neutral"}
            mapped_feedback = [
                (feedback_mapping.get(fb, "Unknown"), count)
                for fb, count in feedback_data
            ]

            df_feedback = pd.DataFrame(mapped_feedback, columns=["Feedback", "Count"])
            df_feedback["Count"] = df_feedback["Count"].astype(int)

            fig_fb = px.pie(
                df_feedback,
                names="Feedback",
                values="Count",
                title=f"📊 Feedback Summary for {selected_student}",
            )
            st.plotly_chart(fig_fb, use_container_width=True)
        else:
            st.info("📊 No feedback available for this student.")

        # --- Weak subjects display ---
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute(
            """
            SELECT subject, COUNT(*) as total,
                   SUM(CASE WHEN feedback = -1 THEN 1 ELSE 0 END) as wrong
            FROM interactions
            WHERE student = ? AND grade = ?
            GROUP BY subject
        """,
            (selected_student, selected_grade),
        )
        topics = c.fetchall()
        conn.close()

        weak_topics = [
            subj for subj, total, wrong in topics if total > 0 and (wrong / total) > 0.3
        ]
        st.markdown(
            f"### ⚠️ Weak Subjects: {', '.join(weak_topics) if weak_topics else 'None'}"
        )

    else:
        st.info("No student interactions available yet.")


else:
    st.error("❌ Unknown role. Please contact support.")

# # ----------------- Sidebar Notes -----------------
st.sidebar.markdown("---")
st.sidebar.markdown("**ℹ️ System Information**")
st.sidebar.success(" Using Enhanced AI Tutor Engine (GPT-4o-mini)")
st.sidebar.markdown("**🔧 Features:**")
st.sidebar.markdown("- Step-by-step explanations")
st.sidebar.markdown("- Learning hints & interactive questions")
st.sidebar.markdown("- Curated educational resources")
st.sidebar.markdown("- Progress tracking & adaptive difficulty")
st.sidebar.markdown("- Gamification placeholders (XP, badges, streaks)")
st.sidebar.markdown("- Persistent feedback (immediate + history)")
st.sidebar.markdown(
    "- Multimodal input placeholders (diagram/PDF OCR) - used internally by AI"
)
st.sidebar.markdown("- **🎯 Subject-specific question filtering**")


# # final code

# import sqlite3
# import json
# from datetime import datetime, timedelta
# import os
# import streamlit as st
# import pandas as pd
# import plotly.express as px
# import re
# from quiz_logic import quiz_component
# from student_utils import get_student_weak_topics
# from tutor_engine import ask_tutor_sync
# from student_db import (
#     log_interaction,
#     get_recent_interactions,
#     set_feedback,
#     init_db,
#     get_gamification,
#     update_gamification,
# )
# from file_handler import render_file_upload_section, get_file_analysis_prompt
# from weekly_email import send_weekly_email, get_weekly_summary

# # ----------------- DATABASE SETUP -----------------
# DB_NAME = "student.db"


# def get_feedback_summary(student_name, grade):
#     """
#     Returns feedback counts for Plotly chart.
#     """
#     conn = sqlite3.connect(DB_NAME)
#     c = conn.cursor()
#     c.execute(
#         """
#         SELECT feedback, COUNT(*)
#         FROM interactions
#         WHERE student = ? AND grade = ?
#         GROUP BY feedback
#     """,
#         (student_name, grade),
#     )
#     rows = c.fetchall()
#     conn.close()
#     return rows


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


# init_db()


# # ----------------- SUBJECT COMPLIANCE -----------------
# def check_subject_compliance(question_text, selected_subject):
#     """
#     Validate that a question belongs to the selected subject.
#     Only allow questions related to the selected subject.
#     """
#     q = question_text.lower()

#     subject_keywords = {
#         "Math": [
#             "solve",
#             "equation",
#             "algebra",
#             "geometry",
#             "numbers",
#             "calculate",
#             "formula",
#             "fraction",
#             "integral",
#             "derivative",
#             "limit",
#             "function",
#             "graph",
#             "polynomial",
#             "quadratic",
#             "linear",
#             "logarithm",
#             "trigonometry",
#             "sine",
#             "cosine",
#             "tangent",
#             "statistics",
#             "probability",
#             "mean",
#             "median",
#             "mode",
#             "matrix",
#             "vector",
#             "coordinate",
#             "angle",
#             "triangle",
#             "circle",
#             "rectangle",
#             "square",
#             "area",
#             "perimeter",
#             "volume",
#             "surface area",
#             "pythagorean",
#             "arithmetic",
#             "multiplication",
#             "division",
#             "addition",
#             "subtraction",
#             "percentage",
#             "ratio",
#             "proportion",
#             "decimal",
#             "integer",
#             "prime",
#             "composite",
#             "factor",
#             "multiple",
#             "gcd",
#             "lcm",
#             "inequality",
#             "complex number",
#             "+",
#             "-",
#             "*",
#             "/",
#             "=",
#             "<",
#             ">",
#             "≤",
#             "≥",
#             "∑",
#             "∏",
#             "∫",
#             "∆",
#         ],
#         "Science": [
#             "force",
#             "energy",
#             "motion",
#             "velocity",
#             "acceleration",
#             "gravity",
#             "friction",
#             "momentum",
#             "pressure",
#             "temperature",
#             "heat",
#             "light",
#             "sound",
#             "wave",
#             "electricity",
#             "magnetism",
#             "current",
#             "voltage",
#             "resistance",
#             "circuit",
#             "newton",
#             "law of motion",
#             "first law",
#             "second law",
#             "third law",
#             "atom",
#             "molecule",
#             "chemical",
#             "reaction",
#             "element",
#             "compound",
#             "mixture",
#             "acid",
#             "base",
#             "ph",
#             "bond",
#             "periodic table",
#             "cell",
#             "organism",
#             "dna",
#             "rna",
#             "gene",
#             "photosynthesis",
#             "ecosystem",
#             "enzyme",
#             "protein",
#             "chromosome",
#             "evolution",
#             "bacteria",
#             "virus",
#             "earthquake",
#             "volcano",
#             "rock",
#             "mineral",
#             "fossil",
#             "weather",
#             "climate",
#             "atmosphere",
#         ],
#         "English": [
#             "grammar",
#             "syntax",
#             "sentence",
#             "paragraph",
#             "noun",
#             "verb",
#             "adjective",
#             "adverb",
#             "pronoun",
#             "preposition",
#             "conjunction",
#             "interjection",
#             "subject",
#             "predicate",
#             "object",
#             "clause",
#             "phrase",
#             "tense",
#             "punctuation",
#             "comma",
#             "period",
#             "semicolon",
#             "apostrophe",
#             "quotation",
#             "essay",
#             "write",
#             "writing",
#             "composition",
#             "introduction",
#             "conclusion",
#             "thesis",
#             "argument",
#             "narrative",
#             "descriptive",
#             "persuasive",
#             "expository",
#             "literature",
#             "poem",
#             "novel",
#             "story",
#             "character",
#             "plot",
#             "theme",
#             "metaphor",
#             "simile",
#             "alliteration",
#             "rhyme",
#             "vocabulary",
#             "synonym",
#             "antonym",
#         ],
#         "General": [],
#     }

#     math_patterns = [
#         r"\d+x",
#         r"x[\+\-\*/]\d+",
#         r"\d+x\^\d+",
#         r"f\(x\)",
#         r"[a-z]\^2",
#         r"\d+/\d+",
#         r"√\d+",
#         r"\d+%",
#     ]

#     detected_subjects = []

#     for subject, keywords in subject_keywords.items():
#         if subject == "General":
#             continue
#         for kw in keywords:
#             if kw in q:
#                 detected_subjects.append(subject)

#     for pat in math_patterns:
#         if re.search(pat, question_text):
#             detected_subjects.append("Math")

#     detected_subjects = list(set(detected_subjects))

#     if selected_subject == "General":
#         return True, detected_subjects

#     if selected_subject in detected_subjects:
#         return True, detected_subjects

#     return False, detected_subjects


# # ----------------- STREAMLIT SETUP -----------------
# st.set_page_config(layout="wide", page_title="AI Tutor Prototype")

# st.sidebar.title("AI Tutor Prototype")
# role = st.sidebar.selectbox("Mode", ["Student", "Teacher / Parent"])
# student_name = st.sidebar.text_input("Student name", "Alex")
# grade = st.sidebar.selectbox("Grade", ["Grade 6", "Grade 7", "Grade 8"])
# subject = st.sidebar.selectbox("Subject", ["Math", "Science", "English", "General"])

# if "chat_history" not in st.session_state:
#     st.session_state.chat_history = []

# st.title("📚 AI Tutor")

# # ----------------- STUDENT VIEW -----------------
# if role == "Student":
#     st.subheader(f"Student: {student_name} | {grade} | {subject}")

#     subject_guidance = {
#         "Math": "Ask questions about equations, geometry, algebra, calculus, statistics, or any mathematical concepts.",
#         "Science": "Ask questions about physics, chemistry, biology, earth science, or scientific experiments.",
#         "English": "Ask questions about grammar, literature, writing, vocabulary, or language skills.",
#         "General": "You can ask questions from any subject - Math, Science, English, or general topics.",
#     }

#     st.info(f"📝 **{subject} Mode**: {subject_guidance.get(subject, '')}")

#     extracted_text, file_info, question = render_file_upload_section(subject)

#     combined_question = ""
#     if extracted_text and question.strip():
#         combined_question = f"""I have uploaded a file with the following content:

# {extracted_text}

# My specific question about this content is:
# {question.strip()}"""
#     elif extracted_text and not question.strip():
#         combined_question = f"""I have uploaded a file with the following content:

# {extracted_text}

# Please analyze this content and provide insights, explanations, or answer any questions you think might be relevant to this material."""
#     elif question.strip() and not extracted_text:
#         combined_question = question.strip()

#     if st.button("Send", type="primary"):
#         if not combined_question:
#             st.warning("Please type a question or upload a file.")
#         else:
#             analysis_text = combined_question
#             if extracted_text:
#                 is_compliant = True
#                 detected_subjects = [subject]
#             else:
#                 is_compliant, detected_subjects = check_subject_compliance(
#                     analysis_text, subject
#                 )

#             if not is_compliant:
#                 st.error(f"🚫 **Question Not Allowed!**")
#                 if detected_subjects and detected_subjects != ["Unknown/General"]:
#                     other_subjects = [s for s in detected_subjects if s != subject]
#                     if other_subjects:
#                         st.warning(
#                             f"Your question is about: **{', '.join(other_subjects)}**"
#                         )
#                         st.error(
#                             f"You are in **{subject}** mode. Only **{subject}** questions are allowed!"
#                         )
#                     else:
#                         st.warning(
#                             f"Your question contains multiple subjects including **{', '.join(detected_subjects)}**"
#                         )
#                         st.error(
#                             f"You are in **{subject}** mode. Only pure **{subject}** questions are allowed!"
#                         )
#                 else:
#                     st.warning(
#                         "Your question doesn't appear to be clearly about any specific subject."
#                     )
#                     st.error(
#                         f"You are in **{subject}** mode. Only **{subject}** questions are allowed!"
#                     )
#             else:
#                 placeholder = st.empty()
#                 with placeholder.container():
#                     if extracted_text:
#                         st.info("🤔 Analyzing your file and question...")
#                     else:
#                         st.info("🤔 Tutor is thinking...")

#                 try:
#                     answer_text, hints, resources_json = ask_tutor_sync(
#                         combined_question, subject, grade, student_name
#                     )
#                     resources = json.loads(resources_json) if resources_json else []

#                     with placeholder.container():
#                         if extracted_text:
#                             st.success(
#                                 "✅ Here's the analysis of your file and answer to your question:"
#                             )
#                         else:
#                             st.success("✅ Here's your answer:")

#                         st.write(answer_text)

#                         if hints:
#                             st.markdown("### 💡 Hints / Next Steps")
#                             for i, h in enumerate(hints, 1):
#                                 st.write(f"{i}. {h}")

#                         if resources:
#                             st.markdown("### 📚 Recommended Resources")
#                             for r in resources:
#                                 st.write(
#                                     f"- [{r.get('title','Resource')}]({r.get('link','#')})"
#                                 )

#                     inter_id = log_interaction(
#                         student_name,
#                         grade,
#                         subject,
#                         combined_question,
#                         answer_text,
#                         json.dumps(resources),
#                     )

#                     st.session_state.chat_history.insert(
#                         0, {"id": inter_id, "q": combined_question, "a": answer_text}
#                     )

#                 except Exception as e:
#                     st.error(
#                         f"❌ An error occurred while processing your question: {str(e)}"
#                     )
#                     st.info(
#                         "Please try again or contact support if the problem persists."
#                     )

#     # ----------------- Recent interactions -----------------
#     st.markdown("---")
#     st.markdown("### 📊 Recent Interactions")
#     with st.spinner("Loading recent interactions..."):
#         recent = get_recent_interactions(student_name, grade, limit=10)
#     if not recent:
#         st.info("No previous interactions yet. Ask your first question above!")
#     else:
#         for row in recent:
#             inter_id, q, a, resources, feedback, feedback_comment, created_at = row[:7]
#             with st.expander(
#                 f"🕒 {created_at} — Q: {q[:60]}{'...' if len(q) > 60 else ''}"
#             ):
#                 st.markdown("**Answer:**")
#                 st.write(a)

#                 try:
#                     res_list = json.loads(resources) if resources else []
#                     if res_list:
#                         st.markdown("**📚 Resources:**")
#                         for r in res_list:
#                             st.write(
#                                 f"- [{r.get('title','Resource')}]({r.get('link','#')})"
#                             )
#                 except Exception:
#                     pass

#                 st.markdown("**👍👎 Feedback:**")
#                 with st.form(key=f"feedback_form_{inter_id}"):
#                     feedback_val = st.radio(
#                         "Was this answer helpful?",
#                         ("👍 Helpful", "👎 Not Helpful", "No Feedback"),
#                         index=2 if feedback == 0 else 0 if feedback == 1 else 1,
#                         key=f"radio_{inter_id}",
#                     )
#                     comment = st.text_input(
#                         "Optional comment",
#                         value=feedback_comment if feedback_comment else "",
#                         key=f"comment_{inter_id}",
#                     )
#                     if st.form_submit_button("Submit Feedback"):
#                         feedback_score = (
#                             1
#                             if feedback_val == "👍 Helpful"
#                             else -1 if feedback_val == "👎 Not Helpful" else 0
#                         )
#                         set_feedback(inter_id, feedback_score, comment)
#                         st.success("✅ Feedback saved!")

#     # ----------------- Quiz Section -----------------
#     quiz_component(grade=grade, subject=subject)

#     # ----------------- Gamification -----------------
#     update_gamification(student_name, xp=0)
#     gamification = get_gamification(student_name)
#     badge_display = (
#         ", ".join(gamification["badges"]) if gamification["badges"] else "No badges yet"
#     )

#     st.info(
#         f"🏆 XP: {gamification['xp']} | "
#         f"🔥 Current Streak: {gamification['streak']} days | "
#         f"🎖 Badge(s): {badge_display}"
#     )
#     st.progress(min(gamification["xp"], 100) / 100)

#     # ----------------- Progress charts -----------------
#     st.markdown("### 📈 Your Progress Overview")
#     df_student = pd.DataFrame(
#         recent,
#         columns=[
#             "id",
#             "question",
#             "answer",
#             "resources",
#             "feedback",
#             "comment",
#             "created_at",
#         ],
#     )

#     if not df_student.empty:
#         feedback_counts = (
#             df_student.groupby("feedback").size().reset_index(name="count")
#         )
#         feedback_counts["feedback_text"] = feedback_counts["feedback"].replace(
#             {1: "👍 Helpful", 0: "😐 Medium", -1: "👎 Not Helpful"}
#         )
#         fig_student = px.pie(
#             feedback_counts,
#             names="feedback_text",
#             values="count",
#             title="Feedback Distribution for Your Questions",
#             hole=0.4,
#         )
#         st.plotly_chart(fig_student, use_container_width=True)

#         df_student["created_at"] = pd.to_datetime(df_student["created_at"])
#         df_student_sorted = (
#             df_student.groupby(df_student["created_at"].dt.date)
#             .size()
#             .reset_index(name="Questions")
#         )
#         fig_bar = px.bar(
#             df_student_sorted,
#             x="created_at",
#             y="Questions",
#             title="Questions Asked Over Time",
#         )
#         st.plotly_chart(fig_bar, use_container_width=True)

#     weak_topics, topic_details = get_student_weak_topics(student_name, grade)
#     st.markdown("### ⚠️ Weak Topics & Suggested Practice")
#     if weak_topics:
#         st.warning(f"You are struggling with: {', '.join(weak_topics)}")
#         st.info("💡 Suggested: Review these topics with extra practice and resources.")
#         for topic in weak_topics:
#             st.markdown(f"#### 🔹 {topic} Examples & Resources")
#             for ex in topic_details[topic]:
#                 st.markdown(f"- ❌ Q: {ex['question'][:80]}...")
#                 st.markdown(f"  ✅ A: {ex['answer'][:80]}...")
#                 if ex["resources"]:
#                     st.markdown("  📚 Resources:")
#                     for r in ex["resources"]:
#                         st.markdown(
#                             f"    - [{r.get('title','Resource')}]({r.get('link','#')})"
#                         )
#     else:
#         st.success("🎉 No weak topics detected. Keep up the good work!")

# # ----------------- TEACHER / PARENT DASHBOARD -----------------
# else:
#     st.subheader("👨‍🏫 Teacher / Parent Dashboard")

#     # Initialize variables
#     selected_student = None
#     selected_grade = None

#     # --- Fetch all students ---
#     conn = sqlite3.connect(DB_NAME)
#     c = conn.cursor()
#     c.execute("SELECT DISTINCT student, grade FROM interactions ORDER BY student")
#     all_students = c.fetchall()
#     conn.close()

#     if all_students:
#         # Select student + grade
#         student_grade_options = [f"{s[0]} (Grade {s[1]})" for s in all_students]
#         selected = st.selectbox("Select a Student", student_grade_options)
#         selected_student = selected.split(" (Grade ")[0]
#         selected_grade = selected.split(" (Grade ")[1][:-1]

#         st.write(
#             f"Viewing student: **{selected_student}** in **Grade {selected_grade}**"
#         )
#         # ---------------- email sent ----------------
#         if st.button("Send Weekly Email Summary to Parent"):
#             if selected_student:
#                 try:
#                     summary_df = get_weekly_summary(
#                         selected_student, selected_grade
#                     )  # likely returns a DataFrame
#                     if summary_df.empty:
#                         st.warning(
#                             f"No interactions found for {selected_student} this week."
#                         )
#                     else:
#                         # Convert DataFrame to a readable string (or HTML)
#                         summary_str = summary_df.to_string(index=False)
#                         send_weekly_email(summary_str)
#                         st.success(
#                             f"✅ Weekly email summary sent successfully for {selected_student}!"
#                         )
#                 except Exception as e:
#                     st.error(f"❌ Error sending email: {e}")
#             else:
#                 st.warning("⚠️ Please select a student first.")

#         # --- Activity by subject ---
#         conn = sqlite3.connect(DB_NAME)
#         c = conn.cursor()
#         c.execute(
#             """
#             SELECT subject, COUNT(*)
#             FROM interactions
#             WHERE student = ? AND grade = ?
#             GROUP BY subject
#         """,
#             (selected_student, selected_grade),
#         )
#         data = c.fetchall()
#         conn.close()

#         if data:
#             df = pd.DataFrame(data, columns=["subject", "count"])
#             df["count"] = df["count"].astype(int)
#             fig = px.bar(
#                 df,
#                 x="subject",
#                 y="count",
#                 title=f"📊 {selected_student}'s Learning Activity by Subject",
#                 labels={"count": "Number of Questions", "subject": "Subject"},
#                 color="count",
#                 color_continuous_scale="Blues",
#             )
#             fig.update_layout(yaxis=dict(dtick=1))
#             st.plotly_chart(fig, use_container_width=True)
#         else:
#             st.info("📈 No interactions recorded for this student yet.")

#         # --- Fetch recent interactions ---
#         recent_interactions = get_recent_interactions(
#             selected_student, selected_grade, limit=10
#         )

#         if recent_interactions:
#             st.markdown("### 📝 Recent Interactions")
#             for row in recent_interactions:
#                 inter_id, q, a, resources, feedback, feedback_comment, created_at = row[
#                     :7
#                 ]
#                 with st.expander(
#                     f"🕒 {created_at} — Q: {q[:60]}{'...' if len(q) > 60 else ''}"
#                 ):
#                     st.markdown("**Answer:**")
#                     st.write(a)

#                     try:
#                         res_list = json.loads(resources) if resources else []
#                         if res_list:
#                             st.markdown("**📚 Resources:**")
#                             for r in res_list:
#                                 st.write(
#                                     f"- [{r.get('title','Resource')}]({r.get('link','#')})"
#                                 )
#                     except Exception:
#                         pass

#                     st.markdown("**👍👎 Feedback:**")
#                     with st.form(key=f"feedback_form_{inter_id}"):
#                         feedback_val = st.radio(
#                             "Was this answer helpful?",
#                             ("👍 Helpful", "👎 Not Helpful", "No Feedback"),
#                             index=2 if feedback == 0 else 0 if feedback == 1 else 1,
#                             key=f"radio_{inter_id}",
#                         )
#                         comment = st.text_input(
#                             "Optional comment",
#                             value=feedback_comment if feedback_comment else "",
#                             key=f"comment_{inter_id}",
#                         )
#                         if st.form_submit_button("Submit Feedback"):
#                             feedback_score = (
#                                 1
#                                 if feedback_val == "👍 Helpful"
#                                 else -1 if feedback_val == "👎 Not Helpful" else 0
#                             )
#                             set_feedback(inter_id, feedback_score, comment)
#                             st.success("✅ Feedback saved!")

#         else:
#             st.info("📋 No recent interactions for this student.")

#         # --- Feedback summary ---
#         conn = sqlite3.connect(DB_NAME)
#         c = conn.cursor()
#         c.execute(
#             """
#             SELECT feedback, COUNT(*)
#             FROM interactions
#             WHERE student = ? AND grade = ?
#             GROUP BY feedback
#         """,
#             (selected_student, selected_grade),
#         )
#         feedback_data = c.fetchall()
#         conn.close()

#         if feedback_data:
#             feedback_mapping = {1: "Helpful", -1: "Not Helpful", 0: "Neutral"}
#             mapped_feedback = [
#                 (feedback_mapping.get(fb, "Unknown"), count)
#                 for fb, count in feedback_data
#             ]

#             df_feedback = pd.DataFrame(mapped_feedback, columns=["Feedback", "Count"])
#             df_feedback["Count"] = df_feedback["Count"].astype(int)

#             fig_fb = px.pie(
#                 df_feedback,
#                 names="Feedback",
#                 values="Count",
#                 title=f"📊 Feedback Summary for {selected_student}",
#             )
#             st.plotly_chart(fig_fb, use_container_width=True)
#         else:
#             st.info("📊 No feedback available for this student.")

#         # --- Weak subjects display ---
#         conn = sqlite3.connect(DB_NAME)
#         c = conn.cursor()
#         c.execute(
#             """
#             SELECT subject, COUNT(*) as total,
#                    SUM(CASE WHEN feedback = -1 THEN 1 ELSE 0 END) as wrong
#             FROM interactions
#             WHERE student = ? AND grade = ?
#             GROUP BY subject
#         """,
#             (selected_student, selected_grade),
#         )
#         topics = c.fetchall()
#         conn.close()

#         weak_topics = [
#             subj for subj, total, wrong in topics if total > 0 and (wrong / total) > 0.3
#         ]
#         st.markdown(
#             f"### ⚠️ Weak Subjects: {', '.join(weak_topics) if weak_topics else 'None'}"
#         )

#     else:
#         st.info("No student interactions available yet.")


# # # ----------------- Sidebar Notes -----------------
# st.sidebar.markdown("---")
# st.sidebar.markdown("**ℹ️ System Information**")
# st.sidebar.success(" Using Enhanced AI Tutor Engine (GPT-4o-mini)")
# st.sidebar.markdown("**🔧 Features:**")
# st.sidebar.markdown("- Step-by-step explanations")
# st.sidebar.markdown("- Learning hints & interactive questions")
# st.sidebar.markdown("- Curated educational resources")
# st.sidebar.markdown("- Progress tracking & adaptive difficulty")
# st.sidebar.markdown("- Gamification placeholders (XP, badges, streaks)")
# st.sidebar.markdown("- Persistent feedback (immediate + history)")
# st.sidebar.markdown(
#     "- Multimodal input placeholders (diagram/PDF OCR) - used internally by AI"
# )
# st.sidebar.markdown("- **🎯 Subject-specific question filtering**")
