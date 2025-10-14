"""
Custom exceptions for the EasySave Backend API.

This module defines domain-specific exceptions that provide meaningful
error messages for business logic violations in the application.
"""


class NonuniqueUsername(Exception):
    """
    Exception raised when attempting to create a user with a username that already exists.
    
    This exception is raised during user creation when the database already
    contains a user with the requested username. Usernames must be unique
    across the system.
    
    Example:
        raise NonuniqueUsername(f"User '{username}' already exists.")
    """
    pass


class InvalidEmail(Exception):
    """
    Exception raised when an invalid email address format is provided.
    
    This exception is raised when email validation fails, indicating that
    the provided email address does not match the expected email format
    (e.g., missing '@' symbol, invalid domain, etc.).
    
    Example:
        raise InvalidEmail("Invalid email format.")
    """
    pass