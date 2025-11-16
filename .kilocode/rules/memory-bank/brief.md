# **MindMentor**

MindMentor is an **AI-driven personal study companion** designed specifically for **competitive exam preparation**. It behaves like a **personal tutor + progress analyst + study planner**, all in one system. The goal is **not just to teach**, but to **learn how the student learns**, and then adapt its teaching style, pace, and content accordingly.

It becomes _better for the student over time_ by understanding:

-   How they study
    
-   Where they struggle
    
-   How quickly they grasp concepts
    
-   How consistent their learning patterns are
    

Ultimately, it becomes a **custom AI mentor for each student**, guiding them end-to-end.

----------

# 🔍 **Core Ideas You Want to Build**

## 1. **Personalized Teaching Through LLMs**

MindMentor teaches concepts like a human tutor:

-   Explains topics simply
    
-   Breaks down definitions
    
-   Uses examples, analogies, diagrams
    
-   Provides interactive Q&A
    
-   Adjusts explanations based on past conversations
  

## 2. **Learning Pattern Analyzer (Adaptive Engine)**

MindMentor _tracks and learns student behaviour_, such as:

-   Attention span
    
-   Time taken to answer questions
    
-   Topics where they frequently make mistakes
    
-   Chat history to detect conceptual gaps
    

This creates a **learning profile** for the student.  
Using this, the system decides:

-   What to teach next
    
-   When to revise
    
-   When to push advanced topics
    
-   When to slow down or simplify
    
## 3. **Quizzes & Tests Based on Learning Progress**

MindMentor doesn’t just generate random quizzes.  
It generates assessments _based on what the student has actually learned_:

-   Short quizzes after topics
    
-   Full tests after chapters
    
-   Timed tests to simulate exam conditions
    
-   Analysis of answer quality (especially for descriptive questions)
    

It uses quiz patterns to update the student’s learning model:

-   Questions you fail → push into revision
    
-   Questions you succeed → mark as mastered
    

## 4. **Personalized Study Schedule Generator**

This is a major part of the project.

MindMentor asks basic inputs:

-   Which exam?
    
-   Time available daily?
    
-   Total remaining months?
    
-   Familiarity with topics?
    

Then it produces:

-   Daily study plans
    
-   Weekly and monthly targets
    
-   Priority order of topics based on performance
    
-   Adjustments depending on how you’re improving
    

## 5. **Smart Assessment Engine**

MindMentor evaluates results like an expert teacher:

-   Shows accuracy trends
    
-   Identifies weak areas
    
-   Detects specific concepts causing mistakes
    
-   Suggests revision cycles
    
-   Gives explainability (like SHAP-style insights)
    
    -   _“You lost marks in Mechanics because you didn’t understand Work-Energy fundamentals.”_
        

## 6. **Dashboard for Progress Tracking**

A complete performance dashboard showing:

-   Topic mastery levels
    
-   Accuracy improvements
    
-   Average answer time
    
-   Learning curve
    
-   Strong vs weak areas
    
-   Revision suggestions
    

# 📌 **Overall Understanding**

MindMentor is essentially an **AI-powered adaptive learning ecosystem** that:

-   Teaches → Tracks → Tests → Analyzes → Adjusts → Plans → Repeats
    
-   Completely aligns to the student’s habits and improvement needs.
    

It's not just a chatbot or quiz generator — it's a **complete personalized tutor powered by AI + analytics.**
This can genuinely transform exam preparation into something **smarter and more efficient**, not just harder.


# 🚀 High-level architecture (Streamlit-first, light backend)

1.  **Streamlit app (single codebase)**
    
    -   UI for lessons, chat/tutor view, quizzes, schedule input, dashboard.
        
    -   Handles session state, small local caching, and orchestrates calls to LLM / scoring functions.
        
2.  **LLM layer (external API)**
    
    -   Gemini-based LLM via API. Prompt templates live in the app.
        
    -   Responsible for: teaching content generation, question generation, answer scoring (for descriptive), hint generation, and short explanations.
        
3.  **Lightweight persistence**
    
    -   **SQLite** (single-file) or **TinyDB / JSON** for MVP. Stores user profiles, progress, quiz history, and schedule.
        
    -   Use simple schema (below).
        
4.  **Small compute layer (local or serverless functions)**
    
    -   For heavier processing (embedding similarity, periodic schedule recalculation, model explainability) you can use lightweight serverless endpoints or run locally inside the Streamlit process if scale is small.
        
