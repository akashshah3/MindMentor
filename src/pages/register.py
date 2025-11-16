"""
User Registration Page
"""

import streamlit as st
from src.core.auth import AuthService
from src.data.db import db


def show_registration_page():
    """Display registration form and handle registration"""
    
    st.title("🎓 MindMentor - Register")
    st.markdown("Create your account to start your JEE preparation journey")
    
    with st.form("registration_form"):
        st.subheader("Account Information")
        
        # Account fields
        col1, col2 = st.columns(2)
        with col1:
            username = st.text_input(
                "Username *",
                placeholder="Enter username",
                help="3-50 characters, letters, numbers, and underscores only"
            )
        
        with col2:
            name = st.text_input(
                "Full Name *",
                placeholder="Enter your full name"
            )
        
        email = st.text_input(
            "Email (optional)",
            placeholder="your.email@example.com"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            password = st.text_input(
                "Password *",
                type="password",
                placeholder="Minimum 6 characters",
                help="At least 6 characters"
            )
        
        with col2:
            confirm_password = st.text_input(
                "Confirm Password *",
                type="password",
                placeholder="Re-enter password"
            )
        
        st.subheader("Study Preferences")
        
        col1, col2 = st.columns(2)
        with col1:
            exam_target = st.selectbox(
                "Target Exam *",
                options=["JEE_MAIN", "JEE_ADVANCED", "BOTH"],
                format_func=lambda x: {
                    "JEE_MAIN": "JEE Main",
                    "JEE_ADVANCED": "JEE Advanced",
                    "BOTH": "Both JEE Main & Advanced"
                }[x]
            )
        
        with col2:
            daily_hours = st.number_input(
                "Daily Study Hours *",
                min_value=0.5,
                max_value=24.0,
                value=4.0,
                step=0.5,
                help="How many hours can you dedicate daily?"
            )
        
        # Submit button
        submitted = st.form_submit_button("Create Account", use_container_width=True)
        
        if submitted:
            # Validate inputs
            errors = []
            
            if not username or not name or not password:
                errors.append("Please fill in all required fields (*)")
            
            if password != confirm_password:
                errors.append("Passwords do not match")
            
            # Validate username
            is_valid, error_msg = AuthService.validate_username(username)
            if not is_valid:
                errors.append(f"Username: {error_msg}")
            
            # Validate password
            is_valid, error_msg = AuthService.validate_password(password)
            if not is_valid:
                errors.append(f"Password: {error_msg}")
            
            # Validate email if provided
            if email:
                is_valid, error_msg = AuthService.validate_email(email)
                if not is_valid:
                    errors.append(f"Email: {error_msg}")
            
            # Display errors
            if errors:
                for error in errors:
                    st.error(error)
            else:
                # Hash password
                password_hash = AuthService.hash_password(password)
                
                # Create user
                user_id = db.create_user(
                    username=username,
                    password_hash=password_hash,
                    name=name,
                    email=email if email else None,
                    exam_target=exam_target,
                    daily_hours=daily_hours
                )
                
                if user_id:
                    st.success("✅ Account created successfully!")
                    st.info("Please log in to continue")
                    st.session_state.show_login = True
                    st.rerun()
                else:
                    st.error("❌ Username already exists. Please choose a different username.")
    
    # Link to login page
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("Already have an account? Login", use_container_width=True):
            st.session_state.show_login = True
            st.rerun()


if __name__ == "__main__":
    show_registration_page()
