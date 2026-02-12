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
from sqlalchemy.orm import Session
from openai import OpenAI
from groq import Groq

# FacultyFlow v2.0 imports
from database import init_db, get_db, CanvasCredentials, UserCourse
from canvas_client import CanvasClient
from canvas_auth import CanvasAuth, encrypt_token, decrypt_token

# Initialize FastAPI
app = FastAPI(
    title="FacultyFlow API",
    description="AI Course Builder for Canvas",
    version="2.0.0"
)

# Database initialization on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    init_db()

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

# AI Clients - Support OpenAI, Groq (FREE!), and Anthropic
openai_client = None
groq_client = None
anthropic_client = None

# Initialize OpenAI (preferred - cheap and high quality)
if os.getenv("OPENAI_API_KEY"):
    try:
        openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        print("✅ OpenAI client initialized (GPT-4o-mini - $0.002/assignment)")
    except Exception as e:
        print(f"⚠️  OpenAI initialization failed: {e}")

# Initialize Groq (second choice - FREE!)
if os.getenv("GROQ_API_KEY"):
    try:
        groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        print("✅ Groq client initialized (Llama 3.3 70B - FREE!)")
    except Exception as e:
        print(f"⚠️  Groq initialization failed: {e}")
        print("   This is a known compatibility issue with Python 3.13")
        print("   Using OpenAI or Anthropic instead")

# Initialize Anthropic (fallback - expensive but highest quality)
if os.getenv("ANTHROPIC_API_KEY"):
    try:
        anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        print("✅ Anthropic client initialized (Claude Sonnet - $0.05/assignment)")
    except Exception as e:
        print(f"⚠️  Anthropic initialization failed: {e}")

