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


# # create current streak and week topic suggest
# import os
# import requests
# import json
# from student_db import (
#     update_student_progress,
#     update_gamification,
#     get_student_progress,
# )

# from datetime import datetime


# class EnhancedAITutor:
#     def __init__(self):
#         self.api_key = os.getenv(
#             "OPENROUTER_API_KEY",
#             "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",
#         )
#         self.base_url = "https://openrouter.ai/api/v1/chat/completions"
#         self.model = "openai/gpt-4o-mini"

#     def analyze_student_pattern(self, student_name, subject):
#         """Fetch recent performance to guide adaptive learning"""
#         progress = get_student_progress(student_name, subject)
#         analysis = {
#             "is_new_student": len(progress) == 0,
#             "total_sessions": len(progress),
#             "average_mastery": (
#                 sum([p[5] for p in progress]) / len(progress) if progress else 0
#             ),
#             "learning_style": progress[0][7] if progress else "visual",
#         }
#         return analysis

#     def generate_personalized_prompt(self, question, subject, grade, analysis):
#         """Generate context-aware, adaptive prompt that returns readable text"""
#         teaching_approach = "balanced explanation"
#         if analysis["is_new_student"]:
#             teaching_approach = "friendly intro, simple steps"
#         elif analysis["average_mastery"] < 0.6:
#             teaching_approach = "step-by-step, scaffolded guidance"
#         elif analysis["average_mastery"] > 0.8:
#             teaching_approach = "advanced challenge with deeper concepts"

#         learning_styles = {
#             "visual": "Include diagrams and visual metaphors",
#             "auditory": "Explain verbally and use rhythm",
#             "kinesthetic": "Provide hands-on or real-life examples",
#             "reading": "Text-based stepwise explanation",
#         }
#         style_instruction = learning_styles.get(
#             analysis["learning_style"], "Use visual metaphors"
#         )

#         prompt = f"""
# You are an AI tutor for a {grade} student studying {subject}.
# STUDENT CONTEXT: {analysis}
# QUESTION: {question}
# TEACHING APPROACH: {teaching_approach}
# LEARNING STYLE: {style_instruction}

# Please provide a comprehensive, well-formatted response that includes:
# 1. A friendly greeting
# 2. Clear explanation of the concept with examples
# 3. Visual aids or diagrams description (if applicable)
# 4. Interactive elements or activities
# 5. Practice suggestions
# 6. Encouragement
# 7. Next steps for learning
# 8. A difficulty check question

# Format your response as readable text with clear sections and emoji headers for better organization.
# Do NOT respond in JSON format - provide a natural, conversational educational response.
# """
#         return prompt

#     def format_response(self, content):
#         """Process the AI response and extract components"""
#         # Since we're not using JSON anymore, we'll work with the text directly
#         # and try to extract hints and create a basic structure

#         # Extract potential hints/suggestions from the content
#         hints = []
#         lines = content.split("\n")

#         for line in lines:
#             line = line.strip()
#             if any(
#                 keyword in line.lower()
#                 for keyword in [
#                     "try",
#                     "practice",
#                     "exercise",
#                     "next",
#                     "suggestion",
#                     "activity",
#                 ]
#             ):
#                 if line and len(line) > 10:  # Avoid very short lines
#                     hints.append(line.replace("- ", "").replace("* ", ""))

#         # If no specific hints found, create some generic ones
#         if not hints:
#             hints = [
#                 "Practice with more similar problems",
#                 "Ask if you need clarification on any step",
#                 "Try explaining the concept back in your own words",
#             ]

#         # Keep only the most relevant hints (max 5)
#         hints = hints[:5]

#         return content, hints

#     def ask_tutor_sync(self, question, subject, grade, student_name="Anonymous"):
#         analysis = self.analyze_student_pattern(student_name, subject)
#         prompt = self.generate_personalized_prompt(question, subject, grade, analysis)

#         headers = {
#             "Authorization": f"Bearer {self.api_key}",
#             "Content-Type": "application/json",
#         }
#         data = {
#             "model": self.model,
#             "messages": [
#                 {
#                     "role": "system",
#                     "content": "You are an expert AI tutor with advanced pedagogical knowledge. Provide clear, engaging, and educational responses formatted with sections and emojis for better readability.",
#                 },
#                 {"role": "user", "content": prompt},
#             ],
#             "temperature": 0.7,
#             "max_tokens": 1200,
#         }

