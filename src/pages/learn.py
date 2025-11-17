"""
Learning page - Interactive AI tutoring interface

This page allows students to:
1. Browse and select topics from JEE syllabus
2. Start learning sessions with AI tutor
3. Engage in interactive chat for concept clarification
4. Track learning progress
"""

import streamlit as st
from datetime import datetime
from typing import Optional, Dict, List
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.data.db import Database
from src.core.auth import SessionManager


def init_learn_state():
    """Initialize learning session state variables"""
    if 'selected_topic_id' not in st.session_state:
        st.session_state.selected_topic_id = None
    if 'learning_mode' not in st.session_state:
        st.session_state.learning_mode = 'browse'  # 'browse' or 'chat'
    if 'current_lesson' not in st.session_state:
        st.session_state.current_lesson = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'lesson_start_time' not in st.session_state:
        st.session_state.lesson_start_time = None


def get_topics_by_subject(db: Database) -> Dict[str, List[Dict]]:
    """
    Organize topics by subject and chapter
    
    Returns:
        Dict with structure: {subject: {chapter: [topics]}}
    """
    topics = db.get_all_topics()
    
    organized = {}
    for topic in topics:
        subject = topic['subject']
        chapter = topic['chapter_name']  # Column is 'chapter_name' not 'chapter'
        
        if subject not in organized:
            organized[subject] = {}
        if chapter not in organized[subject]:
            organized[subject][chapter] = []
        
        organized[subject][chapter].append(topic)
    
    return organized


def render_topic_selection(db: Database, user_id: int):
    """Render topic browsing and selection interface"""
    st.title("📚 Learn with AI Tutor")
    st.markdown("Select a topic to start your personalized learning session")
    
    # Get topics organized by subject
    topics_by_subject = get_topics_by_subject(db)
    
    # Create tabs for each subject
    subjects = list(topics_by_subject.keys())
    tabs = st.tabs(subjects)
    
    for idx, subject in enumerate(subjects):
        with tabs[idx]:
            chapters = topics_by_subject[subject]
            
            # Display each chapter
            for chapter_name, topics in sorted(chapters.items()):
                with st.expander(f"📖 {chapter_name}", expanded=False):
                    # Display topics in this chapter
                    for topic in topics:
                        col1, col2, col3 = st.columns([3, 1, 1])
                        
                        with col1:
                            st.markdown(f"**{topic['topic_name']}**")
                            # Check if description exists (it's not in the database schema)
                            if 'description' in topic and topic['description']:
                                st.caption(topic['description'])
                        
                        with col2:
                            # Show difficulty badge
                            difficulty = topic.get('difficulty_level', 'Medium')
                            if difficulty == 'Easy':
                                st.success(f"🟢 {difficulty}")
                            elif difficulty == 'Hard':
                                st.error(f"🔴 {difficulty}")
                            else:
                                st.info(f"🟡 {difficulty}")
                        
                        with col3:
                            # Start Learning button
                            if st.button("Start Learning", key=f"learn_{topic['id']}"):
                                start_learning_session(topic['id'])
                    
                    st.divider()


def start_learning_session(topic_id: int):
    """Start a new learning session for the selected topic"""
    st.session_state.selected_topic_id = topic_id
    st.session_state.learning_mode = 'chat'
    st.session_state.chat_history = []
    st.session_state.current_lesson = None
    st.session_state.lesson_start_time = datetime.now()
    st.rerun()


def render_chat_interface(db: Database, user_id: int, topic_id: int):
    """Render interactive chat interface with AI tutor"""
    # Get topic details
    topic = db.get_topic_by_id(topic_id)
    if not topic:
        st.error("Topic not found!")
        return
    
    # Header with back button
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("⬅️ Back"):
            end_learning_session(db, user_id, topic_id)
    with col2:
        st.title(f"📚 {topic['topic_name']}")
        st.caption(f"{topic['subject']} • {topic['chapter_name']}")
    
    st.divider()
    
    # Generate initial lesson if not already done
    if st.session_state.current_lesson is None:
        with st.spinner("🤖 Your AI tutor is preparing the lesson..."):
            generate_initial_lesson(topic)
    
    # Display lesson
    if st.session_state.current_lesson:
        display_lesson(st.session_state.current_lesson)
    
    st.divider()
    
    # Chat section
    st.subheader("💬 Ask Questions")
    st.markdown("Ask your AI tutor anything about this topic!")
    
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    user_question = st.chat_input("Type your question here...")
    if user_question:
        handle_user_question(db, user_id, topic, user_question)
    
    # Completion button
    st.divider()
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.button("✅ Mark as Complete", type="primary", use_container_width=True):
            complete_topic(db, user_id, topic_id)