if not openai_client and not groq_client and not anthropic_client:
    print("⚠️  No AI API keys found. AI features will not work.")
    print("   Set one of: OPENAI_API_KEY, GROQ_API_KEY, or ANTHROPIC_API_KEY")

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
    Supports: OpenAI (cheap), Groq (FREE!), Anthropic (premium)
    Provider priority: OpenAI > Groq > Anthropic
    """

    def __init__(self):
        self.openai_client = openai_client
        self.groq_client = groq_client
        self.anthropic_client = anthropic_client
        self.cost_tracker = {
            "syllabus": 0,
            "lesson_plans": 0,
            "quizzes": 0,
            "study_packs": 0,
            "total": 0
        }

    def call_ai(self, prompt: str, system: str = "") -> tuple[str, float]:
        """
        Call AI provider with automatic fallback
        Priority: OpenAI > Groq (FREE!) > Anthropic
        Returns: (response_text, cost)
        """
        # Try OpenAI first (cheapest paid option - $0.002/assignment)
        if self.openai_client:
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system} if system else {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=2048,
                    temperature=0.7
                )

                # Calculate cost for GPT-4o-mini
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens
                cost = (input_tokens / 1_000_000 * 0.15) + (output_tokens / 1_000_000 * 0.60)

                print(f"✅ OpenAI response (cost: ${cost:.4f})")
                return response.choices[0].message.content, cost
            except Exception as e:
                print(f"⚠️  OpenAI failed: {e}, trying Groq...")

        # Try Groq second (FREE! 🎉)
        if self.groq_client:
            try:
                response = self.groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",  # Fast, high quality, FREE!
                    messages=[
                        {"role": "system", "content": system} if system else {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=2048,
                    temperature=0.7
                )

                # Groq is FREE!
                cost = 0.0

                print(f"✅ Groq response (cost: FREE!)")
                return response.choices[0].message.content, cost
            except Exception as e:
                print(f"⚠️  Groq failed: {e}, falling back to Claude...")

        # Fallback to Claude (most expensive but highest quality)
        if self.anthropic_client:
            response = self.anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                system=system,
                messages=[{"role": "user", "content": prompt}]
            )

            # Calculate cost for Claude
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            cost = (input_tokens / 1_000_000 * 3) + (output_tokens / 1_000_000 * 15)

            print(f"✅ Claude response (cost: ${cost:.4f})")
            return response.content[0].text, cost

        raise Exception("No AI provider available. Please set OPENAI_API_KEY, GROQ_API_KEY, or ANTHROPIC_API_KEY")

    # Keep old method name for backward compatibility
    def call_claude(self, prompt: str, system: str = "") -> tuple[str, float]:
        """Alias for call_ai() for backward compatibility"""
        return self.call_ai(prompt, system)
    
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
# FACULTYFLOW V2.0 - CANVAS INTEGRATION
# ============================================================================

class CanvasConnectionRequest(BaseModel):
    canvas_url: str
    access_token: str

class QuizRequest(BaseModel):
    course_id: int
    topic: str
    num_questions: int = 10
    difficulty: str = "medium"
    due_date: Optional[str] = None

@app.post("/api/v2/canvas/connect")
async def connect_canvas_v2(
    request: CanvasConnectionRequest,
    db: Session = Depends(get_db)
):
    """
    Phase 1: Connect professor's Canvas account
    Saves encrypted credentials to database
    """
    try:
        # Aggressively clean inputs - remove ALL whitespace including hidden chars
        import re
        canvas_url = re.sub(r'\s+', '', request.canvas_url)  # Remove all whitespace
        access_token = re.sub(r'\s+', '', request.access_token)  # Remove all whitespace

        print(f"\n{'='*60}")
        print(f"CANVAS CONNECTION ATTEMPT")
        print(f"{'='*60}")
        print(f"Raw URL length: {len(request.canvas_url)}")
        print(f"Cleaned URL: {canvas_url}")
        print(f"Raw token length: {len(request.access_token)}")
        print(f"Cleaned token length: {len(access_token)}")
        print(f"Token first 15 chars: {access_token[:15]}...")
        print(f"Token last 10 chars: ...{access_token[-10:]}")

        # Validate URL format
        if not canvas_url.startswith('http'):
            print("❌ URL doesn't start with http")
            raise HTTPException(
                status_code=400,
                detail="Canvas URL must start with https:// (example: https://vuu.instructure.com)"
            )

        # Validate token format (Canvas tokens are typically 50-70 characters)
        if len(access_token) < 20:
            print("❌ Token too short")
            raise HTTPException(
                status_code=400,
                detail=f"Canvas API token seems too short ({len(access_token)} chars). Typical tokens are 50-70 characters. Please check you copied the full token."
            )

        # Check for suspicious characters
        if not re.match(r'^[A-Za-z0-9~_-]+$', access_token):
            suspicious_chars = re.findall(r'[^A-Za-z0-9~_-]', access_token)
            print(f"❌ Token contains suspicious characters: {suspicious_chars}")
            raise HTTPException(
                status_code=400,
                detail=f"Canvas token contains invalid characters. Please copy only the token (no quotes, spaces, or special characters)."
            )

        print(f"✓ URL format valid")
        print(f"✓ Token format valid")
        print(f"Attempting Canvas API connection...")

        # Test the connection
        canvas_auth = CanvasAuth(canvas_url, access_token)
        success, user_data, error_message = canvas_auth.test_connection()

        print(f"\nConnection result: {'✅ SUCCESS' if success else '❌ FAILED'}")
        if error_message:
            print(f"Error: {error_message}")

        if not success:
            raise HTTPException(
                status_code=401,
                detail=error_message or "Invalid Canvas credentials. Please check your URL and API token."
            )

        # Encrypt and save to database
        encrypted_token = encrypt_token(access_token)
        user_id = 1  # TODO: Use real user ID from authentication

        if db:
            # Check if credentials already exist
            existing = db.query(CanvasCredentials).filter_by(user_id=user_id).first()

            if existing:
                # Update existing
                existing.canvas_url = canvas_url
                existing.access_token_encrypted = encrypted_token
                existing.last_verified = datetime.utcnow()
            else:
                # Create new
                credentials = CanvasCredentials(
                    user_id=user_id,
                    canvas_url=canvas_url,
                    access_token_encrypted=encrypted_token
                )
                db.add(credentials)

            db.commit()

        return {
            "status": "connected",
            "canvas_url": canvas_url,
            "user_name": user_data.get("name") if user_data else "Unknown"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v2/canvas/courses")
async def get_courses_v2(
    db: Session = Depends(get_db)
):
    """
    Phase 1: Get professor's Canvas courses
    Returns list of courses they teach
    """
    try:
        user_id = 1  # TODO: Use real user ID from authentication

        # Get Canvas credentials from database
        if not db:
            raise HTTPException(status_code=500, detail="Database not available")

        credentials = db.query(CanvasCredentials).filter_by(user_id=user_id).first()

        if not credentials:
            raise HTTPException(
                status_code=404,
                detail="Canvas not connected. Please connect your Canvas account first."
            )

        # Decrypt token and fetch courses
        decrypted_token = decrypt_token(credentials.access_token_encrypted)
        canvas_client = CanvasClient(credentials.canvas_url, decrypted_token)

        courses = canvas_client.get_user_courses()

        # Cache courses in database
        for course in courses:
            existing = db.query(UserCourse).filter_by(
                user_id=user_id,
                course_id=course["id"]
            ).first()

            if existing:
                existing.course_name = course["name"]
                existing.course_code = course.get("course_code")
                existing.total_students = course.get("total_students")
                existing.synced_at = datetime.utcnow()
            else:
                user_course = UserCourse(
                    user_id=user_id,
                    course_id=course["id"],
                    course_name=course["name"],
                    course_code=course.get("course_code"),
                    total_students=course.get("total_students")
                )
                db.add(user_course)

        db.commit()

        return {
            "courses": courses,
            "total": len(courses)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v2/canvas/quiz")
async def create_quiz_v2(
    request: QuizRequest,
    db: Session = Depends(get_db)
):
    """
    Phase 2: Create quiz in Canvas course
    1. Generate quiz with Bonita AI
    2. Upload to Canvas
    3. Return preview URL
    """
    try:
        user_id = 1  # TODO: Use real user ID from authentication

        # Get Canvas credentials
        if not db:
            raise HTTPException(status_code=500, detail="Database not available")

        credentials = db.query(CanvasCredentials).filter_by(user_id=user_id).first()

        if not credentials:
            raise HTTPException(
                status_code=404,
                detail="Canvas not connected"
            )

        # Step 1: Generate quiz with Bonita AI
        print(f"🧠 Generating quiz on: {request.topic}")
        quiz_data = bonita.generate_quiz(1, request.topic)

        # Step 2: Upload to Canvas
        decrypted_token = decrypt_token(credentials.access_token_encrypted)
        canvas_client = CanvasClient(credentials.canvas_url, decrypted_token)

        quiz_title = f"Quiz: {request.topic}"
        quiz_id = canvas_client.create_quiz(
            course_id=request.course_id,
            quiz_data={
                "title": quiz_title,
                "quiz_type": "assignment",
                "time_limit": 20,
                "allowed_attempts": 1,
                "points_possible": request.num_questions * 10,
                "due_at": request.due_date
            }
        )

        if not quiz_id:
            raise HTTPException(status_code=500, detail="Failed to create quiz in Canvas")

        # Step 3: Add questions
        for i, question in enumerate(quiz_data.get("questions", []), 1):
            canvas_client.add_quiz_question(
                course_id=request.course_id,
                quiz_id=quiz_id,
                question_data={
                    "name": f"Question {i}",
                    "text": question["question_text"],
                    "type": "multiple_choice_question",
                    "points": 10,
                    "answers": [
                        {
                            "answer_text": ans["text"],
                            "answer_weight": 100 if ans.get("correct") else 0
                        }
                        for ans in question["answers"]
                    ]
                }
            )

        # Return success with preview URL
        preview_url = f"{credentials.canvas_url}/courses/{request.course_id}/quizzes/{quiz_id}"

        return {
            "status": "success",
            "quiz_id": quiz_id,
            "quiz_title": quiz_title,
            "questions_added": len(quiz_data.get("questions", [])),
            "preview_url": preview_url,
            "message": "Quiz created successfully! Review and publish in Canvas."
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class AIAssignmentRequest(BaseModel):
    topic: str
    assignment_type: str
    requirements: str
    points: int = 100


class AnnouncementRequest(BaseModel):
    course_id: int
    topic: str
    details: Optional[str] = None


class AIPageRequest(BaseModel):
    title: str
    page_type: str
    description: str
    objectives: Optional[str] = None


class PageRequest(BaseModel):
    course_id: int
    title: str
    content: str


class AssignmentRequest(BaseModel):
    course_id: int
    title: str
    description: str
    points: int = 100
    due_date: Optional[str] = None


class ModuleRequest(BaseModel):
    course_id: int
    name: str
    position: Optional[int] = None


class DiscussionRequest(BaseModel):
    course_id: int
    topic: str
    prompt: str


@app.post("/api/v2/canvas/announcement")
async def create_announcement_v2(
    request: AnnouncementRequest,
    # user=Depends(verify_token),  # TODO: Add auth back later
    db: Session = Depends(get_db)
):
    """Create an announcement in Canvas course"""
    try:
        user_id = 1  # TODO: Use real user ID from authentication

        # Get Canvas credentials
        if not db:
            raise HTTPException(status_code=500, detail="Database not available")

        credentials = db.query(CanvasCredentials).filter_by(user_id=user_id).first()
        if not credentials:
            raise HTTPException(status_code=404, detail="Canvas not connected")

        # Generate announcement with AI
        print(f"📢 Generating announcement on: {request.topic}")

        system = "You are Bonita, helping professors create course announcements."
        prompt = f"""Create a professional course announcement about: {request.topic}

