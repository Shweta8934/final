# student_utils.py for week topic sugeestion
import sqlite3
import json

DB_NAME = "student.db"


def get_student_weak_topics(student_name, grade=None):
    """
    Returns weak topics and detailed examples for a given student,
    optionally filtered by grade.
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if grade:
        c.execute(
            """
            SELECT subject, question, answer, resources, feedback
            FROM interactions
            WHERE student=? AND grade=? 
        """,
            (student_name, grade),
        )
    else:
        c.execute(
            """
            SELECT subject, question, answer, resources, feedback
            FROM interactions
            WHERE student=? 
        """,
            (student_name,),
        )
    rows = c.fetchall()
    conn.close()

    # Compute weak topics based on negative feedback
    topic_dict = {}
    for subj, q, a, res, fb in rows:
        if fb == -1:  # only count questions with negative feedback
            if subj not in topic_dict:
                topic_dict[subj] = []
            topic_dict[subj].append(
                {
                    "question": q,
                    "answer": a,
                    "resources": json.loads(res) if res else [],
                }
            )

    weak_topics = list(topic_dict.keys())
    return weak_topics, topic_dict
