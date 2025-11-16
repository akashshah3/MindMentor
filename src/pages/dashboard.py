"""
Main Dashboard Page
"""

import streamlit as st
from src.core.auth import SessionManager
from src.data.db import db


def show_dashboard():
    """Display main dashboard for authenticated users"""
    
    # Ensure user is authenticated
    if not SessionManager.is_authenticated(st.session_state):
        st.error("Please log in to access the dashboard")
        st.stop()
    
    # Get user info
    user_id = SessionManager.get_user_id(st.session_state)
    user = db.get_user_by_id(user_id)
    
    if not user:
        st.error("User not found")
        st.stop()
    
    # Header
    st.title(f"Welcome, {user['name']}! 👋")
    
    # Display user info
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Target Exam", user.get('exam_target', 'Not Set'))
    
    with col2:
        st.metric("Daily Study Hours", f"{user.get('daily_hours', 0):.1f} hrs")
    
    with col3:
        # Get topic count
        topics = db.get_all_topics()
        st.metric("Total JEE Topics", len(topics))
    
    st.markdown("---")
    
    # Quick stats section
    st.subheader("📊 Your Progress Overview")
    
    # Get user's learning profiles
    profiles = db.get_all_student_profiles(user_id)
    
    if profiles:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Topics Started", len(profiles))
        
        with col2:
            avg_mastery = sum(p['mastery_score'] for p in profiles) / len(profiles)
            st.metric("Average Mastery", f"{avg_mastery*100:.1f}%")
        
        with col3:
            total_attempts = sum(p['total_attempts'] for p in profiles)
            st.metric("Total Practice", f"{total_attempts} questions")
        
        # Show top weak and strong topics
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔴 Needs Attention")
            weak_topics = sorted(profiles, key=lambda x: x['mastery_score'])[:5]
            
            if weak_topics:
                for topic in weak_topics:
                    st.write(f"• {topic['topic_name']} ({topic['subject']})")
                    st.progress(topic['mastery_score'])
            else:
                st.info("No topics started yet")
        
        with col2:
            st.subheader("🟢 Strong Topics")
            strong_topics = sorted(profiles, key=lambda x: x['mastery_score'], reverse=True)[:5]
            
            if strong_topics:
                for topic in strong_topics:
                    st.write(f"• {topic['topic_name']} ({topic['subject']})")
                    st.progress(topic['mastery_score'])
            else:
                st.info("Keep learning to build strengths!")
    
    else:
        st.info("👋 You haven't started learning any topics yet!")
        st.write("Get started by selecting a topic to learn or taking a quiz.")
    
    # Topics overview
    st.markdown("---")
    st.subheader("📚 JEE Syllabus Overview")
    
    tab_physics, tab_chemistry, tab_math = st.tabs(["⚛️ Physics", "🧪 Chemistry", "📐 Mathematics"])
    
    with tab_physics:
        physics_topics = db.get_all_topics("Physics")
        st.write(f"**Total Topics: {len(physics_topics)}**")
        
        # Group by chapter
        chapters = {}
        for topic in physics_topics:
            chapter = topic['chapter_name']
            if chapter not in chapters:
                chapters[chapter] = []
            chapters[chapter].append(topic['topic_name'])
        
        for chapter, topics_list in chapters.items():
            with st.expander(f"📖 {chapter} ({len(topics_list)} topics)"):
                for topic in topics_list:
                    st.write(f"• {topic}")
    
    with tab_chemistry:
        chemistry_topics = db.get_all_topics("Chemistry")
        st.write(f"**Total Topics: {len(chemistry_topics)}**")
        
        # Group by chapter
        chapters = {}
        for topic in chemistry_topics:
            chapter = topic['chapter_name']
            if chapter not in chapters:
                chapters[chapter] = []
            chapters[chapter].append(topic['topic_name'])
        
        for chapter, topics_list in chapters.items():
            with st.expander(f"📖 {chapter} ({len(topics_list)} topics)"):
                for topic in topics_list:
                    st.write(f"• {topic}")
    
    with tab_math:
        math_topics = db.get_all_topics("Mathematics")
        st.write(f"**Total Topics: {len(math_topics)}**")
        
        # Group by chapter
        chapters = {}
        for topic in math_topics:
            chapter = topic['chapter_name']
            if chapter not in chapters:
                chapters[chapter] = []
            chapters[chapter].append(topic['topic_name'])
        
        for chapter, topics_list in chapters.items():
            with st.expander(f"📖 {chapter} ({len(topics_list)} topics)"):
                for topic in topics_list:
                    st.write(f"• {topic}")
    
    # Coming soon features
    st.markdown("---")
    st.subheader("🚀 Coming Soon")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("**📖 Interactive Learning**\nAI-powered lessons and explanations")
    
    with col2:
        st.info("**✍️ Adaptive Quizzes**\nPersonalized practice questions")
    
    with col3:
        st.info("**📅 Study Planner**\nAI-generated study schedules")


if __name__ == "__main__":
    show_dashboard()
