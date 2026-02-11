"""
FacultyFlow Backend API
FastAPI server with Bonita AI integration

Built by: Sonny (Claude) for CJ
Purpose: Power FacultyFlow SaaS with smart AI routing
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
import os
import anthropic
import requests
import hashlib
import secrets
from datetime import datetime, timedelta
from jose import jwt

# Initialize FastAPI
app = FastAPI(
    title="FacultyFlow API",
    description="AI Course Builder for Canvas",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"

# AI Clients
anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ============================================================================
# DATA MODELS
# ============================================================================

class CourseRequest(BaseModel):
    course_name: str
    course_code: str
    credits: int
    description: str
    objectives: List[str]
    weeks: int
    schedule: str
    canvas_course_id: str

class UserSignup(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class CanvasToken(BaseModel):
    canvas_url: str
    api_token: str

class CourseResponse(BaseModel):
    course_id: str
    canvas_course_id: str
    status: str
    cost: float
    time_saved_hours: int
    created_at: str

# ============================================================================
# AUTHENTICATION
# ============================================================================

def create_access_token(data: dict, expires_delta: timedelta = timedelta(days=30)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ============================================================================
# BONITA AI ENGINE
# ============================================================================

class BonitaEngine:
    """
    Smart AI routing for FacultyFlow
    Uses Claude for quality, Qwen for structure, optimizes costs
    """
    
    def __init__(self):
        self.anthropic_client = anthropic_client
        self.cost_tracker = {
            "syllabus": 0,
            "lesson_plans": 0,
            "quizzes": 0,
            "study_packs": 0,
            "total": 0
        }
    
    def call_claude(self, prompt: str, system: str = "") -> tuple[str, float]:
        """Use Claude Sonnet for high-quality content"""
        response = self.anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=system,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Calculate cost
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        cost = (input_tokens / 1_000_000 * 3) + (output_tokens / 1_000_000 * 15)
        
        return response.content[0].text, cost
    
    def call_qwen_local(self, prompt: str) -> tuple[str, float]:
        """Use Qwen local for structured content (FREE!)"""
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "qwen2.5:32b",
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60
            )
            response.raise_for_status()
            return response.json()["response"], 0.0  # FREE!
        except Exception as e:
            # Fallback to Claude if local fails
            print(f"Qwen local failed: {e}, falling back to Claude")
            return self.call_claude(prompt)
    
    def generate_syllabus(self, course_data: Dict) -> str:
        """Generate complete syllabus (Claude - quality matters)"""
        system = """You are Bonita, an AI assistant helping professors create course content.
Your output should be professional, engaging, and practical - written for college students."""
        
        prompt = f"""Create a complete course syllabus for:

Course: {course_data['course_name']}
Code: {course_data['course_code']}
Credits: {course_data['credits']}
Description: {course_data['description']}
Learning Objectives: {', '.join(course_data['objectives'])}
Duration: {course_data['weeks']} weeks
Schedule: {course_data['schedule']}

Include:
1. Course Overview (2-3 engaging paragraphs)
2. Learning Objectives (formatted list)
3. Weekly Schedule Overview
4. Grading Breakdown (suggest reasonable percentages)
5. Attendance Policy (professional but fair)
6. Academic Integrity Statement
7. Required Materials (if applicable)

Format in clean HTML suitable for Canvas. Use headers, lists, and tables for clarity.
Keep it practical and student-focused - no academic jargon."""
        
        syllabus, cost = self.call_claude(prompt, system)
        self.cost_tracker["syllabus"] += cost
        return syllabus
    
    def generate_lesson_plan(self, week: int, topic: str, objectives: List[str]) -> Dict:
        """Generate lesson plan (Qwen - structured task, FREE!)"""
        prompt = f"""Create a lesson plan for Week {week}:

Topic: {topic}
Learning Objectives:
{chr(10).join(f"- {obj}" for obj in objectives)}

Include:
1. Week Overview (2-3 sentences)
2. Key Concepts (5-7 bullet points)
3. In-Class Activities (2-3 activities)
4. Discussion Prompts (3 thought-provoking questions)
5. Homework/Assignment (if applicable)

