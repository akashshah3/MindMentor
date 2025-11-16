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
