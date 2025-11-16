# MindMentor

AI-driven personal study companion for JEE (Joint Entrance Examination) preparation.

## Overview

MindMentor is an adaptive learning system that acts as a personal tutor, progress analyst, and study planner. It uses LLMs (Google Gemini) to provide personalized teaching, generates adaptive quizzes, tracks learning patterns, and creates customized study schedules.

### Key Features

- **Personalized Teaching**: LLM-powered explanations adapted to your learning style
- **Adaptive Quizzes**: Questions based on your learning progress and weak areas
- **Learning Analytics**: Track mastery levels, identify weak topics, and monitor progress
- **Smart Study Planner**: AI-generated schedules with spaced repetition
- **JEE Focused**: Complete Physics, Chemistry, and Mathematics syllabus coverage

## Tech Stack

- **Frontend**: Streamlit (Python web framework)
- **Backend**: Python 3.10+
- **Database**: SQLite (for MVP)
- **LLM**: Google Gemini 2.5 (Pro, Flash, Flash Lite)
- **ML**: scikit-learn, XGBoost, SHAP

## Project Structure

```
MindMentor/
├── src/
│   ├── pages/          # Streamlit pages (UI)
│   ├── core/           # Business logic
│   ├── llm/            # LLM integration & caching
│   ├── data/           # Database operations
│   └── utils/          # Utility functions
├── tests/              # Test suite
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variables template
└── README.md           # This file
```

## Setup Instructions

### 1. Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Google Gemini API key ([Get one here](https://ai.google.dev/))

### 2. Clone Repository

```bash
git clone <repository-url>
cd MindMentor
```

### 3. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your Gemini API key
nano .env  # or use any text editor
```

Required environment variables:
- `GEMINI_API_KEY`: Your Google Gemini API key

### 6. Initialize Database

```bash
# Create database and apply schema
python src/data/init_db.py

# Seed JEE syllabus data
python src/data/seed_jee_data.py
```

### 7. Run Application

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Formatting

```bash
# Format code
black src/

# Lint code
flake8 src/
```

## Database Schema

The application uses SQLite with the following main tables:

- **users**: User authentication and profiles
- **topics**: JEE syllabus (Physics, Chemistry, Math)
- **llm_cache**: Cached LLM responses (cost optimization)
- **questions**: Quiz questions
- **quizzes**: Quiz sessions
- **attempts**: Individual question attempts
- **student_profiles**: Learning progress per topic
- **schedules**: Study plans
- **chat_history**: Conversational learning history

## API Cost Optimization

The system implements aggressive caching to minimize Gemini API costs:

- All LLM responses are cached with long TTL (7+ days)
- Cache hit rate target: >80%
- Smart model selection (Pro/Flash/Flash Lite based on task)
- Batch operations where possible
- Rule-based grading for objective questions

## Architecture

MindMentor follows a monolithic Streamlit architecture for the MVP:

1. **UI Layer**: Streamlit pages and components
2. **Business Logic**: Teaching, quiz generation, grading, analytics
3. **LLM Layer**: Gemini API integration with caching
4. **Data Layer**: SQLite database operations

See `.kilocode/rules/memory-bank/architecture.md` for detailed architecture documentation.

## Roadmap

### Phase 1: MVP (Current)
- ✅ Database schema and setup
- ⏳ Basic authentication
- ⏳ LLM integration with caching
- ⏳ Teaching/learning module
- ⏳ Quiz generation and grading
- ⏳ Progress tracking

### Phase 2: Enhanced Features
- Advanced analytics with ML
- Personalized study schedules
- Mock test simulator
- Performance insights

### Phase 3: Scale
- Multi-user deployment
- PostgreSQL migration
- REST API
- Mobile app

## Contributing

This is currently a personal project. Contributions, issues, and feature requests are welcome!

## License

[Add your license here]

## Contact

[Add your contact information]

---

**Built with ❤️ for JEE aspirants**
