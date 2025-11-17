"""
Enhanced Analytics Dashboard
"""

import streamlit as st
from src.core.auth import SessionManager
from src.data.db import Database
from src.core.analytics import AnalyticsEngine


def show_dashboard():
    """Display enhanced analytics dashboard"""
    
    # Ensure authenticated
    if not SessionManager.is_authenticated(st.session_state):
        st.error("Please log in to access the dashboard")
        st.stop()
    
    user_id = SessionManager.get_user_id(st.session_state)
    db = Database()
    user = db.get_user_by_id(user_id)
    
    if not user:
        st.error("User not found")
        st.stop()
    
    # Initialize analytics
    analytics = AnalyticsEngine(db)
    
    # ===== HEADER =====
    st.title(f"Welcome back, {user['name']}! 👋")
    st.caption(f"Last login: {user.get('last_login', 'First time')}")
    
    st.markdown("---")
    
    # ===== OVERVIEW METRICS =====
    st.subheader("📊 Learning Overview")
    
    overview = analytics.get_learning_overview(user_id)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Topics Started",
            overview['topics_started'],
            delta=f"{overview['topics_mastered']} mastered" if overview['topics_mastered'] > 0 else None
        )
    
    with col2:
        st.metric(
            "Average Mastery",
            f"{overview['average_mastery']*100:.0f}%",
            delta=f"{overview['strong_topics_count']} strong" if overview['strong_topics_count'] > 0 else None
        )
    
    with col3:
        st.metric(
            "Practice Questions",
            overview['total_attempts'],
            delta=f"{overview['total_correct']} correct" if overview['total_correct'] > 0 else None
        )
    
    with col4:
        if overview['total_attempts'] > 0:
            st.metric("Overall Accuracy", f"{overview['overall_accuracy']:.0f}%")
        else:
            st.metric("Overall Accuracy", "N/A")
    
    # ===== STUDY STREAK =====
    if overview['topics_started'] > 0:
        st.markdown("---")
        st.subheader("🔥 Study Streak")
        
        streak = analytics.get_study_streak(user_id)
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            st.metric("Current Streak", f"{streak['current_streak']} days")
        
        with col2:
            st.metric("Best Streak", f"{streak['longest_streak']} days")
        
        with col3:
            if streak['current_streak'] >= 7:
                st.success("🎉 Incredible! You're on fire! Keep it up!")
            elif streak['current_streak'] > 0:
                st.success(f"💪 Great job! Keep the momentum going!")
            elif streak['last_study_date']:
                st.warning(f"Your streak ended. Last study: {streak['last_study_date']}")
            else:
                st.info("Start your learning streak today!")
    
    st.markdown("---")
    
    # ===== SUBJECT BREAKDOWN =====
    if overview['topics_started'] > 0:
        st.subheader("📚 Subject-wise Performance")
        
        subject_stats = analytics.get_subject_breakdown(user_id)
        
        if subject_stats:
            col1, col2, col3 = st.columns(3)
            
            subjects_list = [('Physics', '⚛️'), ('Chemistry', '🧪'), ('Mathematics', '📐')]
            cols = [col1, col2, col3]
            
            for idx, (subject, icon) in enumerate(subjects_list):
                if subject in subject_stats:
                    data = subject_stats[subject]
                    with cols[idx]:
                        st.markdown(f"### {icon} {subject}")
                        st.metric("Topics", data['topics_started'])
                        st.metric("Avg Mastery", f"{data['average_mastery']*100:.0f}%")
                        if data['total_attempts'] > 0:
                            st.metric("Accuracy", f"{data['accuracy']:.0f}%")
                        st.progress(data['average_mastery'])
        
        st.markdown("---")
    
    # ===== MASTERY DISTRIBUTION =====
    if overview['topics_started'] > 0:
        st.subheader("📈 Mastery Distribution")
        
        distribution = analytics.get_mastery_distribution(user_id)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Create a visual representation
            for level, count in distribution.items():
                if count > 0:
                    percentage = count / overview['topics_started'] * 100
                    st.write(f"**{level}**: {count} topics ({percentage:.0f}%)")
                    st.progress(percentage / 100)
        
        with col2:
            st.metric("Total Topics", overview['topics_started'])
            st.metric("Mastered", overview['topics_mastered'])
            st.metric("Need Work", overview['weak_topics_count'])
        
        st.markdown("---")
    
    # ===== WEAK & STRONG TOPICS =====
    if overview['topics_started'] > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔴 Topics Needing Attention")
            weak_topics = analytics.get_weak_topics(user_id, limit=5)
            
            if weak_topics:
                for topic in weak_topics:
                    with st.expander(f"{topic['topic_name']} - {topic['subject']}"):
                        st.progress(topic['mastery_score'])
                        st.caption(f"Mastery: {topic['mastery_score']*100:.0f}%")
                        st.caption(f"Attempts: {topic['total_attempts']}")
                        if topic['total_attempts'] > 0:
                            accuracy = topic['correct_attempts'] / topic['total_attempts'] * 100
                            st.caption(f"Accuracy: {accuracy:.0f}%")
            else:
                st.success("No weak topics! Great job! 🎉")
        
        with col2:
            st.subheader("🟢 Strong Topics")
            strong_topics = analytics.get_strong_topics(user_id, limit=5)
            
            if strong_topics:
                for topic in strong_topics:
                    with st.expander(f"{topic['topic_name']} - {topic['subject']}"):
                        st.progress(topic['mastery_score'])
                        st.caption(f"Mastery: {topic['mastery_score']*100:.0f}%")
                        st.caption(f"Attempts: {topic['total_attempts']}")
                        if topic['total_attempts'] > 0:
                            accuracy = topic['correct_attempts'] / topic['total_attempts'] * 100
                            st.caption(f"Accuracy: {accuracy:.0f}%")
            else:
                st.info("Keep learning to build your strengths!")
        
        st.markdown("---")
    
    # ===== RECOMMENDATIONS =====
    st.subheader("💡 What to Study Next")
    
    recommendations = analytics.get_topic_recommendations(user_id, limit=5)
    
    if recommendations:
        for rec in recommendations:
            topic = rec['topic']
            with st.expander(f"📌 {topic['topic_name']} - {topic['subject']}"):
                st.write(f"**Chapter:** {topic['chapter_name']}")
                st.write(f"**Difficulty:** {topic['difficulty_level']}")
                st.info(f"**Why:** {rec['reason']}")
                
                if st.button("📖 Start Learning", key=f"learn_{topic['id']}", use_container_width=True):
                    st.session_state.current_page = 'learn'
                    st.rerun()
    else:
        st.info("Start learning topics to get personalized recommendations!")
    
    # ===== RECENT ACTIVITY =====
    if overview['topics_started'] > 0:
        st.markdown("---")
        st.subheader("📅 Recent Activity (Last 7 Days)")
        
        activities = analytics.get_recent_activity(user_id, days=7)
        
        if activities:
            for activity in activities[:10]:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{activity['topic_name']}** ({activity['subject']})")
                with col2:
                    timestamp = activity['timestamp']
                    st.caption(timestamp[:10] if isinstance(timestamp, str) else str(timestamp))
        else:
            st.info("No recent activity in the last 7 days. Start learning!")


if __name__ == "__main__":
    show_dashboard()
