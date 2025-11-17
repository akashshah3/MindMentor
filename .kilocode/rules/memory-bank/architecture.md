# System Architecture

## High-Level Architecture

MindMentor follows a **monolithic Streamlit application** architecture for the MVP, with plans to separate components as needed for scale.

```
┌─────────────────────────────────────────────────────────┐
│                  Streamlit Application                  │
│  ┌───────────┐  ┌──────────┐  ┌────────────────────┐  │
│  │    UI     │  │ Business │  │   LLM Integration  │  │
│  │Components │←→│  Logic   │←→│  (Gemini API)      │  │
│  └───────────┘  └──────────┘  └────────────────────┘  │
│         ↓              ↓                               │
│  ┌───────────────────────────────────────┐            │
│  │      Data Access Layer                │            │
│  └───────────────────────────────────────┘            │
└──────────────────────┬──────────────────────────────────┘
                       ↓
              ┌────────────────┐
              │ SQLite Database│
              └────────────────┘
```

## Component Architecture

### 1. Frontend Layer (Streamlit UI)

**Purpose**: User interface for all interactions

**Key Components**:
- **Dashboard View**: Progress tracking, performance metrics, topic mastery
- **Learning View**: Interactive lessons, chat interface with AI tutor
- **Quiz View**: Test interface with timer, question display, answer input
- **Schedule View**: Study plan display and calendar
- **Assessment View**: Results analysis, weak areas, recommendations

**Technology**: Streamlit components, session state management

### 2. Business Logic Layer

**Purpose**: Core application logic and orchestration

**Key Modules**:

- **Authentication Module**
  - User registration and login
  - Password hashing (bcrypt)
  - Session management
  - Basic access control

- **Teaching Engine**
  - Generates lesson content via LLM (using Gemini 2.5 Flash for cost efficiency)
  - Manages conversation context
  - Adapts explanations based on student profile
  - Handles Q&A interactions
  - **Aggressive caching** of generated content to minimize API calls

- **Quiz Generator**
  - Creates questions from learned content
  - Generates MCQ distractors
  - Manages difficulty levels
  - Applies adaptive selection algorithms
  - Uses Gemini 2.5 Flash or Flash Lite based on complexity
  - Caches generated questions

- **Assessment Engine**
  - Grades objective answers (MCQ, numeric) - no LLM needed
  - LLM-based rubric scoring for descriptive answers (Gemini 2.5 Pro only when necessary)
  - Tracks attempt timing
  - Calculates performance metrics
  - Prefers rule-based grading to minimize API usage

- **Learning Analyzer**
  - Tracks student behavior patterns
  - Computes mastery scores per topic
  - Identifies weak areas
  - Calculates attention/focus metrics
  - Generates learning profile

- **Schedule Generator**
  - Creates personalized study plans
  - Implements spaced repetition (SM-2 algorithm)
  - Balances new learning and revision
  - Dynamically adjusts based on progress

- **Explainability Module**
  - Provides insights into performance
  - Uses simple ML models + SHAP for explanations
  - Generates actionable recommendations

### 3. LLM Integration Layer

**Purpose**: Manage all interactions with Gemini API

**Critical Constraint**: Limited API budget requires smart usage strategies

**Responsibilities**:
- Prompt template management
- API call handling with retry logic
- Response parsing and validation
- Token usage tracking and limiting
- **Aggressive caching** of all responses
- **Smart model selection** (Pro vs Flash vs Flash Lite)
- Batch request handling
- Cache hit/miss monitoring

**Model Selection Strategy**:
- **Gemini 2.5 Pro**: Only for complex descriptive answer grading
- **Gemini 2.5 Flash**: Lesson generation, standard question generation
- **Gemini 2.5 Flash Lite**: Simple explanations, hints, quick responses

**Key Prompt Templates**:
- Lesson content generation (Flash)
- Question generation (Flash/Flash Lite)
- Answer grading - descriptive (Pro)
- Hint generation (Flash Lite)
- Simplification/re-explanation (Flash Lite)

### 4. Data Access Layer