{f'Additional details: {request.details}' if request.details else ''}

Make it:
- Professional but friendly
- Clear and concise (2-3 paragraphs max)
- Action-oriented if needed
- Formatted in HTML for Canvas

Return just the HTML content, no markdown code blocks."""

        announcement_html, _ = bonita.call_claude(prompt, system)

        # Upload to Canvas
        decrypted_token = decrypt_token(credentials.access_token_encrypted)
        canvas_client = CanvasClient(credentials.canvas_url, decrypted_token)

        result = canvas_client.create_announcement(
            course_id=request.course_id,
            announcement_data={
                "title": request.topic,
                "message": announcement_html
            }
        )

        if not result:
            raise HTTPException(status_code=500, detail="Failed to create announcement")

        preview_url = f"{credentials.canvas_url}/courses/{request.course_id}/discussion_topics/{result['id']}"

        return {
            "status": "success",
            "announcement_id": result["id"],
            "title": request.topic,
            "preview_url": preview_url,
            "message": "Announcement posted successfully!"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v2/canvas/generate-page")
async def generate_ai_page(
    request: AIPageRequest,
    db: Session = Depends(get_db)
):
    """
    Generate AI-enhanced course page content using Groq/OpenAI
    Returns professional page content with proper structure
    """
    try:
        print(f"🤖 Generating AI page: {request.title}")

        # Map page types to better descriptions
        type_descriptions = {
            "overview": "course or unit overview",
            "resource_list": "resource list with links and descriptions",
            "study_guide": "study guide with key concepts",
            "tutorial": "tutorial or how-to guide",
            "reading": "reading material or article",
            "reference": "reference material",
            "other": "informational page"
        }

        page_type_desc = type_descriptions.get(request.page_type, "course page")

        system = """You are Bonita, an AI assistant helping college professors create course pages.
