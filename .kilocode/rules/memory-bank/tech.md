# Technology Stack

## Core Technologies

### Frontend Framework
**Streamlit** (Python-based web framework)
- **Version**: Latest stable (3.x+)
- **Why**: Rapid prototyping, Python-native, built-in UI components
- **Use**: Entire user interface, pages, components, state management
- **Limitations**: Less customizable than React/Vue, limited real-time features

### Backend Language
**Python** 3.10+
- **Why**: Rich ML/AI ecosystem, Streamlit requirement, rapid development
- **Libraries**: Standard library, asyncio for async operations

### Database
**SQLite** (for MVP)
- **Why**: Zero-config, single-file, perfect for prototype
- **Limitations**: No concurrent writes, limited for production scale
- **Migration Path**: PostgreSQL for production

**Future**: PostgreSQL 15+
- When: Multi-user production deployment
- Why: ACID compliance, concurrent access, better performance

### LLM Provider
**Google Gemini API**
- **Models**: 
  - Gemini 2.5 Pro (most capable, for complex grading and generation)
  - Gemini 2.5 Flash (balanced performance and cost)
  - Gemini 2.5 Flash Lite (fastest, for simple tasks)
- **Why**: Cost-effective, good performance, multimodal capabilities
- **SDK**: `google-genai` Python package
- **API Cost Constraints**: Limited API budget - requires aggressive caching and model selection strategy
- **Use Cases**:
  - **Gemini 2.5 Pro**: Descriptive answer grading, complex question generation
  - **Gemini 2.5 Flash**: Lesson content generation, hint generation
  - **Gemini 2.5 Flash Lite**: Simple explanations, concept simplification, quick responses

## Python Dependencies

### Required Packages

```txt
# Core Framework
streamlit>=1.30.0

# LLM Integration
google-genai>=0.2.0

# Database
sqlite3 (built-in)

# Data Processing
pandas>=2.0.0
numpy>=1.24.0

# ML & Analytics
scikit-learn>=1.3.0
xgboost>=2.0.0
shap>=0.44.0

# Utilities
python-dotenv>=1.0.0  # Environment variables
pydantic>=2.0.0       # Data validation
```

### Optional Packages

```txt
# If using embeddings for semantic matching
sentence-transformers>=2.2.0
faiss-cpu>=1.7.4

# If adding visualization
plotly>=5.17.0
matplotlib>=3.7.0

# Testing
pytest>=7.4.0
pytest-cov>=4.1.0

# Code Quality
black>=23.0.0
flake8>=6.0.0
mypy>=1.5.0
```

## Development Setup

### Local Development Environment

```bash
# 1. Clone repository
git clone <repo-url>
cd MindMentor

# 2. Create virtual environment
python3.10 -m venv venv
source venv/bin/activate  # On Linux/Mac
# venv\Scripts\activate   # On Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env with API keys

# 5. Initialize database
python -m mindmentor.data.init_db

# 6. Run application
streamlit run app.py
```

### Environment Variables

```bash
# .env file structure
GEMINI_API_KEY=your_api_key_here
DATABASE_URL=sqlite:///mindmentor.db
DEBUG_MODE=true
CACHE_ENABLED=true
LOG_LEVEL=INFO
```

## Deployment

### MVP Deployment
**Streamlit Cloud** (Community/Free Tier)
- **Why**: Zero-config deployment, free for public apps
- **Process**: Connect GitHub repo, auto-deploy on push
- **Limitations**: Resource limits, public by default

### Production Deployment Options

1. **AWS EC2**
   - Full control, scalable
   - Use Docker container
   - Configure nginx as reverse proxy

2. **Google Cloud Run**
   - Serverless, auto-scaling
   - Pay per use
   - Good for variable traffic

3. **Heroku**
   - Simple deployment
   - Add-ons for DB, caching
   - Higher cost

## Technical Constraints

### API Rate Limits & Cost Constraints
- **Gemini API**: Limited budget for API calls - this is a PRIMARY constraint
- **Mitigation Strategies**:
  - **Aggressive caching**: Cache all LLM responses with long TTL
  - **Model selection**: Use cheaper models (Flash Lite) for simple tasks
  - **Batch operations**: Combine multiple questions in single API call where possible
  - **Smart routing**: Route to appropriate model based on task complexity
  - **Response reuse**: Reuse similar content across students when appropriate
  - **Fallback mechanisms**: Pre-generated content for common queries
  - **Usage monitoring**: Track and limit API calls per user/session

### Storage Constraints
- **SQLite**: Max DB size ~140 TB (practical limit much lower)
- **Streamlit Cloud**: Limited disk space
- **Mitigation**: Regular data archival, use cloud storage for large files

### Performance Constraints
- **LLM Response Time**: 2-10 seconds per call
- **Streamlit Reruns**: Can be slow with large session state
- **Mitigation**: Loading indicators, async operations, minimal state