**Purpose**: Abstract database operations

**Key Operations**:
- User authentication (login, registration, password verification)
- User profile CRUD
- Topic and lesson management
- Quiz attempt storage and retrieval
- Schedule operations
- Analytics queries
- LLM response cache management

### 5. Persistence Layer (SQLite)

**Database Schema**:

```sql
-- User authentication and profiles
users (
  id INTEGER PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  name TEXT NOT NULL,
  exam_target TEXT, -- 'JEE_MAIN' or 'JEE_ADVANCED'
  daily_hours REAL,
  created_at TIMESTAMP,
  last_login TIMESTAMP
)

-- Topics in the JEE syllabus (Physics, Chemistry, Math)
topics (
  id INTEGER PRIMARY KEY,
  subject TEXT NOT NULL, -- 'Physics', 'Chemistry', 'Mathematics'
  name TEXT NOT NULL,
  exam_weight REAL,
  prerequisites TEXT -- JSON array of topic IDs
)

-- Cached LLM responses (CRITICAL for API cost control)
llm_cache (
  id INTEGER PRIMARY KEY,
  cache_key TEXT UNIQUE NOT NULL, -- hash of (prompt_template, topic, difficulty, model)
  model_used TEXT, -- 'gemini-2.5-pro', 'gemini-2.5-flash', 'gemini-2.5-flash-lite'
  response_content TEXT,
  created_at TIMESTAMP,
  last_accessed TIMESTAMP,
  access_count INTEGER DEFAULT 1
)

-- Cached lesson content
lessons (
  id INTEGER PRIMARY KEY,
  topic_id INTEGER,
  content_ref TEXT, -- reference to llm_cache
  difficulty TEXT,
  created_at TIMESTAMP
)

-- Quiz attempts
attempts (
  id INTEGER PRIMARY KEY,
  user_id INTEGER,
  topic_id INTEGER,
  question_id INTEGER,
  correctness BOOLEAN,
  score REAL,
  time_taken REAL, -- seconds
  timestamp TIMESTAMP
)

-- Quizzes
quizzes (
  id INTEGER PRIMARY KEY,
  user_id INTEGER,
  topics TEXT, -- JSON array
  total_score REAL,
  timestamp TIMESTAMP
)

-- Study schedules
schedules (
  id INTEGER PRIMARY KEY,
  user_id INTEGER,
  date DATE,
  planned_items TEXT, -- JSON: [{topic_id, activity_type, duration}]
  completed BOOLEAN
)

-- Student learning profile
student_profiles (
  id INTEGER PRIMARY KEY,
  user_id INTEGER,
  topic_id INTEGER,
  mastery_score REAL,
  last_attempt_date DATE,
  accuracy REAL,
  avg_time REAL,
  revision_count INTEGER,
  weak_concepts TEXT -- JSON array
)
```

## Key Design Patterns

### 1. Authentication & Session Management
- Basic username/password authentication with bcrypt hashing
- Streamlit session state stores authenticated user
- Session timeout after inactivity
- Protected routes (redirect to login if not authenticated)

### 2. Session State Management
- Streamlit session state stores current user context
- Active quiz state, current lesson, navigation history
- Temporary data before persistence

### 3. Prompt Engineering Pattern
- Template-based prompts with variable substitution
- Include student profile context in prompts
- Few-shot examples for consistent output
- JSON-structured responses from LLM
- **Model-specific templates** optimized for each Gemini variant

### 4. LLM Response Caching Strategy (CRITICAL)
```python
def get_or_generate_content(prompt_template, params, model='gemini-2.5-flash'):
    # Generate cache key from template + params
    cache_key = hash(f"{prompt_template}:{params}:{model}")
    
    # Check cache first
    cached = db.get_from_llm_cache(cache_key)
    if cached:
        db.update_cache_access(cache_key)  # Track usage
        return cached
    
    # Cache miss - call LLM (cost incurred)
    response = llm_client.generate(model, prompt_template.format(**params))
    
    # Store in cache with long TTL
    db.store_in_llm_cache(cache_key, response, model)
    
    return response
```

