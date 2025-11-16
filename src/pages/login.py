"""
User Login Page
"""

import streamlit as st
from src.core.auth import AuthService, SessionManager
from src.data.db import db


def show_login_page():
    """Display login form and handle authentication"""
    
    st.title("🎓 MindMentor - Login")
    st.markdown("Welcome back! Log in to continue your JEE preparation")
    
    with st.form("login_form"):
        username = st.text_input(
            "Username",
            placeholder="Enter your username"
        )
        
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password"
        )
        
        col1, col2 = st.columns([1, 1])
        with col1:
            login_button = st.form_submit_button("Login", use_container_width=True)
        
        if login_button:
            # Validate inputs
            if not username or not password:
                st.error("Please enter both username and password")
            else:
                # Get user from database
                user = db.get_user_by_username(username)
                
                if user is None:
                    st.error("❌ Invalid username or password")
                else:
                    # Verify password
                    if AuthService.verify_password(password, user['password_hash']):
                        # Password correct - create session
                        SessionManager.create_session(st.session_state, user)
                        
                        # Update last login
                        db.update_last_login(user['id'])
                        
                        st.success(f"✅ Welcome back, {user['name']}!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")
    
    # Link to registration page
    st.markdown("---")
    st.markdown("### Don't have an account?")
    
    if st.button("Create New Account", use_container_width=True):
        st.session_state.show_login = False
        st.rerun()
    
    # Optional: Demo account info
    with st.expander("ℹ️ Demo Account (for testing)"):
        st.info("""
        You can create a new account or use the registration form above.
        
        **Tips for choosing a username:**
        - Must start with a letter
        - Use letters, numbers, and underscores
        - 3-50 characters long
        """)


if __name__ == "__main__":
    show_login_page()
