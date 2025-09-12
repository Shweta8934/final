# weekly_email.py
import sqlite3
import pandas as pd
import yagmail
from datetime import datetime, timedelta

DB_NAME = "student.db"

# ----------------- CONFIGURATION -----------------
SMTP_EMAIL = "shweta.ladne.averybit@gmail.com"  # your email
SMTP_PASSWORD = "lesx zjdt asgs ugtv"  # Gmail app password recommended
PARENT_EMAILS = {
    "Alex": "shweta.ladne.averybit@example.com",
    # Add more students here
}


# ----------------- FETCH WEEKLY DATA -----------------
def get_weekly_summary(student_name, grade=None):
    """
    Fetch student's interactions in the past 7 days and summarize.
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    week_ago = datetime.now() - timedelta(days=7)

    if grade:
        c.execute(
            """
            SELECT subject, COUNT(*), 
                   SUM(CASE WHEN feedback = 1 THEN 1 ELSE 0 END) as helpful,
                   SUM(CASE WHEN feedback = -1 THEN 1 ELSE 0 END) as not_helpful
            FROM interactions
            WHERE student = ? AND grade = ? AND datetime(created_at) >= ?
            GROUP BY subject
        """,
            (student_name, grade, week_ago.strftime("%Y-%m-%d %H:%M:%S")),
        )
    else:
        c.execute(
            """
            SELECT subject, COUNT(*), 
                   SUM(CASE WHEN feedback = 1 THEN 1 ELSE 0 END) as helpful,
                   SUM(CASE WHEN feedback = -1 THEN 1 ELSE 0 END) as not_helpful
            FROM interactions
            WHERE student = ? AND datetime(created_at) >= ?
            GROUP BY subject
        """,
            (student_name, week_ago.strftime("%Y-%m-%d %H:%M:%S")),
        )

    rows = c.fetchall()
    conn.close()

    if not rows:
        return None

    return pd.DataFrame(
        rows, columns=["Subject", "Questions Asked", "Helpful Answers", "Not Helpful"]
    )


# ----------------- SEND EMAIL -----------------
# def send_weekly_email(student_name):
#     df = get_weekly_summary(student_name)
#     if df is None or student_name not in PARENT_EMAILS:
#         print(f"No data to send or email not configured for {student_name}")
#         return

#     email_body = f"Hello,\n\nHere’s the weekly learning summary for {student_name}:\n\n"
#     email_body += df.to_string(index=False)
#     email_body += "\n\nKeep encouraging your child to practice daily!\n\nBest regards,\nAI Tutor Team"

#     try:
#         yag = yagmail.SMTP(SMTP_EMAIL, SMTP_PASSWORD)
#         yag.send(
#             to=PARENT_EMAILS[student_name],
#             subject=f"Weekly Learning Summary for {student_name}",
#             contents=email_body,
#         )
#         print(f"✅ Email sent to {student_name}'s parent")
#     except Exception as e:
#         print(f"❌ Failed to send email: {e}")


def send_weekly_email(student_name):
    df = get_weekly_summary(student_name)
    if df is None or student_name not in PARENT_EMAILS:
        print(f"No data to send or email not configured for {student_name}")
        return

    # Convert DataFrame to HTML table
    table_html = df.to_html(index=False, border=0, justify="center")

    email_body = f"""
    <html>
    <body>
        <p>Hello,</p>
        <p>Here’s the weekly learning summary for <b>{student_name}</b>:</p>
        {table_html}
        <p>Keep encouraging your child to practice daily!</p>
        <p>Best regards,<br>AI Tutor Team</p>
    </body>
    </html>
    """

    try:
        yag = yagmail.SMTP(SMTP_EMAIL, SMTP_PASSWORD)
        yag.send(
            to=PARENT_EMAILS[student_name],
            subject=f"Weekly Learning Summary for {student_name}",
            contents=email_body,
        )
        print(f"✅ Email sent to {student_name}'s parent")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")


# ----------------- RUN FOR ALL STUDENTS -----------------
if __name__ == "__main__":
    for student in PARENT_EMAILS.keys():
        send_weekly_email(student)