Your output should be well-formatted HTML suitable for Canvas LMS.
Use clear structure, headers, lists, and proper formatting."""

        prompt = f"""Create a professional course page titled: {request.title}

Page Type: {page_type_desc}
Description: {request.description}
{f'Learning Objectives: {request.objectives}' if request.objectives else ''}

Generate comprehensive page content with:

1. **Introduction** (2-3 paragraphs explaining the topic and its importance)

2. **Main Content Sections** (organized with clear headings)
   - Break down the content logically
   - Use bullet points and numbered lists where appropriate
   - Include examples or explanations

3. **Key Takeaways** (3-5 bullet points summarizing main points)

4. **Resources** (optional but recommended)
   - Suggested readings
   - Helpful links
   - Additional materials

Format the output in clean HTML suitable for Canvas LMS. Use:
- <h3> for section headings
- <h4> for subsection headings
- <p> for paragraphs
- <ul> and <li> for bullet lists
- <ol> and <li> for numbered lists
- <strong> for emphasis
- <a href="..."> for links (if suggesting real resources)

Do NOT include the page title as an <h1> or <h2> (Canvas will add that).
Make it educational, engaging, and well-organized."""

        # Generate with AI
        generated_content, cost = bonita.call_ai(prompt, system)

        print(f"✅ Page generated (cost: ${cost:.4f})")

        return {
            "status": "success",
            "generated_content": generated_content,
            "cost": cost
        }

    except Exception as e:
        print(f"❌ Error generating page: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v2/canvas/page")
async def create_page_v2(
    request: PageRequest,
    # user=Depends(verify_token),  # TODO: Add auth back later
    db: Session = Depends(get_db)
):
    """Create a course page in Canvas"""
    try:
        user_id = 1  # TODO: Use real user ID from authentication

        # Get Canvas credentials
        if not db:
            raise HTTPException(status_code=500, detail="Database not available")

        credentials = db.query(CanvasCredentials).filter_by(user_id=user_id).first()
        if not credentials:
            raise HTTPException(status_code=404, detail="Canvas not connected")

        # Upload page to Canvas (content already provided)
        print(f"📄 Creating page: {request.title}")

        decrypted_token = decrypt_token(credentials.access_token_encrypted)
        canvas_client = CanvasClient(credentials.canvas_url, decrypted_token)

        result = canvas_client.create_page(
            course_id=request.course_id,
            page_data={
                "title": request.title,
                "content": request.content
            }
        )

        if not result:
            raise HTTPException(status_code=500, detail="Failed to create page")

        preview_url = f"{credentials.canvas_url}/courses/{request.course_id}/pages/{result['url']}"

        return {
            "status": "success",
            "page_url": result["url"],
            "title": request.title,
            "preview_url": preview_url,
            "message": "Page created successfully! Review and publish in Canvas."
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v2/canvas/generate-assignment")
async def generate_ai_assignment(
    request: AIAssignmentRequest,
    db: Session = Depends(get_db)
):
    """
    Generate AI-enhanced assignment content using Bonita
    Returns professional assignment description with instructions, objectives, rubric
    """
    try:
        print(f"🤖 Generating AI assignment: {request.topic}")

        # Map assignment types to better descriptions
        type_descriptions = {
            "essay": "essay or written paper",
            "discussion": "discussion post or forum response",
            "project": "project or presentation",
            "research": "research assignment",
            "case_study": "case study analysis",
            "lab": "lab or practical work",
            "reflection": "reflection assignment",
            "group": "group collaborative assignment",
            "other": "assignment"
        }

        assignment_type_desc = type_descriptions.get(request.assignment_type, "assignment")

        system = """You are Bonita, an AI assistant helping college professors create high-quality assignments.
