import os
import json
import openai
from student_db import (
    update_student_progress,
    update_gamification,
    get_student_progress,
)


class EnhancedAITutor:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise RuntimeError("❌ Missing OPENAI_API_KEY environment variable.")
        openai.api_key = self.api_key
        self.model = "gpt-4o-mini"

    def analyze_student_pattern(self, student_name, subject):
        """Fetch recent performance to guide adaptive learning"""
        progress = get_student_progress(student_name, subject)
        analysis = {
            "is_new_student": len(progress) == 0,
            "total_sessions": len(progress),
            "average_mastery": (
                sum([p[5] for p in progress]) / len(progress) if progress else 0
            ),
            "learning_style": progress[0][7] if progress else "visual",
        }
        return analysis

    def generate_personalized_prompt(self, question, subject, grade, analysis):
        """Generate context-aware, adaptive prompt"""
        teaching_approach = "balanced explanation"
        if analysis["is_new_student"]:
            teaching_approach = "friendly intro, simple steps"
        elif analysis["average_mastery"] < 0.6:
            teaching_approach = "step-by-step, scaffolded guidance"
        elif analysis["average_mastery"] > 0.8:
            teaching_approach = "advanced challenge with deeper concepts"

        learning_styles = {
            "visual": "Include diagrams and visual metaphors",
            "auditory": "Explain verbally and use rhythm",
            "kinesthetic": "Provide hands-on or real-life examples",
            "reading": "Text-based stepwise explanation",
        }
        style_instruction = learning_styles.get(
            analysis["learning_style"], "Use visual metaphors"
        )

        prompt = f"""
You are an AI tutor for a {grade} student studying {subject}.
STUDENT CONTEXT: {analysis}
QUESTION: {question}
TEACHING APPROACH: {teaching_approach}
LEARNING STYLE: {style_instruction}

Please provide a comprehensive, well-formatted response that includes:
1. A friendly greeting
2. Clear explanation of the concept with examples
3. Visual aids or diagrams description (if applicable)
4. Interactive elements or activities
5. Practice suggestions
6. Encouragement
7. Next steps for learning
8. A difficulty check question

Format your response as readable text with clear sections and emoji headers for better organization.
Do NOT respond in JSON format - provide a natural, conversational educational response.
"""
        return prompt

    def format_response(self, content):
        """Process the AI response and extract hints"""
        hints = []
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if any(
                keyword in line.lower()
                for keyword in [
                    "try",
                    "practice",
                    "exercise",
                    "next",
                    "suggestion",
                    "activity",
                ]
            ):
                if line and len(line) > 10:
                    hints.append(line.replace("- ", "").replace("* ", ""))
        if not hints:
            hints = [
                "Practice with more similar problems",
                "Ask if you need clarification on any step",
                "Try explaining the concept back in your own words",
            ]
        return content, hints[:5]

    def ask_tutor_sync(self, question, subject, grade, student_name="Anonymous"):
        analysis = self.analyze_student_pattern(student_name, subject)
        prompt = self.generate_personalized_prompt(question, subject, grade, analysis)

        try:
            # Using OpenAI SDK v1.0+
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert AI tutor with advanced pedagogical knowledge. Provide clear, engaging, and educational responses formatted with sections and emojis for better readability.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=1200,
            )

            content = response.choices[0].message.content.strip()
            formatted_text, hints = self.format_response(content)

            # Update student progress & gamification
            update_student_progress(
                student_name,
                subject,
                "current_topic",
                5,
                analysis.get("average_mastery", 0.7),
                "",
                analysis.get("learning_style", "visual"),
            )
            update_gamification(student_name, xp=10)

            # Basic resources
            resources = [
                {
                    "title": f"{subject} Practice Problems",
                    "link": "https://www.khanacademy.org",
                    "description": "Interactive exercises and explanations",
                },
                {
                    "title": f"{subject} Video Tutorials",
                    "link": "https://www.youtube.com",
                    "description": "Visual learning resources",
                },
            ]

            return formatted_text, hints, json.dumps(resources)

        except Exception as e:
            error_response = f"Hi {student_name}! 👋\n\n❌ I encountered a technical issue: {str(e)}\n\n🔄 Please try again."
            fallback_hints = [
                "Check your internet connection",
                "Try rephrasing your question",
                "Contact your teacher if issues persist",
            ]
            return error_response, fallback_hints, json.dumps([])


# --- Singleton instance ---
enhanced_tutor = EnhancedAITutor()


def ask_tutor_sync(question, subject, grade, student_name="Anonymous"):
    return enhanced_tutor.ask_tutor_sync(question, subject, grade, student_name)