#         try:
#             response = requests.post(
#                 self.base_url, headers=headers, json=data, timeout=30
#             )
#             if response.status_code == 200:
#                 content = response.json()["choices"][0]["message"]["content"]

#                 # Format the response and extract hints
#                 formatted_text, hints = self.format_response(content)

#             else:
#                 formatted_text = f"Hi {student_name}! 👋\n\nI'm having some technical difficulties right now, but I'd love to help you with your question about {subject}!\n\n📝 **Your Question:** {question}\n\n💡 **Quick Tip:** While I get back online, try breaking down your question into smaller parts or looking for patterns in similar problems.\n\n🔄 Please try asking again in a moment!"
#                 hints = [
#                     "Try breaking the problem into smaller steps",
#                     "Look for similar examples in your textbook",
#                     "Ask your teacher or a classmate for help",
#                 ]

#             # Update student progress & gamification
#             update_student_progress(
#                 student_name,
#                 subject,
#                 "current_topic",
#                 5,
#                 analysis.get("average_mastery", 0.7),
#                 "",
#                 analysis.get("learning_style", "visual"),
#             )
#             update_gamification(student_name, xp=10)

#             # Create basic resources (these could be enhanced based on subject/topic)
#             resources = [
#                 {
#                     "title": f"{subject} Practice Problems",
#                     "link": "https://www.khanacademy.org",
#                     "description": "Interactive exercises and explanations",
#                 },
#                 {
#                     "title": f"{subject} Video Tutorials",
#                     "link": "https://www.youtube.com",
#                     "description": "Visual learning resources",
#                 },
#             ]

#             return formatted_text, hints, json.dumps(resources)

#         except Exception as e:
#             error_response = f"Hi {student_name}! 👋\n\n❌ I encountered a technical issue: {str(e)}\n\n🔄 Please try again, and if the problem persists, contact your teacher for assistance.\n\n💪 Don't worry - we'll get your question answered!"
#             fallback_hints = [
#                 "Check your internet connection",
#                 "Try rephrasing your question",
#                 "Contact your teacher if issues persist",
#             ]
#             return error_response, fallback_hints, json.dumps([])


# # --- Singleton instance ---
# enhanced_tutor = EnhancedAITutor()


# def ask_tutor_sync(question, subject, grade, student_name="Anonymous"):
#     return enhanced_tutor.ask_tutor_sync(question, subject, grade, student_name)


# # import os
# # import requests
# # import json
# # import sqlite3
# # from datetime import datetime
# # import random
# # from student_db import update_student_progress, update_gamification, get_student_progress

# # class EnhancedAITutor:
# #     def __init__(self):
# #         self.api_key = os.getenv("OPENROUTER_API_KEY", "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")
# #         self.base_url = "https://openrouter.ai/api/v1/chat/completions"
# #         self.model = "openai/gpt-4o-mini"

# #     def analyze_student_pattern(self, student_name, subject):
# #         """Fetch recent performance to guide adaptive learning"""
# #         progress = get_student_progress(student_name, subject)
# #         analysis = {
# #             "is_new_student": len(progress) == 0,
# #             "total_sessions": len(progress),
# #             "average_mastery": sum([p[5] for p in progress])/len(progress) if progress else 0,
# #             "learning_style": progress[0][7] if progress else "visual"
# #         }
# #         return analysis

# #     def generate_personalized_prompt(self, question, subject, grade, analysis):
# #         """Generate context-aware, adaptive prompt"""
# #         teaching_approach = "balanced explanation"
# #         if analysis["is_new_student"]:
# #             teaching_approach = "friendly intro, simple steps"
# #         elif analysis["average_mastery"] < 0.6:
# #             teaching_approach = "step-by-step, scaffolded guidance"
# #         elif analysis["average_mastery"] > 0.8:
# #             teaching_approach = "advanced challenge with deeper concepts"

# #         learning_styles = {
# #             "visual": "Include diagrams and visual metaphors",
# #             "auditory": "Explain verbally and use rhythm",
# #             "kinesthetic": "Provide hands-on or real-life examples",
# #             "reading": "Text-based stepwise explanation"
# #         }
# #         style_instruction = learning_styles.get(analysis["learning_style"], "Use visual metaphors")

