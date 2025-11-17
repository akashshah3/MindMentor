"""
MindMentor - AI-driven JEE Preparation System
Main Application Entry Point
"""

import streamlit as st
from src.core.auth import SessionManager
from src.pages.login import show_login_page
from src.pages.register import show_registration_page
from src.pages.dashboard import show_dashboard
from src.pages.learn import main as show_learn_page
from src.pages.quiz import main as show_quiz_page


# Page configuration
st.set_page_config(
    page_title="MindMentor - JEE Preparation",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .stButton>button {
        background-color: #1f77b4;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables"""
    if 'show_login' not in st.session_state:
        st.session_state.show_login = True
    
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'dashboard'


def show_sidebar():
    """Display sidebar with navigation and user info"""
    with st.sidebar:
        st.title("🎓 MindMentor")
        st.markdown("---")
        
        if SessionManager.is_authenticated(st.session_state):
            # Show user info
            st.success(f"Logged in as: **{st.session_state.username}**")
            
            st.markdown("### Navigation")
            
            # Navigation menu
            if st.button("📊 Dashboard", use_container_width=True):
                st.session_state.current_page = "dashboard"
                st.rerun()
            
            if st.button("📖 Learn", use_container_width=True):
                st.session_state.current_page = "learn"
                st.rerun()
            
            if st.button("✍️ Practice", use_container_width=True):
                st.session_state.current_page = "quiz"
                st.rerun()
            
            st.button("📅 Schedule", use_container_width=True, disabled=True,
                     help="Coming soon!")
            st.button("📈 Analytics", use_container_width=True, disabled=True,
                     help="Coming soon!")
            
            st.markdown("---")
            
            # Logout button
            if st.button("🚪 Logout", use_container_width=True):
                SessionManager.clear_session(st.session_state)
                st.session_state.show_login = True
                st.rerun()
        
        else:
            st.info("Please log in to access features")
            
            st.markdown("### About")
            st.write("""
            **MindMentor** is your AI-powered companion for JEE preparation.
            
            **Features:**
            - 🤖 Personalized AI tutoring
            - 📝 Adaptive quizzes
            - 📊 Progress tracking
            - 📅 Smart study planning
            """)


def main():
    """Main application logic"""
    init_session_state()
    show_sidebar()
    
    # Routing logic
    if SessionManager.is_authenticated(st.session_state):
        # User is logged in - route to appropriate page
        current_page = st.session_state.get('current_page', 'dashboard')
        
        if current_page == 'learn':
            show_learn_page()
        elif current_page == 'quiz':
            show_quiz_page()
        else:
            show_dashboard()
    
    else:
        # User is not logged in - show login or registration
        if st.session_state.show_login:
            show_login_page()
        else:
            show_registration_page()


if __name__ == "__main__":
    main()
