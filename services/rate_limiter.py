"""
Rate limiting service for security-sensitive operations.
Prevents brute force attacks and abuse of sensitive endpoints.
Requirements: 13.4
"""
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from typing import Tuple
import logging

logger = logging.getLogger('services')


class RateLimiter:
    """
    Service for rate limiting security-sensitive operations.
    Uses Django's cache backend to track request counts.
    """
    
    # Rate limit configurations
    PASSWORD_CHANGE_LIMIT = 5  # Maximum password change attempts
    PASSWORD_CHANGE_WINDOW = 3600  # Time window in seconds (1 hour)
    
    LOGIN_ATTEMPT_LIMIT = 5  # Maximum login attempts
    LOGIN_ATTEMPT_WINDOW = 900  # Time window in seconds (15 minutes)
    
    def __init__(self):
        """Initialize the rate limiter."""
        pass
    
    def check_password_change_limit(self, student_id: int) -> Tuple[bool, int]:
        """
        Check if a student has exceeded password change rate limit.
        
        Tracks password change attempts per student within a time window.
        Prevents abuse of password change functionality.
        
        Args:
            student_id: Student's database ID
            
        Returns:
            Tuple of (is_allowed: bool, remaining_attempts: int)
            - is_allowed: True if request is allowed, False if rate limit exceeded
            - remaining_attempts: Number of attempts remaining before limit
            
        Requirements: 13.4
        """
        cache_key = f'password_change_limit_{student_id}'
        
        # Get current attempt count from cache
        attempts = cache.get(cache_key, 0)
        
        # Check if limit exceeded
        if attempts >= self.PASSWORD_CHANGE_LIMIT:
            logger.warning(
                f"Password change rate limit exceeded for student {student_id}: "
                f"{attempts} attempts in last {self.PASSWORD_CHANGE_WINDOW} seconds"
            )
            return False, 0
        
        # Calculate remaining attempts
        remaining = self.PASSWORD_CHANGE_LIMIT - attempts
        
        return True, remaining
    
    def record_password_change_attempt(self, student_id: int) -> None:
        """
        Record a password change attempt for rate limiting.
        
        Increments the attempt counter for the student.
        Counter expires after PASSWORD_CHANGE_WINDOW seconds.
        
        Args:
            student_id: Student's database ID
            
        Requirements: 13.4
        """
        cache_key = f'password_change_limit_{student_id}'
        
        # Get current attempt count
        attempts = cache.get(cache_key, 0)
        
        # Increment and store with timeout
        cache.set(cache_key, attempts + 1, self.PASSWORD_CHANGE_WINDOW)
        
        logger.info(
            f"Password change attempt recorded for student {student_id}: "
            f"{attempts + 1}/{self.PASSWORD_CHANGE_LIMIT}"
        )
    
    def reset_password_change_limit(self, student_id: int) -> None:
        """
        Reset password change rate limit for a student.
        
        Called after successful password change or by admin.
        
        Args:
            student_id: Student's database ID
        """
        cache_key = f'password_change_limit_{student_id}'
        cache.delete(cache_key)
        logger.info(f"Password change rate limit reset for student {student_id}")
    
    def check_login_attempt_limit(self, identifier: str) -> Tuple[bool, int]:
        """
        Check if login attempts have exceeded rate limit.
        
        Tracks login attempts per identifier (username or school_id) within a time window.
        Prevents brute force attacks on login endpoints.
        
        Args:
            identifier: Username or school_id being used for login
            
        Returns:
            Tuple of (is_allowed: bool, remaining_attempts: int)
            - is_allowed: True if request is allowed, False if rate limit exceeded
            - remaining_attempts: Number of attempts remaining before limit
            
        Requirements: 13.4
        """
        cache_key = f'login_attempt_limit_{identifier}'
        
        # Get current attempt count from cache
        attempts = cache.get(cache_key, 0)
        
        # Check if limit exceeded
        if attempts >= self.LOGIN_ATTEMPT_LIMIT:
            logger.warning(
                f"Login rate limit exceeded for identifier {identifier}: "
                f"{attempts} attempts in last {self.LOGIN_ATTEMPT_WINDOW} seconds"
            )
            return False, 0
        
        # Calculate remaining attempts
        remaining = self.LOGIN_ATTEMPT_LIMIT - attempts
        
        return True, remaining
    
    def record_login_attempt(self, identifier: str, success: bool = False) -> None:
        """
        Record a login attempt for rate limiting.
        
        Increments the attempt counter for failed logins.
        Resets counter on successful login.
        
        Args:
            identifier: Username or school_id being used for login
            success: Whether the login was successful
            
        Requirements: 13.4
        """
        cache_key = f'login_attempt_limit_{identifier}'
        
        if success:
            # Reset counter on successful login
            cache.delete(cache_key)
            logger.info(f"Login successful for {identifier}, rate limit reset")
        else:
            # Increment counter for failed login
            attempts = cache.get(cache_key, 0)
            cache.set(cache_key, attempts + 1, self.LOGIN_ATTEMPT_WINDOW)
            logger.info(
                f"Failed login attempt recorded for {identifier}: "
                f"{attempts + 1}/{self.LOGIN_ATTEMPT_LIMIT}"
            )
    
    def reset_login_attempt_limit(self, identifier: str) -> None:
        """
        Reset login attempt rate limit for an identifier.
        
        Called by admin or after timeout period.
        
        Args:
            identifier: Username or school_id to reset
        """
        cache_key = f'login_attempt_limit_{identifier}'
        cache.delete(cache_key)
        logger.info(f"Login rate limit reset for {identifier}")
