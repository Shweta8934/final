import os
import json
import uuid
import streamlit as st
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
print(f"Loaded OPENAI_API_KEY: {repr(OPENAI_API_KEY)}")
if not OPENAI_API_KEY:
    raise RuntimeError("❌ Missing OPENAI_API_KEY environment variable.")

openai.api_key = OPENAI_API_KEY


def clean_json_response(content: str):
    """Remove markdown fences and extract JSON only."""
    content = content.strip()
    if content.startswith("```"):
        content = content.strip("`")
        if content.lower().startswith("json"):
            content = content[4:].strip()
    if "[" in content and "]" in content:
        content = content[content.find("[") : content.rfind("]") + 1]
    return content


def get_quiz_questions(grade, subject, limit=3):
    """Fetch quiz questions dynamically from OpenAI using new API (>=1.0.0)."""

    prompt = f"""
    Generate {limit} multiple-choice quiz questions for Grade {grade} in {subject}.
    Each question must have:
    - "id": a unique number
    - "question": the question text
    - "options": a list of 3 possible answers
    - "correct": the correct answer (must match one of the options)

    Respond only with JSON in this format:
    [
      {{
        "id": 1,
        "question": "What is 2 + 2?",
        "options": ["3", "4", "5"],
        "correct": "4"
      }}
    ]
    """

    try:
        # New API syntax
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )

        content = response.choices[0].message.content.strip()
        if not content:
            raise ValueError("Empty AI response")

        content = clean_json_response(content)
        questions = json.loads(content)

        formatted = []
        for q in questions:
            formatted.append(
                (
                    q.get("id", str(uuid.uuid4())),
                    q["question"],
                    json.dumps(q["options"]),
                    q["correct"],
                )
            )
        return formatted

    except Exception as e:
        st.error(f"⚠️ AI Question generation failed: {e}")

    return []


def quiz_component():
    """Streamlit UI for AI-powered quiz."""
    st.header(" Quiz")

    # Select student, grade, and subject
    student = st.text_input("Enter Student Name")
    grade = st.selectbox("Select Grade", ["6", "7", "8"])
    subject = st.selectbox("Select Subject", ["Math", "Science", "English"])

    if "attempts" not in st.session_state:
        st.session_state.attempts = {}  # {student: {subject: count}}

    if student:
        st.session_state.attempts.setdefault(student, {}).setdefault(subject, 0)

    # Button to start quiz
    if st.button("🎯 Generate Quiz"):
        if not student:
            st.warning("Please enter student name first!")
        else:
            attempts_used = st.session_state.attempts[student][subject]
            if attempts_used >= 2:
                st.error(f"❌ Maximum 2 attempts reached for {subject}!")
                st.session_state.questions = []  # clear quiz
            else:
                st.session_state.questions = get_quiz_questions(
                    grade=grade, subject=subject, limit=3
                )
                st.session_state.answers = {}
                st.session_state.submitted = False

    # Show quiz only if questions exist
    if student and "questions" in st.session_state and st.session_state.questions:
        for qid, question, options_json, correct in st.session_state.questions:
            st.subheader(f"Q{qid}: {question}")
            options = json.loads(options_json)
            st.session_state.answers[qid] = st.radio(
                f"Choose answer for Q{qid}", options, key=f"q{qid}"
            )

        if st.button("✅ Submit Answers"):
            if st.session_state.submitted:
                st.warning("You already submitted this attempt.")
            else:
                st.session_state.submitted = True
                st.session_state.attempts[student][subject] += 1

    # Results after submit
    if student and st.session_state.get("submitted", False):
        score = 0
        total = len(st.session_state.questions)
        st.write("### 📊 Results:")

        for qid, question, options_json, correct in st.session_state.questions:
            user_answer = st.session_state.answers.get(qid)
            if user_answer == correct:
                st.success(f"Q{qid}: ✅ Correct! ({question})")
                score += 1
            else:
                st.error(f"Q{qid}: ❌ Wrong. Correct answer: {correct}")

        st.info(f"Final Score: {score}/{total}")
        st.info(
            f"Attempts used: {st.session_state.attempts[student][subject]}/2 for {subject}"
        )


# Run the app
if __name__ == "__main__":
    quiz_component()