# #         prompt = f"""
# # You are an AI tutor for a {grade} student studying {subject}.
# # STUDENT CONTEXT: {analysis}
# # QUESTION: {question}
# # TEACHING APPROACH: {teaching_approach}
# # LEARNING STYLE: {style_instruction}
# # Respond in JSON format with:
# # - greeting
# # - main_explanation
# # - interactive_elements
# # - practice_suggestions
# # - encouragement
# # - next_steps
# # - difficulty_check
# # - resources
# # """
# #         return prompt

# #     def ask_tutor_sync(self, question, subject, grade, student_name="Anonymous"):
# #         analysis = self.analyze_student_pattern(student_name, subject)
# #         prompt = self.generate_personalized_prompt(question, subject, grade, analysis)
# #         headers = {
# #             "Authorization": f"Bearer {self.api_key}",
# #             "Content-Type": "application/json"
# #         }
# #         data = {
# #             "model": self.model,
# #             "messages": [
# #                 {"role": "system", "content": "You are an expert AI tutor with advanced pedagogical knowledge."},
# #                 {"role": "user", "content": prompt}
# #             ],
# #             "temperature": 0.7,
# #             "max_tokens": 1200
# #         }
# #         try:
# #             response = requests.post(self.base_url, headers=headers, json=data, timeout=30)
# #             if response.status_code == 200:
# #                 content = response.json()['choices'][0]['message']['content']
# #                 try:
# #                     parsed = json.loads(content)
# #                 except:
# #                     parsed = {"greeting": "Hi!", "main_explanation": content, "interactive_elements": [], "practice_suggestions": [], "encouragement": "", "next_steps": "", "difficulty_check": "", "resources": []}
# #             else:
# #                 parsed = {"greeting": "Hi!", "main_explanation": "Tutor unavailable, fallback guidance.", "interactive_elements": [], "practice_suggestions": [], "encouragement": "", "next_steps": "", "difficulty_check": "", "resources": []}

# #             # Update student progress
# #             update_student_progress(
# #                 student_name, subject, "current_topic", 5, analysis.get("average_mastery", 0.7),
# #                 "", analysis.get("learning_style", "visual")
# #             )
# #             update_gamification(student_name, xp=10)

# #             # Return plain text for UI
# #             main_text = f"{parsed.get('greeting','Hi!')}\n\n{parsed.get('main_explanation','')}"
# #             if parsed.get('encouragement'):
# #                 main_text += f"\n\n{parsed.get('encouragement')}"
# #             hints = parsed.get('interactive_elements',[]) + parsed.get('practice_suggestions',[])
# #             if parsed.get('next_steps'):
# #                 hints.append(f"Next: {parsed['next_steps']}")
# #             if parsed.get('difficulty_check'):
# #                 hints.append(parsed['difficulty_check'])
# #             return main_text, hints, json.dumps(parsed.get('resources',[]))
# #         except Exception as e:
# #             return f"Hi {student_name}! Technical issue, try again.", ["Check your input"], json.dumps([])

# # # Singleton
# # enhanced_tutor = EnhancedAITutor()
# # def ask_tutor_sync(question, subject, grade, student_name="Anonymous"):
# #     return enhanced_tutor.ask_tutor_sync(question, subject, grade, student_name)


# # # *********************************final code for me
# # import os
# # import requests
# # import json
# # import sqlite3
# # from datetime import datetime, timedelta
# # import random

# # class EnhancedAITutor:
# #     def __init__(self):
# #         self.api_key = "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"
# #         self.base_url = "https://openrouter.ai/api/v1/chat/completions"
# #         self.model = "openai/gpt-4o-mini"
# #         self.init_database()

# #     def init_database(self):
# #         """Initialize enhanced database for student tracking"""
# #         conn = sqlite3.connect("enhanced_tutor.db")
# #         c = conn.cursor()

