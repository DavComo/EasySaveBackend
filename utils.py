"""
Utility functions for the EasySave Backend API.

This module provides essential utility functions for:
- Unique identifier generation and manipulation
- Password hashing and verification
- Email validation
- Access key generation

The unique identifier system uses a dot-separated hierarchical format
with environment prefixes (e.g., "prod.username.path.to.resource").
"""

from enum import Enum
from functools import singledispatch
from typing import Any
import secrets
from argon2 import PasswordHasher


class envs(str, Enum):
    """
    Enumeration of available environments in the system.
    
    Attributes:
        test: Testing environment for safe experimentation.
        prod: Production environment for live data.
    """
    test = "test"
    prod = "prod"

    def __str__(self):
        """Return the environment name as a string."""
        return self.name


@singledispatch
def generateUniqueId(arg: Any, *args, **kwargs) -> str: # type: ignore
    """
    Generate a unique hierarchical identifier.
    
    This is a singledispatch function that generates unique IDs based on the
    argument type. It serves as the base implementation that raises an error
    for unsupported types.
    
    Args:
        arg: The input to generate an ID from. Supported types are registered
            via @generateUniqueId.register decorators.
    
    Raises:
        NotImplementedError: If the argument type is not supported.
    
    Returns:
        str: A dot-separated hierarchical unique identifier.
    
    Example:
        # Using list overload:
        id1 = generateUniqueId(["prod", "johndoe", "documents"])
        # Using env/user overload:
        id2 = generateUniqueId(envs.prod, "johndoe", "documents", "report1")
    """
    raise NotImplementedError(f"Unsupported type: {type(arg)}")


@generateUniqueId.register
def _(path: list) -> str: # type: ignore
    """
    Generate a unique ID from a list of path components.
    
    Args:
        path (list): List of strings representing the hierarchical path.
            First element should be an environment name.
    
    Returns:
        str: Dot-joined path string (e.g., "prod.johndoe.documents").
    
    Raises:
        ValueError: If the path list is empty.
        RuntimeError: If the generated ID fails validation.
    """
    if len(path) > 0: # type: ignore
        id = ".".join(path) # type: ignore
        if isUniqueIdValid(id):
            return id
        else:
            raise RuntimeError("Error when generating unique ID")
        
    raise ValueError("ID Path list cannot be empty.")


@generateUniqueId.register
def _(env: envs, user: str, *folders: list[str]) -> str:
    """
    Generate a unique ID from environment, user, and optional folder path.
    
    Args:
        env (envs): The environment enum value (prod or test).
        user (str): The username.
        *folders: Optional additional path components for sub-resources.
    
    Returns:
        str: Hierarchical unique identifier (e.g., "prod.johndoe.documents").
    
    Example:
        id1 = generateUniqueId(envs.prod, "johndoe")  # "prod.johndoe"
        id2 = generateUniqueId(envs.prod, "johndoe", "docs")  # "prod.johndoe.docs"
    """
    path: list[str] = ([str(env), user, *folders]) if len(folders) > 0 else ([str(env), user]) # type: ignore
    return generateUniqueId(path)


def separateUniqueId(id: str) -> list[str]:
    """
    Split a unique ID into its component parts.
    
    Args:
        id (str): The unique identifier to separate.
    
    Returns:
        list[str]: List of path components with the first element converted
            to an envs enum value.
    
    Raises:
        ValueError: If the ID format is invalid.
    
    Example:
        parts = separateUniqueId("prod.johndoe.documents")
        # Returns: [envs.prod, "johndoe", "documents"]
    """
    if not (isUniqueIdValid(id)):
        raise ValueError("Invalid Unique ID")
    
    idList = id.split(".")
    idList[0] = envs[idList[0]]

    return idList


