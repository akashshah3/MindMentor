"""
Simple Quiz Page - Clean implementation
"""

import streamlit as st
from datetime import datetime
import time

from src.data.db import Database
from src.core.auth import SessionManager
from src.core.simple_quiz import SimpleQuizGenerator


def init_quiz_state():
    """Initialize quiz session state"""
    if 'quiz_questions' not in st.session_state:
        st.session_state.quiz_questions = None
    if 'quiz_answers' not in st.session_state:
        st.session_state.quiz_answers = {}
    if 'quiz_result' not in st.session_state:
        st.session_state.quiz_result = None
    if 'quiz_start_time' not in st.session_state:
        st.session_state.quiz_start_time = None
    if 'quiz_topic_ids' not in st.session_state:
        st.session_state.quiz_topic_ids = []


def show_topic_selection(db: Database, user_id: int):
    """Show topic selection screen"""
    st.title("✍️ Practice Quiz")
    st.markdown("Select topics and start your quiz")
    
    st.divider()
    
    # Get all topics grouped by subject
    all_topics = db.get_all_topics()
    topics_by_subject = {}
    for topic in all_topics:
        subject = topic['subject']
        if subject not in topics_by_subject:
            topics_by_subject[subject] = []
        topics_by_subject[subject].append(topic)
    
    # Topic selection
    st.subheader("📚 Select Topics")
    
    selected_topic_ids = []
    
    # Create tabs for each subject
    tabs = st.tabs(list(topics_by_subject.keys()))
    
    for tab, subject in zip(tabs, topics_by_subject.keys()):
        with tab:
            for topic in topics_by_subject[subject]:
                if st.checkbox(
                    topic['topic_name'],
                    key=f"topic_{topic['id']}",
                    help=f"Difficulty: {topic['difficulty_level']}, Weight: {topic['exam_weight']}"
                ):
                    selected_topic_ids.append(topic['id'])
    
    st.divider()
    
    # Quiz configuration
    col1, col2 = st.columns(2)
    
    with col1:
        num_questions = st.slider(
            "Number of Questions",
            min_value=3,
            max_value=10,
            value=5,
            help="How many questions do you want in the quiz?"
        )
    
    with col2:
        difficulty = st.selectbox(
            "Difficulty Level",
            options=["Easy", "Medium", "Hard"],
            index=1
        )
    
    st.divider()
    
    # Generate quiz button
    if len(selected_topic_ids) == 0:
        st.warning("⚠️ Please select at least one topic to generate a quiz")
    else:
        st.success(f"✅ {len(selected_topic_ids)} topic(s) selected")
        
        if st.button("🎯 Generate Quiz", type="primary", use_container_width=True):
            with st.spinner(f"Generating {num_questions} questions..."):
                quiz_gen = SimpleQuizGenerator(db)
                questions = quiz_gen.generate_quiz(
                    user_id=user_id,
                    topic_ids=selected_topic_ids,
                    num_questions=num_questions,
                    difficulty=difficulty
                )
                
                if questions:
                    st.session_state.quiz_questions = questions
                    st.session_state.quiz_answers = {}
                    st.session_state.quiz_result = None
                    st.session_state.quiz_start_time = datetime.now()
                    st.session_state.quiz_topic_ids = selected_topic_ids
                    st.success(f"✅ Generated {len(questions)} questions!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("❌ Failed to generate quiz. Please try again.")


def show_quiz_taking():
    """Show quiz questions"""
    questions = st.session_state.quiz_questions
    
    st.title("✍️ Quiz in Progress")
    
    # Timer display
    if st.session_state.quiz_start_time:
        elapsed = (datetime.now() - st.session_state.quiz_start_time).total_seconds()
        mins = int(elapsed // 60)
        secs = int(elapsed % 60)
        st.info(f"⏱️ Time: {mins:02d}:{secs:02d}")
    
    st.divider()
    
    # Show all questions
    for idx, question in enumerate(questions, 1):
        st.markdown(f"### Question {idx}")
        st.markdown(f"**{question.question_text}**")
        st.caption(f"Topic: {question.topic_name}")
        
        # Answer options
        answer = st.radio(
            "Select your answer:",
            options=['A', 'B', 'C', 'D'],
            format_func=lambda x: {
                'A': f"A. {question.option_a}",
                'B': f"B. {question.option_b}",
                'C': f"C. {question.option_c}",
                'D': f"D. {question.option_d}"
            }[x],
            key=f"q_{question.id}",
            index=None,
            horizontal=False
        )
        
        # Store answer
        if answer:
            st.session_state.quiz_answers[question.id] = answer
        
        st.divider()
    
    # Submit button
    answered = len(st.session_state.quiz_answers)
    total = len(questions)
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.write(f"**Progress:** {answered}/{total} questions answered")
    
    with col2:
        if st.button("Cancel", use_container_width=True):
            st.session_state.quiz_questions = None
            st.session_state.quiz_answers = {}
            st.rerun()
    
    with col3:
        if answered < total:
            st.warning(f"{total - answered} unanswered")
        
        if st.button("Submit Quiz", type="primary", use_container_width=True, disabled=answered == 0):
            # Grade the quiz
            db = Database()
            user_id = SessionManager.get_user_id(st.session_state)
            quiz_gen = SimpleQuizGenerator(db)
            
            # Calculate time taken
            time_taken = int((datetime.now() - st.session_state.quiz_start_time).total_seconds() / 60)
            if time_taken < 1:
                time_taken = 1
            
            # Grade
            result = quiz_gen.grade_quiz(questions, st.session_state.quiz_answers)
            
            # Save to database
            quiz_gen.save_quiz_attempt(
                user_id=user_id,
                topic_ids=st.session_state.quiz_topic_ids,
                result=result,
                time_taken_minutes=time_taken
            )
            
            # Store result
            st.session_state.quiz_result = result
            st.success("✅ Quiz submitted and graded!")
            time.sleep(0.5)
            st.rerun()


def show_quiz_results():
    """Show quiz results"""
    result = st.session_state.quiz_result
    
    st.title("📊 Quiz Results")
    
    # Overall score
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Score",
            f"{result.correct_answers}/{result.total_questions}",
            delta=f"{result.score_percentage}%"
        )
    
    with col2:
        st.metric(
            "Correct",
            result.correct_answers,
            delta=f"{result.score_percentage:.1f}%"
        )
    
    with col3:
        performance = (
            "Excellent! 🎉" if result.score_percentage >= 80 else
            "Good Job! 👍" if result.score_percentage >= 60 else
            "Keep Practicing! 💪"
        )
        st.metric("Performance", performance)
    
    st.divider()
    
    # Question-by-question results
    st.subheader("📝 Detailed Results")
    
    for idx, qr in enumerate(result.question_results, 1):
        is_correct = qr['is_correct']
        
        # Question header with status
        status_icon = "✅" if is_correct else "❌"
        st.markdown(f"### {status_icon} Question {idx}")
        st.markdown(f"**{qr['question_text']}**")
        
        # Show options
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**A.** {qr['option_a']}")
            st.markdown(f"**B.** {qr['option_b']}")
        with col2:
            st.markdown(f"**C.** {qr['option_c']}")
            st.markdown(f"**D.** {qr['option_d']}")
        
        # Show answer and explanation
        user_answer = qr['user_answer'] or "Not answered"
        correct_answer = qr['correct_answer']
        
        if is_correct:
            st.success(f"✅ Your answer: **{user_answer}** - Correct!")
        else:
            st.error(f"❌ Your answer: **{user_answer}**")
            st.info(f"✓ Correct answer: **{correct_answer}**")
        
        # Explanation
        with st.expander("📖 Explanation"):
            st.write(qr['explanation'])
        
        st.divider()
    
    # Action buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Take Another Quiz", use_container_width=True):
            st.session_state.quiz_questions = None
            st.session_state.quiz_answers = {}
            st.session_state.quiz_result = None
            st.session_state.quiz_start_time = None
            st.rerun()
    
    with col2:
        if st.button("📊 View Dashboard", use_container_width=True):
            st.session_state.current_page = 'dashboard'
            st.session_state.quiz_questions = None
            st.session_state.quiz_answers = {}
            st.session_state.quiz_result = None
            st.session_state.quiz_start_time = None
            st.rerun()


def main():
    """Main quiz page function"""
    # Check authentication
    if not SessionManager.is_authenticated(st.session_state):
        st.error("Please log in to access quizzes")
        st.stop()
    
    # Initialize state
    init_quiz_state()
    
    db = Database()
    user_id = SessionManager.get_user_id(st.session_state)
    
    # Route to appropriate screen
    if st.session_state.quiz_result is not None:
        show_quiz_results()
    elif st.session_state.quiz_questions is not None:
        show_quiz_taking()
    else:
        show_topic_selection(db, user_id)


if __name__ == "__main__":
    main()