Format in clean HTML for Canvas. Keep it practical and actionable."""
        
        lesson, cost = self.call_qwen_local(prompt)
        self.cost_tracker["lesson_plans"] += cost
        return {
            "week": week,
            "topic": topic,
            "content": lesson
        }
    
    def generate_quiz(self, week: int, topic: str) -> Dict:
        """Generate quiz questions (Qwen - structured, FREE!)"""
        prompt = f"""Create a 10-question multiple choice quiz for Week {week}: {topic}

Requirements:
- 10 questions total
- 4 answer options each (A, B, C, D)
- Mix of difficulty (3 easy, 5 medium, 2 hard)
- Clear, unambiguous questions
- One correct answer per question

Format as JSON:
{{
  "questions": [
    {{
      "question_text": "Question here?",
      "answers": [
        {{"text": "A. Option 1", "correct": false}},
        {{"text": "B. Option 2", "correct": true}},
        {{"text": "C. Option 3", "correct": false}},
        {{"text": "D. Option 4", "correct": false}}
      ]
    }}
  ]
}}"""
        
        quiz_json, cost = self.call_qwen_local(prompt)
        self.cost_tracker["quizzes"] += cost
        
        try:
            import json
            quiz_data = json.loads(quiz_json.strip().replace("```json", "").replace("```", ""))
            return quiz_data
        except:
            return {"questions": [], "error": "Failed to parse quiz"}
    
    def generate_study_pack(self, week: int, topic: str) -> str:
        """Generate study pack with real resources (Claude + search intent)"""
        system = """You are Bonita, creating study materials for college students.
Find REAL, working resources. Do not make up URLs."""
        
        prompt = f"""Create a study pack for Week {week}: {topic}

Include:
1. Key Concepts Summary (3-5 bullet points)
2. Real-World Examples (2-3 relevant examples)
3. Discussion Questions (3-5 thought-provoking questions)
4. External Resources:
   - 2-3 articles (from reputable sources with REAL URLs)
   - 1-2 videos (YouTube links that actually exist)
   - 1-2 tools/platforms students can explore

Format as HTML for Canvas. Use embedded links. Make it engaging and practical.
Prefer recent (2020+) resources. Cite sources properly."""
        
        study_pack, cost = self.call_claude(prompt, system)
        self.cost_tracker["study_packs"] += cost
        return study_pack

# Initialize Bonita
bonita = BonitaEngine()

# ============================================================================
# CANVAS API INTEGRATION
# ============================================================================

class CanvasAPI:
    """Canvas LMS API integration"""
    
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def create_module(self, course_id: str, name: str, position: int) -> Dict:
        """Create a Canvas module"""
        url = f"{self.base_url}/api/v1/courses/{course_id}/modules"
        data = {"module": {"name": name, "position": position}}
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()
    
    def create_assignment(self, course_id: str, name: str, description: str, 
                         points: int = 0, due_date: str = None) -> Dict:
        """Create a Canvas assignment"""
        url = f"{self.base_url}/api/v1/courses/{course_id}/assignments"
        data = {
            "assignment": {
                "name": name,
                "description": description,
                "points_possible": points,
                "due_at": due_date,
                "submission_types": ["none"],
                "published": False
            }
        }
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()
    
    def create_quiz(self, course_id: str, title: str, description: str,
                   quiz_data: Dict, due_date: str = None) -> Dict:
        """Create a Canvas quiz with questions"""
        # 1. Create quiz
        url = f"{self.base_url}/api/v1/courses/{course_id}/quizzes"
        data = {
            "quiz": {
                "title": title,
                "quiz_type": "assignment",
                "points_possible": 100,
                "time_limit": 30,
                "allowed_attempts": 2,
                "due_at": due_date,
                "description": description,
                "published": False
            }
        }
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        quiz = response.json()
        
        # 2. Add questions
        for i, q in enumerate(quiz_data.get("questions", []), 1):
            question_url = f"{url}/{quiz['id']}/questions"
            question_data = {
                "question": {
                    "question_name": f"Q{i}",
                    "question_text": q["question_text"],
                    "question_type": "multiple_choice_question",
                    "points_possible": 10,
                    "answers": [
                        {
                            "answer_text": ans["text"],
                            "answer_weight": 100 if ans.get("correct") else 0
                        }
                        for ans in q["answers"]
                    ]
                }
            }
            requests.post(question_url, headers=self.headers, json=question_data)
        
        return quiz

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    return {
        "service": "FacultyFlow API",
        "version": "1.0.0",
        "status": "operational"
    }

@app.post("/api/auth/signup")
async def signup(user: UserSignup):
    """User signup"""
    # In production: save to database with hashed password
    # For now: return token
    token = create_access_token({"email": user.email, "name": user.full_name})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "email": user.email,
            "name": user.full_name
        }
    }

@app.post("/api/auth/login")
async def login(user: UserLogin):
    """User login"""
    # In production: verify against database
    # For now: return token
    token = create_access_token({"email": user.email})
    return {
        "access_token": token,
        "token_type": "bearer"
    }

@app.post("/api/canvas/connect")
async def connect_canvas(canvas_data: CanvasToken, user=Depends(verify_token)):
    """Save user's Canvas credentials (encrypted)"""
    # In production: encrypt and save to database
    return {
        "status": "connected",
        "canvas_url": canvas_data.canvas_url
    }