**Caching Rules**:
- Cache ALL LLM responses indefinitely
- Cache by (prompt_template, topic, difficulty, model)
- Track cache hit rate (target: >80%)
- Invalidate only when content is incorrect
- Share cache across students with similar profiles

### 5. Adaptive Selection Algorithm
```
Question Selection Weight = 
  (1 - mastery_score) × topic_weight × recency_factor
  
where:
  - mastery_score: 0-1, student's competency in topic
  - topic_weight: exam importance weight (JEE weightage per topic)
  - recency_factor: higher for recently studied topics
```

### 6. Spaced Repetition (SM-2)
- Track ease factor per topic
- Calculate next review interval
- Integrate into schedule generation

### 6. Explainability via Simple ML
- Train lightweight model (logistic regression/XGBoost)
- Features: recent accuracy, time spent, revision gap, mastery
- Predict: failure probability on next quiz
- Apply SHAP for feature importance
- Translate to human-readable insights
- **Note**: ML training doesn't require LLM API calls

## Source Code Structure (Planned)

```
mindmentor/
├── app.py                 # Main Streamlit entry point (login/routing)
├── pages/                 # Streamlit pages
│   ├── login.py          # Authentication
│   ├── register.py       # User registration
│   ├── dashboard.py      # Main dashboard (authenticated)
│   ├── learn.py
│   ├── quiz.py
│   ├── schedule.py
│   └── assessment.py
├── core/                  # Business logic
│   ├── auth.py           # Authentication logic
│   ├── teaching.py
│   ├── quiz_generator.py
│   ├── grading.py
│   ├── analyzer.py
│   ├── scheduler.py
│   └── explainer.py
├── llm/                   # LLM integration
│   ├── client.py         # Gemini API client with model selection
│   ├── prompts.py        # Prompt templates
│   ├── cache.py          # Cache management (CRITICAL)
│   └── models.py         # Model selection logic
├── data/                  # Data access
│   ├── db.py             # Database operations
│   ├── models.py         # Data models
│   ├── schema.sql        # Database schema
│   └── seed_jee.py       # Seed JEE syllabus data
│   ├── models.py
│   └── schema.sql
├── utils/                 # Utilities
│   ├── config.py
│   └── helpers.py
├── tests/                 # Test suite
├── requirements.txt       # Python dependencies
└── README.md
```

## Critical Implementation Paths

### Path 0: Authentication
1. User navigates to app
2. Check if authenticated (session state)
3. If not, redirect to login page
4. Validate credentials, hash password
5. Create session, store user_id
6. Redirect to dashboard

### Path 1: Teaching & Learning (API-intensive, requires caching)
1. User (authenticated) selects JEE topic
2. Teaching engine checks cache for lesson content
3. **Cache hit**: Return cached content (no API call)
4. **Cache miss**: Generate via LLM (Gemini 2.5 Flash), store in cache
5. Content displayed in chat interface
6. User asks questions
7. System checks cache for similar Q&A
8. Generate answer if needed (Flash Lite for simple, Flash for complex)
9. Student profile updated based on interaction

### Path 2: Quiz & Assessment (Minimize API calls)
1. Quiz generator selects JEE topics based on recent learning + weak areas
2. **Check cache** for similar quizzes
3. **Cache miss**: Generate questions via LLM (Gemini 2.5 Flash) with difficulty calibration
4. Present questions with timer
5. Capture answers and timing
6. Grade using appropriate method:
   - MCQ/Numeric: Rule-based (no API call)
   - Descriptive: LLM rubric (Gemini 2.5 Pro) - only if necessary
7. Store attempt in database
8. Update student profile and mastery scores
9. Display results with explanations (cache explanation generation)

### Path 3: Adaptive Planning (No API calls)
1. Gather user inputs (JEE Main/Advanced, time available, familiarity with Physics/Chem/Math)
2. Calculate topic priorities (JEE weight × weakness)
3. Apply spaced repetition for review items
4. Generate daily schedule
5. Track completion
6. Recalculate and adjust based on progress
7. Update schedule in database