# #         # Student progress tracking
# #         c.execute('''CREATE TABLE IF NOT EXISTS student_progress (
# #             id INTEGER PRIMARY KEY,
# #             student_name TEXT,
# #             subject TEXT,
# #             topic TEXT,
# #             difficulty_level INTEGER,
# #             mastery_score REAL,
# #             struggle_areas TEXT,
# #             learning_style TEXT,
# #             last_session TIMESTAMP,
# #             total_sessions INTEGER DEFAULT 0,
# #             success_rate REAL DEFAULT 0
# #         )''')

# #         # Learning patterns and preferences
# #         c.execute('''CREATE TABLE IF NOT EXISTS learning_patterns (
# #             id INTEGER PRIMARY KEY,
# #             student_name TEXT,
# #             preferred_explanation_type TEXT,
# #             response_time_average REAL,
# #             common_mistakes TEXT,
# #             motivation_triggers TEXT,
# #             engagement_level INTEGER,
# #             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
# #         )''')

# #         # Session analytics
# #         c.execute('''CREATE TABLE IF NOT EXISTS session_analytics (
# #             id INTEGER PRIMARY KEY,
# #             student_name TEXT,
# #             session_duration INTEGER,
# #             questions_asked INTEGER,
# #             concepts_learned INTEGER,
# #             difficulty_progression TEXT,
# #             engagement_score INTEGER,
# #             session_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
# #         )''')

# #         conn.commit()
# #         conn.close()

# #     def analyze_student_pattern(self, student_name, question, subject):
# #         """Analyze student's learning patterns and history"""
# #         conn = sqlite3.connect("enhanced_tutor.db")
# #         c = conn.cursor()

# #         # Get recent interactions
# #         c.execute("""
# #             SELECT * FROM student_progress
# #             WHERE student_name = ? AND subject = ?
# #             ORDER BY last_session DESC LIMIT 10
# #         """, (student_name, subject))
# #         progress_history = c.fetchall()

# #         # Get learning patterns
# #         c.execute("""
# #             SELECT * FROM learning_patterns
# #             WHERE student_name = ?
# #             ORDER BY created_at DESC LIMIT 1
# #         """, (student_name,))
# #         learning_pattern = c.fetchone()

# #         conn.close()

# #         # Analyze patterns
# #         analysis = {
# #             "is_new_student": len(progress_history) == 0,
# #             "total_sessions": len(progress_history),
# #             "recent_subjects": list(set([p[2] for p in progress_history])),
# #             "average_mastery": sum([p[4] for p in progress_history]) / len(progress_history) if progress_history else 0,
# #             "learning_style": learning_pattern[3] if learning_pattern else "visual",
# #             "common_struggles": learning_pattern[4] if learning_pattern else "",
# #             "motivation_level": learning_pattern[6] if learning_pattern else 5
# #         }

# #         return analysis

# #     def generate_personalized_prompt(self, question, subject, grade, student_analysis):
# #         """Generate highly personalized prompt based on student analysis"""

# #         # Adaptive teaching strategies based on student history
# #         if student_analysis["is_new_student"]:
# #             teaching_approach = "friendly introduction with confidence building"
# #             complexity = "start simple and gauge understanding"
# #         elif student_analysis["average_mastery"] < 0.6:
# #             teaching_approach = "patient, step-by-step with lots of encouragement"
# #             complexity = "break down into very small steps"
# #         elif student_analysis["average_mastery"] > 0.8:
# #             teaching_approach = "challenging with deeper concepts"
# #             complexity = "provide advanced insights and extensions"
# #         else:
# #             teaching_approach = "balanced with moderate challenge"
# #             complexity = "standard progression with some stretch"

# #         # Learning style adaptation
# #         style_instructions = {
# #             "visual": "Use analogies, diagrams descriptions, and visual metaphors",
# #             "auditory": "Use rhythmic patterns, verbal repetition, and sound associations",
# #             "kinesthetic": "Use hands-on examples, real-world applications, and movement analogies",
# #             "reading": "Provide written steps, lists, and text-based explanations"
# #         }

# #         learning_style = student_analysis.get("learning_style", "visual")
# #         style_instruction = style_instructions.get(learning_style, style_instructions["visual"])

# #         # Motivation triggers
# #         motivation_elements = [
# #             "Acknowledge effort and progress",
# #             "Connect to real-world applications",
# #             "Use encouraging language",
# #             "Celebrate small wins",
# #             "Show how this builds on previous knowledge"
# #         ]