5.  **Optional: Vector DB for semantic grading / search**
    
    -   Use Faiss or simple in-file embeddings if you want semantic answer-matching. For MVP, keep this optional — use LLM scoring + heuristic checks.
        

----------

# 🧩 Core Components — Technical Details

## 1. Teaching & Interactive Q&A (LLM-driven)

-   **Prompt strategy:** few-shot templates per topic (context, learning-level tag, desired output format).
    
-   **Modes:** explain, simplify, example, diagram description (textual / ASCII / embed SVG), walk-through problems.
    
-   **Adaptive tuning:** include `student_profile` info (past mistakes, preferred pace, recent topics) in the prompt to adapt explanations.
    

**Implementation notes**

-   Cache generated lesson content keyed by (topic, difficulty, student-level) to reduce API calls.
    
-   Keep prompts short, provide explicit instructions for format (JSON with `explain`, `examples`, `quiz_questions`).
    

## 2. Quiz & Test Generation

-   **Question types:** MCQ (with distractors), short answer, long-form essay, numerical.
    
-   **Generation flow:** LLM produces question + answer + difficulty + tags. Post-filter generated distractors using heuristics (plausibility, not identical to answer).
    
-   **Adaptive selection:** pick questions from recent lessons + weak topics. Use weighted sampling based on mastery score.
    

## 3. Assessment & Auto-Grading

-   **Objective (MCQ/numeric):** straightforward scoring.
    
-   **Descriptive answers:** two-step:
    
    1.  **LLM rubric scoring** — instruct LLM with rubric and expected keypoints. Output score + missed keypoints.
        
    2.  (Optional) **Embedding similarity**: compare student answer embedding with model answer embedding; combine with LLM score for robustness.
        
-   **Answer timing**: capture timestamps to estimate attention / focus metrics.
    

## 4. Learning Pattern Analyzer (student model)

-   **Features tracked per student-topic:**
    
    -   Accuracy (last N attempts)
        
    -   Avg answer time
        
    -   Time-of-day study pattern
        
    -   Revision count
        
    -   Spaced retention score (recall after intervals)
        
-   **Derived signals:**
    
    -   Weakness score = function(accuracy, recency, incorrect patterns)
        
    -   Attention estimate = function(answer times, session length, inactivity)
        
-   **Model:** start with rule-based heuristics and simple ML (logistic regression or XGBoost) to predict "forget probability" or "need revision". Use SHAP on the ML model for explainability.
    

## 5. Personalized Study Schedule Generator

-   **Inputs:** target exam (syllabus), days available / hours per day, familiarity per topic.
    
-   **Algorithm:** greedy + spaced repetition:
    
    -   Prioritize high-weighted topics (exam weight * weakness score).
        
    -   Use SM-2 style scheduling for items requiring repetition.
        
    -   Fill daily slots respecting user time budget and mixing review + new learning.
        
-   **Dynamic adjustments:** at session end, update mastery and re-run scheduling logic (incremental recalculation).
    

## 6. Dashboard & Explainability (SHAP-style)

-   **Metrics to show:**
    
    -   Topic mastery heatmap
        
    -   Weekly accuracy trend
        
    -   Average answer time
        
    -   Weak topics list + top-k concepts missed
        
-   **Explainability:** train a simple model that predicts whether the student will fail the next quiz (features: recent accuracy, time spent, last revision gap). Use SHAP to produce human-readable reasons like:
    
    -   “You lost marks mostly because you skipped practice problems on Concept X and hadn’t revised in 14 days.”
        

----------

# 🗂 Data Schema (minimal MVP)

-   **users**: id, name, exam_target, daily_hours, created_at
    
-   **topics**: id, name, exam_weight, prerequisites
    
-   **lessons**: id, topic_id, content_ref (cached key), difficulty
    
-   **attempts**: id, user_id, topic_id, question_id, correctness, score, time_taken, timestamp
    
-   **quizzes**: id, user_id, topics[], score, timestamp
    
-   **schedules**: user_id, date, planned_items[] (topic_id, activity_type)
    

(Implement as simple SQL tables or JSON documents.)

----------

# ⚙️ Tech Stack Recommendations (MVP)

-   **Frontend / primary app:** Streamlit (Python).
    
-   **LLM API:** Gemini (or other available LLM), accessed from Streamlit.
    
-   **Database:** SQLite for MVP; migrate to Postgres later if needed.
    
-   **Embeddings / Vector search:** OpenAI/Gemini embeddings or local sentence-transformers + Faiss (optional).
    
-   **ML & explainability:** scikit-learn, XGBoost, SHAP.
    
-   **Deployment:** Streamlit Cloud