## Technical Constraints

1. **LLM API Costs**: LIMITED BUDGET - Must aggressively cache and minimize unnecessary calls
2. **Response Time**: LLM calls can be slow (2-10s); need loading indicators and async where possible
3. **SQLite Limitations**: Single-file DB, no concurrent writes at scale (acceptable for MVP)
4. **Streamlit State**: Session state is in-memory; doesn't persist across restarts (store auth in session)
5. **Offline Operation**: Requires internet for LLM API calls (future: pre-generated content for offline)
6. **Authentication**: Basic auth (not OAuth) - simple but less secure than enterprise solutions

## Future Architecture Considerations

When scaling beyond MVP:

1. **Separate Backend**: FastAPI/Flask service with REST/GraphQL API
2. **Database Migration**: Move to PostgreSQL for better concurrency
3. **Caching Layer**: Redis for session management and LLM response cache
4. **Vector DB**: Add Pinecone/Weaviate for semantic search and answer matching
5. **Queue System**: Celery for background processing (schedule recalculation)
6. **Authentication**: Add user auth with JWT tokens
7. **Multi-tenancy**: Support for multiple institutions/user groups
8. **Analytics Platform**: Separate analytics DB for reporting

## Current Implementation Status

### ✅ Completed Modules

#### Authentication System
- **Files**: `src/core/auth.py`, `src/pages/login.py`, `src/pages/register.py`
- **Features**:
  - User registration with validation
  - Login with bcrypt password hashing
  - Session management via Streamlit session state
  - Password security enforcement
  - Session persistence across pages
- **Database**: `users` table with secure password storage

#### LLM Integration Layer
- **Files**: `src/llm/client.py`, `src/llm/models.py`, `src/llm/cache.py`, `src/llm/prompts.py`
- **Features**:
  - Gemini 2.5 API client with three models (Pro, Flash, Flash Lite)
  - Smart model selection based on task complexity
  - Aggressive caching system (80%+ hit rate achieved)
  - SHA256-based cache keys
  - Retry logic with exponential backoff
  - Token limit enforcement (8192 for lessons, 4096 default)
  - JSON response parsing with markdown code block handling
  - Convenience functions: `generate_lesson()`, `generate_questions()`, `generate_hint()`
- **Database**: `llm_cache` table with access tracking
- **Tested**: All tests passing with cache hit rate monitoring

#### Teaching/Learning Module
- **Files**: `src/pages/learn.py`
- **Features**:
  - Topic selection UI with 62 JEE topics organized by subject/chapter
  - Subject tabs (Physics, Chemistry, Mathematics)
  - Difficulty badges (Easy, Medium, Hard)
  - AI-generated lessons with structured content (explanations, examples, formulas, tips)
  - Interactive chat Q&A interface
  - Context-aware responses using conversation history
  - Chat history persistence in database
  - Progress tracking in `student_profiles` table
  - Topic completion marking with mastery scores
  - Session state management for smooth navigation
  - Auto-save on session end
- **Database**: `chat_history`, `student_profiles` tables
- **Implementation Notes**:
  - Chat Q&A uses direct API calls (no caching for conversational context)
  - Conversation history limited to last 10 messages
  - Database commits happen BEFORE `st.rerun()` to prevent transaction loss
  - Uses `generate_lesson()` for initial content with caching

#### Quiz Generation System
- **Files**: `src/core/quiz_generator.py`
- **Features**:
  - `QuizGenerator` class with adaptive quiz generation
  - Three question types: MCQ, Numeric, Descriptive
  - Adaptive difficulty calculation based on `student_profiles.mastery_score`
  - Topic selection with multi-select support
  - Question count and type distribution configuration
  - Time limit calculation (2min/MCQ, 3min/Numeric, 5min/Descriptive)
  - LLM-based question generation using Gemini Flash (temperature=0.8 for variety)
  - Question caching via `TaskType.QUESTION_GENERATION`
  - Database persistence to `quizzes` and `questions` tables
  - JSON serialization for options and correct answers
