"""
User data model for authentication and account management.

This module defines the User class, which represents a user account in the system.
Users have credentials, environment assignment, and a hierarchical unique identifier.
"""

import utils


class User:
    """
    Represents a user account in the EasySave system.
    
    A User contains authentication credentials, profile information, and is assigned
    to an environment (production or test). Each user has a unique hierarchical
    identifier based on their environment and username.
    
    Attributes:
        env (utils.envs): The environment this user belongs to (prod or test).
        username (str): The username for login and identification.
        uniqueid (str): The full hierarchical identifier (e.g., "prod.johndoe").
        email (str): The user's email address.
        accessKey (str): The 128-character authentication access key.
        password (str): The Argon2 hashed password.
    
    Example:
        user = User(
            username="johndoe",
            email="john@example.com",
            password="securepass123",
            env=utils.envs.prod
        )
        print(user.getUniqueid())  # "prod.johndoe"
    """
    env: utils.envs
    username: str
    uniqueid: str
    email: str
    accessKey: str
    password: str

    def __init__(self, username: str, email: str, password: str, env: utils.envs=utils.envs.prod, uniqueid: str | None =None, accessKey: str | None =None):
        """
        Initialize a new User instance.
        
        Creates a user with the provided credentials. If uniqueid or accessKey
        are not provided, they are automatically generated.
        
        Args:
            username (str): The username for this account.
            email (str): The user's email address.
            password (str): The plain-text password (will be hashed).
            env (utils.envs, optional): The environment assignment. Defaults to prod.
            uniqueid (str | None, optional): Preset unique ID. If None, generated
                from env and username.
            accessKey (str | None, optional): Preset access key. If None, a new
                cryptographically secure key is generated.
        """
        self.env = env
        self.username = username
        if uniqueid:
            self.uniqueid = uniqueid
        else:
            self.uniqueid = utils.generateUniqueId(env, username)
        self.email = email
        if accessKey:
            self.accessKey = accessKey
        else:
            self.accessKey = utils.generateAccessKey()
        self.password = utils.hashPassword(password)

    def __str__(self) -> str:
        """
        Get a string representation of the user.
        
        Returns:
            str: A formatted string with user details (excluding sensitive data).
        """
        return f"User(env={self.env}, username={self.username}, uniqueid={self.uniqueid}, email={self.email}, accessKey={self.accessKey})"
    
    def getEnv(self) -> utils.envs:
        """
        Get the environment this user belongs to.
        
        Returns:
            utils.envs: The environment enum value (prod or test).
        """
        return self.env
    
    def setEnv(self, env: utils.envs) -> None:
        """
        Set the environment for this user.
        
        Args:
            env (utils.envs): The new environment assignment.
        """
        self.env = env

    def getUsername(self) -> str:
        """
        Get the username.
        
        Returns:
            str: The username.
        """
        return self.username
    
    def setUsername(self, username: str) -> None:
        """
        Set the username.
        
        Args:
            username (str): The new username.
        """
        self.username = username

    def getUniqueid(self) -> str:
        """
        Get the unique identifier.
        
        Returns:
            str: The hierarchical unique identifier (e.g., "prod.johndoe").
        """
        return self.uniqueid
        
    def setUniqueid(self, uniqueid: str) -> None:
        """
        Set the unique identifier.
        
        Args:
            uniqueid (str): The new unique identifier.
        """
        self.uniqueid = uniqueid

    def getEmail(self) -> str:
        """
        Get the email address.
        
        Returns:
            str: The user's email address.
        """
        return self.email
    
    def setEmail(self, email: str) -> None:
        """
        Set the email address.
        
        Args:
            email (str): The new email address.
        """
        self.email = email

    def getAccessKey(self) -> str:
        """
        Get the access key for authentication.
        
        Returns:
            str: The 128-character hexadecimal access key.
        """
        return self.accessKey
    
    def setAccessKey(self, accessKey: str) -> None:
        """
        Set the access key.
        
        Args:
            accessKey (str): The new access key.
        """
        self.accessKey = accessKey
    
    def getPassword(self) -> str:
        """
        Get the hashed password.
        
        Returns:
            str: The Argon2 hashed password.
        """
        return self.password
    
    def setPassword(self, password: str) -> None:
        """
        Set the password.
        
        Note: This method expects an already-hashed password. To set a plain-text
        password, use utils.hashPassword() first.
        
        Args:
            password (str): The hashed password to store.
        """
        self.password = password