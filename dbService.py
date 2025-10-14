"""
Database service layer for PostgreSQL operations.

This module provides the DBService class, which encapsulates all database
interactions for the EasySave Backend API. It handles:
- User account management (CRUD operations)
- Block data management (CRUD operations)
- Authentication and access key verification
- Transaction management with automatic rollback

The service uses psycopg2 for PostgreSQL connectivity and implements
connection pooling and cursor management.
"""

from typing import Optional, Callable, TypeVar, Any
from user import User
from block import Block
from functools import wraps
from customExceptions import *
import psycopg2
import psycopg2.extras
import atexit
import utils
import os




class DBService:
    """
    Database service for managing PostgreSQL operations.
    
    This class provides a high-level interface for all database operations
    in the EasySave system. It manages database connections, implements
    transaction handling, and provides methods for user and block management.
    
    Attributes:
        dsn (str): Database connection string from environment variable.
        conn: PostgreSQL connection object.
        cur: Standard database cursor for queries.
        dict_cur: Dictionary cursor for queries returning dict-like rows.
    
    Example:
        db = DBService()
        user_id = db.createUser("johndoe", "john@example.com", "password123")
        users = db.getUsers(username="johndoe", uniqueid=None, email=None, accessKey=None)
    """
    def __init__(self):
        """
        Initialize the database service and establish connection.
        
        Reads the DATABASE_DSN environment variable for connection details
        and sets up database cursors. Registers cleanup handler to close
        connection on program exit.
        """
        self.dsn = os.getenv("DATABASE_DSN")
        atexit.register(lambda: self.conn.close())

        self.conn = psycopg2.connect(self.dsn)
        self.cur = self.conn.cursor()
        self.dict_cur: psycopg2.extensions.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)


    F = TypeVar("F", bound=Callable[..., Any])

    def rollback_on_fail(func: F) -> F: # type: ignore
        """
        Decorator that automatically rolls back transactions on SQL failures.
        
        This decorator wraps database methods to provide automatic rollback
        when a failed SQL transaction is detected. This ensures database
        consistency even when errors occur during operations.
        
        Args:
            func: The function to wrap with rollback protection.
        
        Returns:
            The wrapped function with rollback capability.
        
        Raises:
            Propagates any exceptions after performing rollback.
        """
        @wraps(func)
        def wrapper(self, *args, **kwargs): # type: ignore
            try:
                return func(self, *args, **kwargs)
            except psycopg2.errors.InFailedSqlTransaction:
                self.conn.rollback() # type: ignore
                raise
        return wrapper  # type: ignore
    

    @rollback_on_fail
    def modify_data(self, sql: str, params: list[str]):
        """
        Execute a SQL statement that modifies data (INSERT, UPDATE, DELETE).
        
        Executes the SQL with parameters and commits the transaction.
        Automatically rolls back on failure via decorator.
        
        Args:
            sql (str): The SQL statement with %s placeholders.
            params (list[str]): List of parameters to substitute into SQL.
        
        Example:
            db.modify_data(
                "INSERT INTO users (name, email) VALUES (%s, %s)",
                ["John", "john@example.com"]
            )
        """
        self.cur.execute(sql, params)
        self.conn.commit()
    
    @rollback_on_fail
    def query_data(self, sql: str, params: list[str]):
        """
        Execute a SQL SELECT query and return results as tuples.
        
        Args:
            sql (str): The SQL SELECT statement with %s placeholders.
            params (list[str]): List of parameters to substitute into SQL.
        
        Returns:
            List of tuples representing the query results.
        
        Example:
            results = db.query_data(
                "SELECT * FROM users WHERE username = %s",
                ["johndoe"]
            )
        """
        self.cur.execute(sql, params)
        return self.cur.fetchall()
    
    @rollback_on_fail
    def query_dict_data(self, sql: str, params: list[str]):
        """
        Execute a SQL SELECT query and return results as dictionaries.
        
        Uses DictCursor to return rows as dict-like objects where columns
        can be accessed by name.
        
        Args:
            sql (str): The SQL SELECT statement with %s placeholders.
            params (list[str]): List of parameters to substitute into SQL.
        
        Returns:
            List of dict-like objects representing the query results.
        
        Example:
            results = db.query_dict_data(
                "SELECT * FROM users WHERE username = %s",
                ["johndoe"]
            )
            print(results[0]['email'])  # Access by column name
        """
        self.dict_cur.execute(sql, params)
        return self.dict_cur.fetchall()
    
    def verifyAccessKey(self, username: str, accessKey: str) -> str | None:
        """
        Verify that an access key matches the stored key for a username.
        
        This method is used for authentication. It checks that the access key
        is properly formatted (128 alphanumeric characters) and matches the
        key stored in the database for the given username.
        
        Args:
            username (str): The username to verify.
            accessKey (str): The access key to check.
        
        Returns:
            str | None: The access key if valid, None if invalid or not found.
        
        Example:
            key = db.verifyAccessKey("johndoe", "a3f5d2...")
            if key:
                print("Authentication successful")
        """
        if (len(accessKey) != 64*2) or (not accessKey.isalnum()):
            return None
        
        queryResult = self.query_data("""
            SELECT accessKey
            FROM users
            WHERE (
                users.username = %s AND
                users.accessKey = %s
            );""",
            [username, accessKey]
            )

        if (bool(queryResult)):
            return queryResult[0][0]
        return None


    def createUser(self, username: str, email: str, password: str, test:bool = False) -> int:
        """
        Create a new user account in the database.
        
        Creates a User object with hashed password and generated access key,
        validates the email format, checks for username uniqueness, and
        inserts the user into the database.
        
        Args:
            username (str): The desired username (must be unique).
            email (str): The user's email address (must be valid format).
            password (str): The plain-text password (will be hashed).
            test (bool, optional): Whether to create as test user. Defaults to False.
        
        Returns:
            int: 1 if successful.
        
        Raises:
            InvalidEmail: If the email format is invalid.
            NonuniqueUsername: If the username already exists.
        
        Example:
            user_id = db.createUser("johndoe", "john@example.com", "pass123")
        """
        env = (utils.envs.test if test else utils.envs.prod)
        user = User(username=username, email=email, password=password, env=env)

        if not utils.validateEmail(email):
            raise InvalidEmail("Invalid email format.")
        elif self.getUsers(username, None, None, None):
            raise NonuniqueUsername(f"User '{username}' already exists.")
        else:
            self.modify_data("""
                INSERT INTO users (username, uniqueid, email, accessKey, password)
                VALUES (%s, %s, %s, %s, %s);
                """, 
                [user.getUsername(), user.getUniqueid(), user.getEmail(), user.getAccessKey(), user.getPassword()])

            return 1


    def getUsers(
        self,
        username: Optional[str],
        uniqueid: Optional[str],
        email: Optional[str],
        accessKey: Optional[str]
    ) -> list[User]:
        """
        Retrieve users from the database based on search criteria.
        
        Searches for users matching any provided criteria. All non-None
        parameters are used as search conditions (AND logic).
        
        Args:
            username (Optional[str]): Filter by username.
            uniqueid (Optional[str]): Filter by unique ID.
            email (Optional[str]): Filter by email address.
            accessKey (Optional[str]): Filter by access key.
        
        Returns:
            list[User]: List of User objects matching the criteria.
                Empty list if no matches found.
        
        Example:
            # Find by username
            users = db.getUsers("johndoe", None, None, None)
            
            # Find by email
            users = db.getUsers(None, None, "john@example.com", None)
        """

        searchStatements: list[str] = []
        data: list[str] = []

        for key, value in {**locals()}.items():
            if (type(value) == str):
                searchStatements.append(f"{str(key)} = %s")
                data.append(value)

        searchStatement = " AND ".join(searchStatements)

        queryResult = self.query_dict_data(("SELECT * FROM users WHERE " + searchStatement), data)
        
        users: list[User] = []

        for result in queryResult:
            userEnv = utils.envs[str(utils.uniqueIdToMap(result['uniqueid'])['env'])] # type: ignore
            user = User(
                username=result['username'], # type: ignore
                uniqueid=result['uniqueid'], # type: ignore
                email=result['email'], # type: ignore
                accessKey=result['accesskey'], # type: ignore
                password=result['password'], # type: ignore
                env=userEnv
            )
            users.append(user)

        return users


    def updateUser(
        self,
        uniqueid: str,
        valuesToUpdate: dict[str, str]
    ):
        """
        Update user profile fields in the database.
        
        Updates specified fields for a user identified by unique ID.
        Only email, accessKey, and password fields can be updated.
        Email values are validated before update.
        
        Args:
            uniqueid (str): The unique identifier of the user to update.
            valuesToUpdate (dict[str, str]): Dictionary of field:value pairs
                to update. Allowed keys: 'email', 'accessKey', 'password'.
        
        Raises:
            KeyError: If an invalid field name is provided or email format is invalid.
        
        Example:
            db.updateUser(
                "prod.johndoe",
                {"email": "newemail@example.com", "password": "newhashedpass"}
            )
        """
        
        allowedValues: set[str] = {"email", "accessKey", "password"}

        setStatements: list[str] = []

        for key, value in valuesToUpdate.items():
            if key not in allowedValues:
                raise KeyError(f"Invalid key '{key}' in valuesToUpdate. Allowed keys are: {allowedValues}")
            if key == "email" and not utils.validateEmail(value):
                raise KeyError(f"Invalid email format for value: {value}")
            setStatements.append(str(key + " = '" + value + "'"))

        setStatement: str = ", ".join(setStatements)
        
        self.modify_data(("UPDATE users SET " + setStatement + " WHERE users.uniqueID = %s"), [uniqueid])


    def login(
        self,
        username: str,
        password: str
    ) -> str | None:
        """
        Authenticate a user and return their access key.
        
        Verifies the username and password combination. If valid, returns
        the user's access key for subsequent API requests.
        
        Args:
            username (str): The username to authenticate.
            password (str): The plain-text password to verify.
        
        Returns:
            str | None: The access key if authentication successful, None if
                credentials are invalid or verification fails.
        
        Raises:
            RuntimeError: If multiple users found with same username (database
                integrity issue).
        
        Example:
            access_key = db.login("johndoe", "password123")
            if access_key:
                print(f"Login successful: {access_key}")
            else:
                print("Invalid credentials")
        """
        
        queryResult = self.query_dict_data(("SELECT * FROM users WHERE username=%s"), [username])

        if len(queryResult) == 1:
            try:
                if utils.verifyHash(queryResult[0]["password"], password): # type: ignore
                    return queryResult[0]['accesskey'] # type: ignore
            except:
                return None
        elif len(queryResult) == 0:
            return None
        else:
            raise RuntimeError("Unusual amount of users found when logging in.")


    def createBlock(
        self,
        identifier: str,
        content: str
    ) -> int:
        """
        Create a new data block in the database.
        
        Inserts a new block with the given hierarchical identifier and content.
        
        Args:
            identifier (str): The full hierarchical identifier for the block
                (e.g., "prod.johndoe.documents.report1").
            content (str): The data content to store in the block.
        
        Returns:
            int: 1 if successful.
        
        Example:
            block_id = db.createBlock(
                "prod.johndoe.documents.report1",
                "This is my report content"
            )
        """
        
        valueBlock: Block = Block(identifier, content)

        self.modify_data("""
            INSERT INTO data (identifier, value)
            VALUES (%s, %s);
            """, 
            [valueBlock.getIdentifier(), valueBlock.getValue()])

        return 1


    def getBlocks(
        self,
        identifier: str
    ):
        """
        Retrieve blocks matching an identifier prefix.
        
        Uses SQL LIKE pattern matching to find all blocks whose identifier
        starts with the given prefix. This enables hierarchical queries
        (e.g., get all blocks under "prod.johndoe.documents").
        
        Args:
            identifier (str): The identifier prefix to match. Results will
                include all blocks starting with this path.
        
        Returns:
            list[Block]: List of Block objects matching the prefix.
        
        Example:
            # Get all blocks under documents folder
            blocks = db.getBlocks("prod.johndoe.documents")
            # Returns: documents.report1, documents.report2, documents.work.notes, etc.
        """
        
        queryResult = self.query_dict_data(("SELECT * FROM data WHERE identifier LIKE %s"), [(identifier + "%")])
        
        blocks: list[Block] = []

        for result in queryResult:
            block = Block(
                identifier=result['identifier'], # type: ignore
                value=result['value'] # type: ignore
            )
            blocks.append(block)

        return blocks


    def updateBlock(
        self,
        identifier: str,
        value: str
    ):
        """
        Update the value of an existing block.
        
        Updates the content of a block identified by its full hierarchical path.
        
        Args:
            identifier (str): The full identifier of the block to update.
            value (str): The new content to store in the block.
        
        Example:
            db.updateBlock(
                "prod.johndoe.documents.report1",
                "Updated report content"
            )
        """
        
        self.modify_data(("UPDATE data SET value=%s WHERE data.identifier = %s"), [value, identifier])

    def deleteBlock(
        self,
        identifier: str
    ):
        """
        Delete a block from the database.
        
        Removes the block with the specified identifier. Note that this only
        deletes the exact block, not child blocks in the hierarchy.
        
        Args:
            identifier (str): The full identifier of the block to delete.
        
        Example:
            db.deleteBlock("prod.johndoe.documents.report1")
        """
        self.modify_data(("DELETE FROM data WHERE data.identifier = %s"), [identifier])