"""
AI Study Service
Powers flashcard generation, quiz creation, writing help, and study scheduling.
Uses Groq API with Llama 3.3 70B for fast, affordable inference.
"""

import json
import os
from typing import Dict, List, Optional
from openai import OpenAI


client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)
MODEL = "llama-3.3-70b-versatile"


def _ask_llm(system: str, prompt: str, max_tokens: int = 2000) -> str:
    """Send a prompt to Groq and return the response text."""
    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content


def _strip_code_fences(text: str) -> str:
    """Strip markdown code fences from LLM output."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        text = text.rsplit("```", 1)[0]
    return text.strip()


def generate_flashcards(topic: str, source_text: str, count: int = 10) -> List[Dict]:
    """
    Generate flashcards from notes or course content.
    Returns list of {front, back, difficulty} dicts.
    """
    system = (
        "You are a study assistant that creates effective flashcards for college students. "
        "Create clear, concise flashcards that test key concepts. "
        "Return ONLY valid JSON — no markdown, no code fences."
    )
    prompt = f"""Create {count} flashcards from the following material about "{topic}".

Material:
{source_text[:4000]}

Return a JSON array where each object has:
- "front": the question or prompt (concise)
- "back": the answer (clear but brief)
- "difficulty": "easy", "medium", or "hard"

Return ONLY the JSON array, nothing else."""

    try:
        text = _ask_llm(system, prompt)
        return json.loads(_strip_code_fences(text))
    except Exception as e:
        print(f"Flashcard generation error: {e}")
        return []


def generate_quiz(topic: str, context: str, num_questions: int = 5) -> List[Dict]:
    """
    Generate multiple-choice quiz questions.
    Returns list of {question, options[], correct_index, explanation} dicts.
    """
    system = (
        "You are a study assistant creating quiz questions for college students. "
        "Create challenging but fair multiple-choice questions. "
        "Return ONLY valid JSON — no markdown, no code fences."
    )
    prompt = f"""Create {num_questions} multiple-choice quiz questions about "{topic}".

Context:
{context[:4000]}

Return a JSON array where each object has:
- "question": the question text
- "options": array of 4 answer choices (strings)
- "correct_index": index (0-3) of the correct answer
- "explanation": brief explanation of why the answer is correct

Return ONLY the JSON array, nothing else."""

    try:
        text = _ask_llm(system, prompt)
        return json.loads(_strip_code_fences(text))
    except Exception as e:
        print(f"Quiz generation error: {e}")
        return []


def writing_help(
    help_type: str,
    assignment_name: str,
    assignment_description: str,
    user_input: str,
) -> str:
    """
    Provide writing assistance — NOT writing it for them.
    help_type: "outline", "brainstorm", "feedback", "strengthen", "cite"
    """
    system = (
        "You are a writing tutor helping a college student improve their work. "
        "IMPORTANT: You help students think and write better — you do NOT write their assignment for them. "
        "Give guidance, suggestions, and feedback. Ask questions that help them think deeper. "
        "Be encouraging but honest."
    )

    type_prompts = {
        "outline": f"""Help me create an outline for this assignment.

Assignment: {assignment_name}
Description: {assignment_description}

My initial thoughts: {user_input}

Create a structured outline with main sections and key points I should cover. Suggest what to include in each section but don't write the actual content.""",

        "brainstorm": f"""Help me brainstorm ideas for this assignment.

Assignment: {assignment_name}
Description: {assignment_description}

What I have so far: {user_input}

Give me 5-7 thought-provoking questions and angles I could explore. Help me think deeper about the topic.""",

        "feedback": f"""Give me feedback on my draft for this assignment.

Assignment: {assignment_name}
Description: {assignment_description}

My draft:
{user_input}

Give constructive feedback on: structure, argument strength, clarity, and what's missing. Be specific about what works well and what needs improvement.""",

        "strengthen": f"""Help me strengthen this paragraph/section.

Assignment: {assignment_name}

My writing:
{user_input}

Suggest specific ways to make this stronger — better word choices, clearer logic, stronger evidence. Don't rewrite it, but point out where and how I can improve.""",

        "cite": f"""Help me think about sources and citations for this assignment.

Assignment: {assignment_name}
Description: {assignment_description}

My topic/argument: {user_input}

Suggest what types of sources I should look for, where to find them, and how they would support my argument. Don't make up specific sources — tell me what to search for.""",
    }

    prompt = type_prompts.get(help_type, type_prompts["feedback"])

    try:
        return _ask_llm(system, prompt, max_tokens=1500)
    except Exception as e:
        print(f"Writing help error: {e}")
        return "Sorry, I couldn't generate a response. Please try again."


def generate_study_schedule(
    assignments: List[Dict],
    courses: List[Dict],
    preferences: Optional[str] = None,
) -> Dict:
    """
    Generate a study schedule based on upcoming deadlines.
    Returns a structured schedule with time blocks.
    """
    system = (
        "You are a study planner helping a college student manage their time. "
        "Create realistic, balanced study schedules. Include breaks. "
        "Return ONLY valid JSON — no markdown, no code fences."
    )

    assignment_text = ""
    for a in assignments[:20]:
        assignment_text += f"- {a['name']} ({a['course_name']}) — Due: {a.get('due_at', 'No date')} — {a.get('points_possible', '?')} pts — {'Submitted' if a.get('submitted') else 'Not submitted'}\n"

    prompt = f"""Create a study schedule for today and the next 3 days based on these upcoming assignments:

{assignment_text}

{f'Student preferences: {preferences}' if preferences else ''}

Return a JSON object with:
- "schedule": array of day objects, each with:
  - "date": "today", "tomorrow", or the day name
  - "blocks": array of study blocks, each with:
    - "time": suggested time (e.g., "9:00 AM - 10:30 AM")
    - "task": what to work on
    - "course": course name
    - "priority": "high", "medium", or "low"
    - "tip": a quick study tip for this task
- "summary": a 1-2 sentence overview of the plan
- "tips": array of 3 general study tips

Return ONLY the JSON object, nothing else."""

    try:
        text = _ask_llm(system, prompt, max_tokens=2500)
        return json.loads(_strip_code_fences(text))
    except Exception as e:
        print(f"Schedule generation error: {e}")
        return {"schedule": [], "summary": "Could not generate schedule", "tips": []}