def uniqueIdToMap(id: str) -> dict[str, str | list[str]]:
    """
    Convert a unique ID to a structured dictionary.
    
    Args:
        id (str): The unique identifier to parse.
    
    Returns:
        dict: Dictionary with keys 'env' (environment), 'username', and
            'folders' (list of sub-path components).
    
    Example:
        map = uniqueIdToMap("prod.johndoe.documents.work")
        # Returns: {
        #     "env": envs.prod,
        #     "username": "johndoe",
        #     "folders": ["documents", "work"]
        # }
    """
    idList = separateUniqueId(id)
    
    mapping: dict[str, str | list[str]] = {
        "env" : idList[0],
        "username" : idList[1],
        "folders" : idList[2:]
    }

    return mapping


def mapToUniqueId(map: dict[str, str | list[str]]):
    """
    Convert a dictionary to a unique ID string.
    
    Args:
        map (dict): Dictionary with 'env', 'username', and 'folders' keys.
    
    Returns:
        str: The hierarchical unique identifier.
    
    Example:
        map = {"env": envs.prod, "username": "johndoe", "folders": ["docs"]}
        id = mapToUniqueId(map)  # "prod.johndoe.docs"
    """
    return generateUniqueId(map["env"], map["username"], map["folders"])


def isUniqueIdValid(id: str) -> bool:
    """
    Validate a unique identifier format.
    
    A valid ID must:
    - Contain at least 2 components (environment.username)
    - Start with a valid environment name
    - Not contain empty components
    
    Args:
        id (str): The unique identifier to validate.
    
    Returns:
        bool: True if valid, False otherwise.
    
    Example:
        isUniqueIdValid("prod.johndoe")  # True
        isUniqueIdValid("invalid.user")  # False (invalid env)
        isUniqueIdValid("prod")          # False (too short)
    """
    idList = id.split(".")
    
    if len(idList) < 2:
        return False
    
    try:
        envs[idList[0]]
    except KeyError:
        return False

    for directory in idList:
        if not directory.strip():
            return False
    
    return True


def generateAccessKey() -> str:
    """
    Generate a cryptographically secure access key.
    
    Creates a 128-character hexadecimal string (64 bytes) suitable for
    use as an authentication token.
    
    Returns:
        str: A 128-character hexadecimal access key.
    
    Example:
        key = generateAccessKey()
        # Returns something like: "a3f5...d2e8" (128 characters)
    """
    return secrets.token_hex(64)


def validateEmail(email: str) -> bool:
    """
    Validate an email address format.
    
    Uses a regular expression to check for basic email format compliance.
    Checks for presence of @ symbol, valid characters, and domain structure.
    
    Args:
        email (str): The email address to validate.
    
    Returns:
        bool: True if the email format is valid, False otherwise.
    
    Example:
        validateEmail("user@example.com")  # True
        validateEmail("invalid.email")     # False
    """
    import re
    email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(email_regex, email) is not None


def hashPassword(password: str) -> str:
    """
    Hash a password using Argon2.
    
    Argon2 is a memory-hard password hashing function that is resistant
    to GPU-based attacks. The hash includes salt and is suitable for
    secure password storage.
    
    Args:
        password (str): The plain-text password to hash.
    
    Returns:
        str: The Argon2 hash string.
    
    Example:
        hashed = hashPassword("mySecurePassword123")
        # Returns an Argon2 hash string
    """
    return PasswordHasher().hash(password)


def verifyHash(hashedPassword: str, rawPassword: str) -> bool:
    """
    Verify a password against its Argon2 hash.
    
    Compares a plain-text password with an Argon2 hash to determine if
    they match. Uses constant-time comparison to prevent timing attacks.
    
    Args:
        hashedPassword (str): The stored Argon2 hash.
        rawPassword (str): The plain-text password to verify.
    
    Returns:
        bool: True if the password matches the hash, False otherwise.
    
    Example:
        hashed = hashPassword("myPassword")
        verifyHash(hashed, "myPassword")    # True
        verifyHash(hashed, "wrongPassword") # False
    """
    return PasswordHasher().verify(hashedPassword, rawPassword)