- **Implementation Details**:
  - `generate_quiz()` - Main quiz generation method
  - `_generate_questions_by_type()` - Type-specific generation with LLM
  - `get_adaptive_difficulty()` - Determines Easy/Medium/Hard based on performance
  - `save_quiz()` - Persists quiz and questions with proper JSON handling
  - `_calculate_time_limit()` - Allocates time per question type

#### Grading System
- **Files**: `src/core/grading.py`
- **Features**:
  - `GradingEngine` class with multi-strategy grading
  - Rule-based grading for MCQ (exact string matching) - no API cost
  - Rule-based grading for Numeric (tolerance-based with partial credit) - no API cost
  - LLM-based grading for Descriptive using Gemini Pro (temperature=0.3)
  - Keyword matching fallback for descriptive if LLM fails
  - Partial credit support (50% for numeric answers within 0.5% tolerance)
  - Quiz-level grading with score aggregation
  - Detailed feedback generation per question
  - Database persistence to `quiz_attempts` table
- **Implementation Details**:
  - `grade_answer()` - Routes to appropriate grading method
  - `_grade_mcq()` - Case-insensitive exact matching
  - `_grade_numeric()` - Tolerance checking with partial credit logic
  - `_grade_descriptive()` - LLM-based with structured feedback (score, strengths, improvements)
  - `_grade_descriptive_fallback()` - Keyword-based backup grading
  - `grade_quiz()` - Grades entire quiz and calculates percentage
  - `_save_quiz_attempt()` - Persists results with timestamp

#### Quiz Interface
- **Files**: `src/pages/quiz.py`
- **Features**:
  - Three-mode interface: select, taking, results
  - Topic selection with multi-checkbox UI organized by subject
  - Quiz configuration: question count slider, difficulty selector, question type toggles
  - Real-time timer countdown display
  - Question-by-question rendering with appropriate input types:
    - Radio buttons for MCQ with formatted options
    - Number input for Numeric questions
    - Text area for Descriptive questions
  - Answer collection in session state
  - Submit validation (warn on unanswered questions)
  - Results display with:
    - Overall score metrics (total, percentage, correct count, time)
    - Performance indicator (Excellent/Good/Review needed)
    - Question-wise breakdown with expandable details
    - Feedback per question
    - Correct answers for wrong responses
  - Navigation buttons: Try Another Quiz, Review Topics, View Dashboard
- **Session State Management**:
  - `quiz_mode` - Tracks current interface mode
  - `current_quiz` - Stores active quiz data
  - `quiz_start_time` - Timer reference
  - `student_answers` - Collects user responses
  - `quiz_results` - Stores grading output
- **Integration**: Uses `QuizGenerator` and `GradingEngine` classes

#### Application Routing
- **Files**: `app.py`
- **Features**:
  - Main entry point with page routing
  - Sidebar navigation (Dashboard, Learn, Practice)
  - Session state initialization
  - Authentication checks on all routes
  - Page imports: `show_login_page`, `show_registration_page`, `show_dashboard`, `show_learn_page`, `show_quiz_page`

### ⏳ Pending Modules

#### Enhanced Analytics Dashboard
- **Planned File**: `src/pages/dashboard.py` (update existing)
- **Features to Add**:
  - Quiz performance graphs (score trends over time)
  - Topic mastery heatmap visualization
  - Study time tracking per topic
  - Weak area identification and recommendations
  - Recent activity timeline
  - Comparative performance metrics

#### Study Scheduler
- **Planned Files**: `src/core/scheduler.py`, `src/pages/schedule.py`
- **Features to Add**:
  - Automated schedule generation based on available time
  - Spaced repetition using SM-2 algorithm
  - Topic prioritization (JEE weight × weakness)
  - Calendar UI with daily tasks
  - Progress tracking against schedule
  - Dynamic schedule adjustment based on quiz performance

#### Test Suite
- **Planned Files**: `tests/test_quiz.py`, `tests/test_grading.py`
- **Features to Add**:
  - Unit tests for quiz generation logic
  - Grading accuracy tests for all question types
  - Integration tests for quiz flow
  - Edge case handling tests