# #         prompt = f"""
# # You are an advanced AI tutor with deep pedagogical expertise. You're working with a {grade} student studying {subject}.

# # STUDENT CONTEXT:
# # - Total previous sessions: {student_analysis['total_sessions']}
# # - Average mastery level: {student_analysis['average_mastery']:.2f}
# # - Learning style: {learning_style}
# # - Is new student: {student_analysis['is_new_student']}

# # QUESTION: {question}

# # TEACHING APPROACH: {teaching_approach}
# # COMPLEXITY LEVEL: {complexity}
# # LEARNING STYLE ADAPTATION: {style_instruction}

# # RESPONSE FORMAT (JSON):
# # {{
# #   "greeting": "Personalized greeting acknowledging their progress/effort",
# #   "main_explanation": "Detailed, step-by-step explanation adapted to their learning style",

# #   "next_steps": "What to study next and why",
# #   "difficulty_check": "Question to gauge if explanation was right level",
# #   "resources": ["Curated resources matching their learning style"]
# # }}

# # PEDAGOGICAL PRINCIPLES:
# # 1. Use Socratic questioning - guide discovery rather than just telling
# # 2. Provide scaffolding - support that can be gradually removed
# # 3. Check for misconceptions actively
# # 4. {motivation_elements[random.randint(0, len(motivation_elements)-1)]}
# # 5. Adapt difficulty based on student response patterns
# # 6. Make learning meaningful through connections

# # Remember: You're not just answering a question - you're building understanding, confidence, and love for learning.
# # """

# #         return prompt

# #     def ask_tutor_sync(self, question, subject, grade, student_name="Anonymous"):
# #         """Enhanced AI tutoring with personalization and advanced pedagogy"""

# #         # Analyze student patterns
# #         student_analysis = self.analyze_student_pattern(student_name, question, subject)

# #         # Generate personalized prompt
# #         prompt = self.generate_personalized_prompt(question, subject, grade, student_analysis)

# #         headers = {
# #             "Authorization": f"Bearer {self.api_key}",
# #             "Content-Type": "application/json"
# #         }

# #         data = {
# #             "model": self.model,
# #             "messages": [
# #                 {"role": "system", "content": "You are an expert AI tutor with advanced pedagogical knowledge. You understand learning psychology, motivation, and personalized education. Always respond in valid JSON format."},
# #                 {"role": "user", "content": prompt}
# #             ],
# #             "temperature": 0.7,
# #             "max_tokens": 1200
# #         }

# #         try:
# #             print(f"🧠 Analyzing student pattern for {student_name}...")
# #             print(f"📊 Student Analysis: {student_analysis}")
# #             print(f"🔄 Making personalized API call...")

# #             response = requests.post(self.base_url, headers=headers, json=data, timeout=30)

# #             if response.status_code == 200:
# #                 result = response.json()
# #                 content = result['choices'][0]['message']['content'].strip()

# #                 print(f"✅ Enhanced tutor response received: {len(content)} characters")

# #                 try:
# #                     # Parse comprehensive response
# #                     parsed_data = json.loads(content)

# #                     # Extract all components
# #                     response_data = {
# #                         "greeting": parsed_data.get("greeting", f"Hi! Let's work on this {subject} question together."),
# #                         "main_explanation": parsed_data.get("main_explanation", ""),
# #                         "interactive_elements": parsed_data.get("interactive_elements", []),
# #                         "practice_suggestions": parsed_data.get("practice_suggestions", []),
# #                         "encouragement": parsed_data.get("encouragement", "Great question!"),
# #                         "next_steps": parsed_data.get("next_steps", ""),
# #                         "difficulty_check": parsed_data.get("difficulty_check", ""),
# #                         "resources": parsed_data.get("resources", []),
# #                         "connection_to_previous": parsed_data.get("connection_to_previous", ""),
# #                         "real_world_application": parsed_data.get("real_world_application", "")
# #                     }

# #                     # Update student progress
# #                     self.update_student_progress(student_name, subject, question, response_data, student_analysis)

# #                     print(f"✅ Successfully processed enhanced tutoring response!")
# #                     return response_data