Your output should be professional, clear, and properly formatted for Canvas LMS.
Use HTML formatting with headers, lists, and proper structure."""

        prompt = f"""Create a professional college assignment on: {request.topic}

Assignment Type: {assignment_type_desc}
Points: {request.points}
Professor's Requirements:
{request.requirements}

Generate a complete assignment description with the following sections:

1. **Assignment Overview** (2-3 paragraphs explaining what students will do and why it's important)

2. **Learning Objectives** (3-5 specific, measurable objectives students will achieve)

3. **Instructions** (Step-by-step directions for completing the assignment)

4. **Deliverables** (Specific list of what students must submit)

5. **Grading Rubric** (Clear criteria for how the assignment will be evaluated)

6. **Resources** (Suggested materials, readings, or tools students can use)

Format the output in clean HTML suitable for Canvas LMS. Use:
- <h3> for section headings
- <p> for paragraphs
- <ul> and <li> for lists
- <strong> for emphasis
- <table> for rubric (if applicable)

Keep it professional but engaging. Make instructions clear and actionable.
Do NOT include the assignment title as a heading (it will be added separately).
Focus on creating content that helps students succeed."""

        # Generate with Bonita AI
        generated_content, cost = bonita.call_claude(prompt, system)

        print(f"✅ Assignment generated (cost: ${cost:.4f})")

        return {
            "status": "success",
            "generated_content": generated_content,
            "cost": cost
        }

    except Exception as e:
        print(f"❌ Error generating assignment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v2/canvas/assignment")
async def create_assignment_v2(
    request: AssignmentRequest,
    # user=Depends(verify_token),  # TODO: Add auth back later
    db: Session = Depends(get_db)
):
    """Create an assignment in Canvas course"""
    try:
        user_id = 1  # TODO: Use real user ID from authentication

        # Get Canvas credentials
        if not db:
            raise HTTPException(status_code=500, detail="Database not available")

        credentials = db.query(CanvasCredentials).filter_by(user_id=user_id).first()
        if not credentials:
            raise HTTPException(status_code=404, detail="Canvas not connected")

        # Generate assignment description with AI if needed
        description = request.description
        if len(description) < 50:  # If description is too short, expand it with AI
            print(f"📝 Enhancing assignment description with AI")

            system = "You are Bonita, creating assignment descriptions for professors."
            prompt = f"""Create a detailed assignment description for: {request.title}

Brief description: {description}

Include:
- Assignment overview (what students will do)
- Learning objectives
- Submission requirements
- Grading criteria

Format in HTML for Canvas."""

            description, _ = bonita.call_claude(prompt, system)

        # Upload to Canvas
        decrypted_token = decrypt_token(credentials.access_token_encrypted)
        canvas_client = CanvasClient(credentials.canvas_url, decrypted_token)

        result = canvas_client.create_assignment(
            course_id=request.course_id,
            assignment_data={
                "title": request.title,
                "description": description,
                "points": request.points,
                "due_date": request.due_date
            }
        )

        if not result:
            raise HTTPException(status_code=500, detail="Failed to create assignment")

        preview_url = f"{credentials.canvas_url}/courses/{request.course_id}/assignments/{result['id']}"

        return {
            "status": "success",
            "assignment_id": result["id"],
            "title": request.title,
            "points": request.points,
            "preview_url": preview_url,
            "message": "Assignment created successfully! Review and publish in Canvas."
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v2/canvas/modules/{course_id}")
async def get_modules_v2(
    course_id: int,
    # user=Depends(verify_token),  # TODO: Add auth back later
    db: Session = Depends(get_db)
):
    """Get all modules in a course"""
    try:
        user_id = 1  # TODO: Use real user ID from authentication

        # Get Canvas credentials
        if not db:
            raise HTTPException(status_code=500, detail="Database not available")

        credentials = db.query(CanvasCredentials).filter_by(user_id=user_id).first()
        if not credentials:
            raise HTTPException(status_code=404, detail="Canvas not connected")

        decrypted_token = decrypt_token(credentials.access_token_encrypted)
        canvas_client = CanvasClient(credentials.canvas_url, decrypted_token)

        modules = canvas_client.get_modules(course_id)

        return {
            "modules": modules,
            "total": len(modules)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v2/canvas/module")
async def create_module_v2(
    request: ModuleRequest,
    # user=Depends(verify_token),  # TODO: Add auth back later
    db: Session = Depends(get_db)
):
    """Create a module in Canvas course"""
    try:
        user_id = 1  # TODO: Use real user ID from authentication

        # Get Canvas credentials
        if not db:
            raise HTTPException(status_code=500, detail="Database not available")

        credentials = db.query(CanvasCredentials).filter_by(user_id=user_id).first()
        if not credentials:
            raise HTTPException(status_code=404, detail="Canvas not connected")

        decrypted_token = decrypt_token(credentials.access_token_encrypted)
        canvas_client = CanvasClient(credentials.canvas_url, decrypted_token)

        result = canvas_client.create_module(
            course_id=request.course_id,
            module_data={
                "name": request.name,
                "position": request.position
            }
        )

        if not result:
            raise HTTPException(status_code=500, detail="Failed to create module")

        preview_url = f"{credentials.canvas_url}/courses/{request.course_id}/modules"

        return {
            "status": "success",
            "module_id": result["id"],
            "name": request.name,
            "preview_url": preview_url,
            "message": f"Module '{request.name}' created successfully!"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v2/canvas/discussion")
async def create_discussion_v2(
    request: DiscussionRequest,
    # user=Depends(verify_token),  # TODO: Add auth back later
    db: Session = Depends(get_db)
):
    """Create a discussion topic in Canvas course"""
    try:
        user_id = 1  # TODO: Use real user ID from authentication

        # Get Canvas credentials
        if not db:
            raise HTTPException(status_code=500, detail="Database not available")

        credentials = db.query(CanvasCredentials).filter_by(user_id=user_id).first()
        if not credentials:
            raise HTTPException(status_code=404, detail="Canvas not connected")

        # Generate discussion content with AI
        print(f"💬 Generating discussion: {request.topic}")

        system = "You are Bonita, creating discussion prompts for courses."
        prompt = f"""Create a discussion topic titled: {request.topic}

Prompt: {request.prompt}

Create an engaging discussion post that:
- Provides context for the discussion
- Asks thought-provoking questions (3-4 questions)
- Encourages student participation
- Is formatted in HTML for Canvas

Keep it concise but meaningful."""

        discussion_html, _ = bonita.call_claude(prompt, system)

        # Upload to Canvas
        decrypted_token = decrypt_token(credentials.access_token_encrypted)
        canvas_client = CanvasClient(credentials.canvas_url, decrypted_token)

        result = canvas_client.create_discussion(
            course_id=request.course_id,
            discussion_data={
                "title": request.topic,
                "message": discussion_html
            }
        )

        if not result:
            raise HTTPException(status_code=500, detail="Failed to create discussion")

        preview_url = f"{credentials.canvas_url}/courses/{request.course_id}/discussion_topics/{result['id']}"

        return {
            "status": "success",
            "discussion_id": result["id"],
            "title": request.topic,
            "preview_url": preview_url,
            "message": "Discussion created successfully! Review and publish in Canvas."
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

class AIDiscussionRequest(BaseModel):
    topic: str
    discussion_type: str
    goals: str


@app.post("/api/v2/canvas/generate-discussion")
async def generate_ai_discussion(request: AIDiscussionRequest):
    """Generate AI-enhanced discussion topic"""
    try:
        print(f"🤖 Generating AI discussion: {request.topic}")
        
        system = "You are Bonita, helping professors create engaging class discussions."
        prompt = f"""Create a discussion topic on: {request.topic}

Discussion Type: {request.discussion_type}
Learning Goals: {request.goals}

Generate an engaging discussion post that includes:

1. **Opening Prompt** (2-3 paragraphs that provide context and spark interest)

2. **Discussion Questions** (3-5 thought-provoking questions that encourage critical thinking)

3. **Participation Guidelines** (How students should engage - length, citations, peer responses)

4. **Expected Outcomes** (What students should gain from this discussion)

Format in HTML for Canvas. Make it engaging and encourage meaningful dialogue."""

        content, cost = bonita.call_ai(prompt, system)
        print(f"✅ Discussion generated (cost: ${cost:.4f})")
        return {"status": "success", "generated_content": content, "cost": cost}
    except Exception as e:
        print(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