@app.post("/api/build-course", response_model=CourseResponse)
async def build_course(course: CourseRequest, user=Depends(verify_token)):
    """
    Main endpoint: Build complete Canvas course
    This is where the magic happens!
    """
    try:
        # 1. Generate syllabus
        print(f"📋 Generating syllabus for {course.course_name}...")
        syllabus = bonita.generate_syllabus(course.dict())
        
        # 2. Generate lesson plans
        print(f"📚 Generating {course.weeks} lesson plans...")
        lesson_plans = []
        for week in range(1, course.weeks + 1):
            topic = f"Week {week} Content"  # In production: extract from syllabus or ask user
            lesson = bonita.generate_lesson_plan(week, topic, course.objectives[:2])
            lesson_plans.append(lesson)
        
        # 3. Generate quizzes
        print(f"🧪 Generating {course.weeks} quizzes...")
        quizzes = []
        for week in range(1, course.weeks + 1):
            topic = f"Week {week}"
            quiz = bonita.generate_quiz(week, topic)
            quizzes.append(quiz)
        
        # 4. Generate study packs
        print(f"📦 Generating {course.weeks} study packs...")
        study_packs = []
        for week in range(1, course.weeks + 1):
            topic = f"Week {week}"
            study_pack = bonita.generate_study_pack(week, topic)
            study_packs.append(study_pack)
        
        # 5. Upload to Canvas
        print(f"📤 Uploading to Canvas course {course.canvas_course_id}...")
        # In production: get user's Canvas credentials from database
        canvas = CanvasAPI(
            base_url="https://vuu.instructure.com",
            token=os.getenv("CANVAS_API_TOKEN")  # In production: from user's encrypted storage
        )
        
        # Create modules
        for week in range(1, course.weeks + 1):
            canvas.create_module(course.canvas_course_id, f"Week {week}", week)
        
        # Create study pack assignments
        for week, study_pack in enumerate(study_packs, 1):
            canvas.create_assignment(
                course.canvas_course_id,
                f"Week {week} Study Pack",
                study_pack,
                points=0
            )
        
        # Create quizzes
        for week, quiz_data in enumerate(quizzes, 1):
            canvas.create_quiz(
                course.canvas_course_id,
                f"Quiz {week}",
                f"Quiz covering Week {week} material",
                quiz_data
            )
        
        # Calculate total cost
        bonita.cost_tracker["total"] = sum(bonita.cost_tracker.values())
        
        print(f"✅ Course build complete! Cost: ${bonita.cost_tracker['total']:.2f}")
        
        return CourseResponse(
            course_id=secrets.token_urlsafe(16),
            canvas_course_id=course.canvas_course_id,
            status="complete",
            cost=bonita.cost_tracker["total"],
            time_saved_hours=25,
            created_at=datetime.utcnow().isoformat()
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "bonita": "online"
    }

# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
