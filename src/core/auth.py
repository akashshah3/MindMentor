"""
Authentication module for MindMentor
Handles user registration, login, and password management
"""

import bcrypt
from typing import Optional, Dict, Tuple
from datetime import datetime


class AuthService:
    """Service for authentication operations"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password as string
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash
        
        Args:
            password: Plain text password
            hashed_password: Hashed password from database
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception:
            return False
    
    @staticmethod
    def validate_password(password: str) -> Tuple[bool, str]:
        """
        Validate password meets requirements
        
        Args:
            password: Password to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password) < 6:
            return False, "Password must be at least 6 characters long"
        
        if len(password) > 128:
            return False, "Password must be less than 128 characters"
        
        # Add more validation rules as needed
        # if not any(c.isupper() for c in password):
        #     return False, "Password must contain at least one uppercase letter"
        
        return True, ""
    
    @staticmethod
    def validate_username(username: str) -> Tuple[bool, str]:
        """
        Validate username meets requirements
        
        Args:
            username: Username to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(username) < 3:
            return False, "Username must be at least 3 characters long"
        
        if len(username) > 50:
            return False, "Username must be less than 50 characters"
        
        if not username.isalnum() and '_' not in username:
            return False, "Username can only contain letters, numbers, and underscores"
        
        if not username[0].isalpha():
            return False, "Username must start with a letter"
        
        return True, ""
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """
        Basic email validation
        
        Args:
            email: Email to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not email:
            return True, ""  # Email is optional
        
        if '@' not in email or '.' not in email:
            return False, "Invalid email format"
        
        if len(email) > 255:
            return False, "Email must be less than 255 characters"
        
        return True, ""


class SessionManager:
    """Manage user sessions in Streamlit"""
    
    @staticmethod
    def create_session(session_state, user_data: Dict):
        """
        Create a new user session
        
        Args:
            session_state: Streamlit session state
            user_data: Dictionary with user information (id, username, name, etc.)
        """
        session_state.authenticated = True
        session_state.user_id = user_data['id']
        session_state.username = user_data['username']
        session_state.user_name = user_data['name']
        session_state.exam_target = user_data.get('exam_target')
        session_state.login_time = datetime.now()
    
    @staticmethod
    def clear_session(session_state):
        """
        Clear user session (logout)
        
        Args:
            session_state: Streamlit session state
        """
        for key in ['authenticated', 'user_id', 'username', 'user_name', 
                    'exam_target', 'login_time']:
            if key in session_state:
                del session_state[key]
    
    @staticmethod
    def is_authenticated(session_state) -> bool:
        """
        Check if user is authenticated
        
        Args:
            session_state: Streamlit session state
            
        Returns:
            True if authenticated, False otherwise
        """
        return getattr(session_state, 'authenticated', False)
    
    @staticmethod
    def get_user_id(session_state) -> Optional[int]:
        """
        Get current user ID from session
        
        Args:
            session_state: Streamlit session state
            
        Returns:
            User ID if authenticated, None otherwise
        """
        return getattr(session_state, 'user_id', None)
    
    @staticmethod
    def require_auth(session_state):
        """
        Decorator/helper to require authentication
        Raises exception if not authenticated
        
        Args:
            session_state: Streamlit session state
            
        Raises:
            Exception: If user is not authenticated
        """
        if not SessionManager.is_authenticated(session_state):
            raise Exception("Authentication required")