# #                 except json.JSONDecodeError as e:
# #                     print(f"❌ JSON parsing failed: {e}")
# #                     # Fallback to basic response
# #                     return {
# #                         "greeting": "Hi there!",
# #                         "main_explanation": content,
# #                         "interactive_elements": ["Can you explain this back to me in your own words?"],
# #                         "practice_suggestions": ["Try a similar problem"],
# #                         "encouragement": "You're doing great!",
# #                         "next_steps": "Keep practicing",
# #                         "difficulty_check": "Was this explanation clear?",
# #                         "resources": ["https://www.khanacademy.org/"],
# #                         "connection_to_previous": "",
# #                         "real_world_application": ""
# #                     }

# #             else:
# #                 print(f"❌ API error: {response.status_code}")
# #                 raise Exception(f"API returned status code: {response.status_code}")

# #         except Exception as e:
# #             print(f"❌ Error in enhanced tutoring: {str(e)}")
# #             return self.get_fallback_response(question, subject, grade, student_name)

# #     def update_student_progress(self, student_name, subject, question, response_data, analysis):
# #         """Update student progress and learning patterns"""
# #         conn = sqlite3.connect("enhanced_tutor.db")
# #         c = conn.cursor()

# #         # Simple mastery estimation based on question complexity and response
# #         estimated_mastery = 0.7 if len(question.split()) > 10 else 0.8

# #         # Update or insert progress
# #         c.execute("""
# #             INSERT OR REPLACE INTO student_progress
# #             (student_name, subject, topic, difficulty_level, mastery_score,
# #              struggle_areas, learning_style, last_session, total_sessions, success_rate)
# #             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
# #         """, (
# #             student_name, subject, "current_topic", 5, estimated_mastery,
# #             "", analysis.get("learning_style", "visual"), datetime.now(),
# #             analysis["total_sessions"] + 1, estimated_mastery
# #         ))

# #         conn.commit()
# #         conn.close()

# #     def get_fallback_response(self, question, subject, grade, student_name):
# #         """Intelligent fallback when API fails"""
# #         return {
# #             "greeting": f"Hi {student_name}! I'm having some technical difficulties, but I'm here to help.",
# #             "main_explanation": f"For your {subject} question '{question[:100]}...', let me provide some guidance. This type of problem typically requires breaking it down into smaller steps and applying fundamental concepts systematically.",
# #             "interactive_elements": ["Can you identify what the question is asking for?", "What information are you given?"],
# #             "practice_suggestions": ["Try similar problems from your textbook", "Review the relevant formulas or concepts"],
# #             "encouragement": "Don't worry - every expert was once a beginner. You're building important skills!",
# #             "next_steps": "Once we solve this, we can explore related concepts",
# #             "difficulty_check": "Is this the right level of explanation for you?",
# #             "resources": ["https://www.khanacademy.org/", "https://www.mathsisfun.com/", "Ask your teacher for additional help"],
# #             "connection_to_previous": "This builds on concepts you've learned before",
# #             "real_world_application": f"These {subject} skills are used in many real-world situations"
# #         }

# # # Initialize the enhanced tutor
# # enhanced_tutor = EnhancedAITutor()


# # def ask_tutor_sync(question, subject, grade, student_name="Anonymous"):
# #     """Main function for enhanced AI tutoring"""
# #     response_data = enhanced_tutor.ask_tutor_sync(question, subject, grade, student_name)

# #     # Only show greeting + main explanation + optional encouragement + real-world link
# #     main_text = f"{response_data['greeting']}\n\n{response_data['main_explanation']}"
# #     if response_data.get('encouragement'):
# #         main_text += f"\n\n{response_data['encouragement']}"
# #     if response_data.get('real_world_application'):
# #         main_text += f"\n\nReal-world connection: {response_data['real_world_application']}"

# #     # Build hints list for internal use (do NOT display JSON)
# #     hints = []
# #     hints.extend(response_data.get('interactive_elements', []))
# #     hints.extend(response_data.get('practice_suggestions', []))
# #     if response_data.get('next_steps'):
# #         hints.append(f"Next: {response_data['next_steps']}")
# #     if response_data.get('difficulty_check'):
# #         hints.append(response_data['difficulty_check'])

# #     # Return plain text for UI, JSON only internally
# #     return main_text, hints, json.dumps(response_data.get('resources', []))


# # # **************final code end here for me