def generate_initial_lesson(topic: Dict):
    """Generate initial lesson content using LLM"""
    from src.llm.client import generate_lesson
    
    try:
        # Generate lesson
        lesson_data, was_cached = generate_lesson(
            subject=topic['subject'],
            topic_name=topic['topic_name'],
            chapter_name=topic['chapter_name'],
            difficulty=topic.get('difficulty_level', 'Medium'),
            student_level='intermediate'  # TODO: Get from student profile
        )
        
        # Store in session state
        st.session_state.current_lesson = lesson_data
        
        # Show cache status
        if was_cached:
            st.success("✅ Lesson loaded from cache (instant!)")
        else:
            st.info("🆕 Fresh lesson generated for you")
        
    except Exception as e:
        st.error(f"Failed to generate lesson: {str(e)}")
        st.session_state.current_lesson = {
            'explanation': f"Error loading lesson content. Please try again.",
            'key_points': [],
            'examples': []
        }


def display_lesson(lesson_data: Dict):
    """Display formatted lesson content"""
    st.subheader("📖 Lesson")
    
    # Main explanation
    if 'explanation' in lesson_data:
        st.markdown(lesson_data['explanation'])
    
    # Key points
    if 'key_points' in lesson_data and lesson_data['key_points']:
        st.markdown("### 🎯 Key Points")
        for point in lesson_data['key_points']:
            st.markdown(f"- {point}")
    
    # Formulas
    if 'formulas' in lesson_data and lesson_data['formulas']:
        st.markdown("### 📐 Important Formulas")
        for formula in lesson_data['formulas']:
            st.latex(formula)
    
    # Examples
    if 'examples' in lesson_data and lesson_data['examples']:
        st.markdown("### 💡 Examples")
        for idx, example in enumerate(lesson_data['examples'], 1):
            with st.expander(f"Example {idx}", expanded=False):
                # Check if example is a dictionary (structured) or string
                if isinstance(example, dict):
                    if 'problem' in example:
                        st.markdown("**Problem:**")
                        st.markdown(example['problem'])
                    if 'solution' in example:
                        st.markdown("**Solution:**")
                        st.markdown(example['solution'])
                else:
                    st.markdown(example)
    
    # Common mistakes
    if 'common_mistakes' in lesson_data and lesson_data['common_mistakes']:
        st.markdown("### ⚠️ Common Mistakes to Avoid")
        for mistake in lesson_data['common_mistakes']:
            st.warning(mistake)
    
    # JEE tips
    if 'jee_tips' in lesson_data and lesson_data['jee_tips']:
        st.markdown("### 🎓 JEE Tips")
        for tip in lesson_data['jee_tips']:
            st.info(tip)


def handle_user_question(db: Database, user_id: int, topic: Dict, question: str):
    """Handle user question and get AI response"""
    from src.llm.client import gemini_client
    from src.llm.models import TaskType
    from src.llm.prompts import PromptTemplates
    
    # Add user message to chat
    st.session_state.chat_history.append({
        "role": "user",
        "content": question
    })
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(question)
    
    # Generate AI response
    with st.chat_message("assistant"):
        with st.spinner("🤔 Thinking..."):
            try:
                # Get conversation context (last 5 messages)
                context_messages = st.session_state.chat_history[-5:]
                conversation_history = "\n".join([
                    f"{'Student' if msg['role'] == 'user' else 'Tutor'}: {msg['content']}"
                    for msg in context_messages
                ])
                
                # If no history, use a placeholder
                if not conversation_history:
                    conversation_history = "This is the start of the conversation."
                
                # Generate response WITHOUT caching (chat is conversational/context-dependent)
                response = gemini_client._call_api(
                    model='gemini-2.5-flash',  # Use Flash for chat
                    prompt=PromptTemplates.CHAT_QA.format(
                        topic_name=topic['topic_name'],
                        subject=topic['subject'],
                        student_question=question,
                        conversation_history=conversation_history
                    ),
                    temperature=0.7
                )
                
                # Display response
                st.markdown(response)
                
                # Add to chat history
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response
                })
                
                # Save to database
                save_chat_message(db, user_id, topic['id'], question, response)
                
            except Exception as e:
                error_msg = f"Sorry, I encountered an error: {str(e)}"
                st.error(error_msg)
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": error_msg
                })