### Cost Constraints
- **Gemini API**: Token-based pricing
- **Compute**: Streamlit Cloud free tier limits
- **Storage**: Free tier limits on cloud platforms

## Development Tools

### IDE/Editor
- **VS Code** (recommended)
  - Extensions: Python, Pylance, Black Formatter, GitLens
- **PyCharm** (alternative)

### Version Control
- **Git** + **GitHub**
- Branch strategy: main (production), develop (integration), feature branches

### Code Quality Tools
- **black**: Code formatting
- **flake8**: Linting
- **mypy**: Type checking
- **pytest**: Testing

### Monitoring & Debugging
- **Streamlit's built-in debugging**: st.write(), st.exception()
- **Python logging**: Standard logging module
- **Future**: Sentry for error tracking in production

## Data Flow & Integration

### LLM Integration Pattern

```python
# Simplified flow using google-genai
from google import genai

# Configure
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Select model based on task complexity
model_name = "gemini-2.5-flash"  # or "gemini-2.5-pro", "gemini-2.5-flash-lite"

# Generate with prompt template
prompt = f"""Explain {topic} at {difficulty} level.
Student profile: {student_context}
Format: JSON with 'explanation', 'examples', 'questions'"""

response = client.models.generate_content(
    model=model_name,
    contents=prompt
)
result = json.loads(response.text)

# Model selection strategy
def select_model(task_type):
    if task_type in ['grading_descriptive', 'complex_generation']:
        return 'gemini-2.5-pro'  # Most capable
    elif task_type in ['lesson_content', 'question_gen']:
        return 'gemini-2.5-flash'  # Balanced
    else:
        return 'gemini-2.5-flash-lite'  # Fast & cheap
```
```

### Database Access Pattern

```python
# Using context manager
import sqlite3

def get_student_profile(user_id, topic_id):
    with sqlite3.connect('mindmentor.db') as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM student_profiles WHERE user_id=? AND topic_id=?",
            (user_id, topic_id)
        )
        return cursor.fetchone()
```

### Streamlit State Management

```python
# Initialize session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'current_quiz' not in st.session_state:
    st.session_state.current_quiz = None

# Access state
user_id = st.session_state.user_id
```

## Testing Strategy

### Unit Tests
- Test individual functions in core logic
- Mock LLM responses
- Test data access layer
- Coverage target: 80%+

### Integration Tests
- Test complete user flows
- Use test database
- Mock external APIs

### Manual Testing
- UI/UX testing
- End-to-end user journeys
- Performance testing with realistic data

## Security Considerations

### Current (MVP)
- **Basic Authentication**: Simple username/password authentication for multi-user support
- API keys in environment variables (not committed)
- Basic input validation with Pydantic
- Password hashing (bcrypt or similar)
- Session management via Streamlit session state

### Future (Production)
- User authentication (OAuth 2.0 or JWT)
- API key rotation
- SQL injection prevention (parameterized queries)
- XSS protection
- Rate limiting per user
- HTTPS only
- Data encryption at rest

## Performance Optimization

### Current Strategies (CRITICAL due to API constraints)
1. **Aggressive LLM Response Caching**: 
   - Cache by (topic, difficulty, student_level)
   - Long TTL (7+ days for stable content)
   - Store in SQLite cache table
2. **Smart Model Selection**: Use cheapest appropriate model for each task
3. **Database Indexing**: Index on frequently queried columns
4. **Lazy Loading**: Load data only when needed
5. **Session State Minimization**: Keep only essential data in state
6. **Batch API Calls**: Combine multiple requests when possible
7. **Pre-generated Content**: Store common explanations and examples
8. **Response Reuse**: Share cached responses across similar student profiles

### Future Optimizations
1. **Redis Caching**: For distributed deployments
2. **CDN**: For static assets
3. **Database Connection Pooling**: For PostgreSQL
4. **Async LLM Calls**: Non-blocking API requests
5. **Batch Processing**: Process multiple items in single LLM call

## Tool Usage Patterns

### Common Development Workflows

**Starting Development Session**:
```bash
source venv/bin/activate
streamlit run app.py
```

**Running Tests**:
```bash
pytest tests/ -v --cov=mindmentor
```

**Code Formatting**:
```bash
black mindmentor/
flake8 mindmentor/
```

**Database Migrations** (manual for SQLite):
```bash
sqlite3 mindmentor.db < migrations/001_add_column.sql
```

**Checking LLM Usage**:
```bash
# Log token usage in code
# Monitor via Gemini API dashboard
```

## Documentation Standards

- **Code Comments**: Docstrings for all public functions
- **Type Hints**: Use Python type hints throughout
- **README**: Setup instructions, architecture overview
- **API Documentation**: Document LLM prompt templates
- **Database Schema**: Keep schema.sql updated
