# student_utils.py for week topic sugeestion 
import sqlite3
import json

DB_NAME = "student.db"

# def get_student_weak_topics(student_name, threshold=0.2, limit_examples=5):
#     """
#     Returns weak topics, along with example questions, answers, and resources.
#     """
#     conn = sqlite3.connect(DB_NAME)
#     c = conn.cursor()

#     # Weak topics based on negative feedback
#     c.execute("""
#         SELECT subject, COUNT(*) as total,
#                SUM(CASE WHEN feedback = -1 THEN 1 ELSE 0 END) as wrong
#         FROM interactions
#         WHERE student = ?
#         GROUP BY subject
#     """, (student_name,))
#     topics = c.fetchall()

#     weak_topics = []
#     for subj, total, wrong in topics:
#         if total > 0 and (wrong / total) > threshold:
#             weak_topics.append(subj)

#     # Collect examples + resources per weak topic
#     topic_details = {}
#     for topic in weak_topics:
#         c.execute("""
#             SELECT question, answer, resources
#             FROM interactions
#             WHERE student = ? AND subject = ? AND feedback = -1
#             ORDER BY created_at DESC
#             LIMIT ?
#         """, (student_name, topic, limit_examples))
#         examples = []
#         rows = c.fetchall()
#         for q, a, resources in rows:
#             try:
#                 res_list = json.loads(resources) if resources else []
#             except:
#                 res_list = []
#             examples.append({"question": q, "answer": a, "resources": res_list})
#         topic_details[topic] = examples

#     conn.close()
#     return weak_topics, topic_details
def get_student_weak_topics(student_name, grade=None):
    """
    Returns weak topics and detailed examples for a given student,
    optionally filtered by grade.
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if grade:
        c.execute("""
            SELECT subject, question, answer, resources, feedback
            FROM interactions
            WHERE student=? AND grade=? 
        """, (student_name, grade))
    else:
        c.execute("""
            SELECT subject, question, answer, resources, feedback
            FROM interactions
            WHERE student=? 
        """, (student_name,))
    rows = c.fetchall()
    conn.close()

    # Compute weak topics based on negative feedback
    topic_dict = {}
    for subj, q, a, res, fb in rows:
        if fb == -1:  # only count questions with negative feedback
            if subj not in topic_dict:
                topic_dict[subj] = []
            topic_dict[subj].append({"question": q, "answer": a, "resources": json.loads(res) if res else []})

    weak_topics = list(topic_dict.keys())
    return weak_topics, topic_dict