def save_chat_message(db: Database, user_id: int, topic_id: int, 
                     question: str, response: str):
    """Save chat interaction to database"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Save user message
            cursor.execute("""
                INSERT INTO chat_history 
                (user_id, topic_id, role, message, timestamp)
                VALUES (?, ?, 'user', ?, ?)
            """, (user_id, topic_id, question, datetime.now()))
            
            # Save assistant response
            cursor.execute("""
                INSERT INTO chat_history 
                (user_id, topic_id, role, message, timestamp)
                VALUES (?, ?, 'assistant', ?, ?)
            """, (user_id, topic_id, response, datetime.now()))
            
            conn.commit()
        
    except Exception as e:
        print(f"Error saving chat message: {e}")


def complete_topic(db: Database, user_id: int, topic_id: int):
    """Mark topic as completed and update progress"""
    try:
        # First, complete the database transaction
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get or create student profile for this topic
            cursor.execute("""
                SELECT id, mastery_score, strength_level
                FROM student_profiles
                WHERE user_id = ? AND topic_id = ?
            """, (user_id, topic_id))
            
            profile = cursor.fetchone()
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            if profile:
                # Update existing profile - mark as completed
                cursor.execute("""
                    UPDATE student_profiles
                    SET strength_level = 'STRONG',
                        mastery_score = CASE 
                            WHEN mastery_score < 0.7 THEN 0.7 
                            ELSE mastery_score 
                        END,
                        last_attempt_date = ?,
                        updated_at = ?
                    WHERE user_id = ? AND topic_id = ?
                """, (current_time, current_time, user_id, topic_id))
            else:
                # Create new profile - mark as completed
                cursor.execute("""
                    INSERT INTO student_profiles
                    (user_id, topic_id, mastery_score, strength_level, 
                     last_attempt_date, updated_at)
                    VALUES (?, ?, 0.7, 'STRONG', ?, ?)
                """, (user_id, topic_id, current_time, current_time))
            
            # IMPORTANT: Commit BEFORE leaving the context manager
            conn.commit()
        # Context manager closes connection here, AFTER commit
        
        st.success("🎉 Topic marked as complete! Great progress!")
        
        # THEN reset state and navigate - database is already committed
        st.session_state.learning_mode = 'browse'
        st.session_state.selected_topic_id = None
        st.session_state.current_lesson = None
        st.session_state.chat_history = []
        st.session_state.lesson_start_time = None
        st.rerun()
        
    except Exception as e:
        st.error(f"Error updating progress: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


def calculate_session_duration() -> int:
    """Calculate session duration in minutes"""
    if st.session_state.lesson_start_time:
        duration = datetime.now() - st.session_state.lesson_start_time
        return int(duration.total_seconds() / 60)
    return 0


def end_learning_session(db: Database, user_id: int, topic_id: int):
    """End learning session and return to browse mode"""
    # Save session as in-progress if not completed
    if st.session_state.lesson_start_time:
        try:
            # Complete database transaction FIRST
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if profile exists
                cursor.execute("""
                    SELECT id, strength_level
                    FROM student_profiles
                    WHERE user_id = ? AND topic_id = ?
                """, (user_id, topic_id))
                
                profile = cursor.fetchone()
                
                if not profile:
                    # Create in-progress profile if it doesn't exist
                    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    cursor.execute("""
                        INSERT INTO student_profiles
                        (user_id, topic_id, mastery_score, strength_level, 
                         last_attempt_date, updated_at)
                        VALUES (?, ?, 0.3, 'AVERAGE', ?, ?)
                    """, (user_id, topic_id, current_time, current_time))
                    # Commit before leaving context manager
                    conn.commit()
                # Context manager closes connection here, AFTER commit
                
        except Exception as e:
            print(f"Error saving progress: {e}")
            import traceback
            print(f"Full error: {traceback.format_exc()}")
    
    # THEN reset state and navigate - database is already committed
    st.session_state.learning_mode = 'browse'
    st.session_state.selected_topic_id = None
    st.session_state.current_lesson = None
    st.session_state.chat_history = []
    st.session_state.lesson_start_time = None
    st.rerun()


def main():
    """Main learning page"""
    # Check authentication
    if not SessionManager.is_authenticated(st.session_state):
        st.warning("Please login to access the learning module")
        st.stop()
    
    user_id = st.session_state.user_id
    
    # Initialize state
    init_learn_state()
    
    # Get database connection
    db = Database()
    
    # Render appropriate interface
    if st.session_state.learning_mode == 'chat' and st.session_state.selected_topic_id:
        render_chat_interface(db, user_id, st.session_state.selected_topic_id)
    else:
        render_topic_selection(db, user_id)


if __name__ == "__main__":
    main()
