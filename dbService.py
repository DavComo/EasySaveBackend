from typing import Optional, Callable, TypeVar, Any
from user import User
from block import Block
from functools import wraps
from customExceptions import *
import psycopg2
import psycopg2.extras
import atexit
import utils




class DBService:
    def __init__(self, dsn: str):
        self.conn = psycopg2.connect(dsn)
        self.cur = self.conn.cursor()
        self.dict_cur: psycopg2.extensions.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)


    F = TypeVar("F", bound=Callable[..., Any])

    def rollback_on_fail(func: F) -> F: # type: ignore
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
        self.cur.execute(sql, params)
        self.conn.commit()
    
    @rollback_on_fail
    def query_data(self, sql: str, params: list[str]):
        self.cur.execute(sql, params)
        return self.cur.fetchall()
    
    @rollback_on_fail
    def query_dict_data(self, sql: str, params: list[str]):
        self.dict_cur.execute(sql, params)
        return self.dict_cur.fetchall()


serviceInstance = DBService("dbname=EasySaveDB user=postgres password=REDACTED host=localhost")
atexit.register(lambda: serviceInstance.conn.close())



def verifyAccessKey(username: str, accessKey: str) -> str | None:
    if (len(accessKey) != 64*2) or (not accessKey.isalnum()):
        return None
    
    queryResult = serviceInstance.query_data("""
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


def createUser(username: str, email: str, password: str, test:bool = False) -> int:
    env = (utils.envs.test if test else utils.envs.prod)
    user = User(username=username, email=email, password=REDACTED env=env)

    if not utils.validateEmail(email):
        raise InvalidEmail("Invalid email format.")
    elif getUsers(username, None, None, None):
        raise NonuniqueUsername(f"User '{username}' already exists.")
    else:
        serviceInstance.modify_data("""
            INSERT INTO users (username, uniqueid, email, accessKey, password)
            VALUES (%s, %s, %s, %s, %s);
            """, 
            [user.getUsername(), user.getUniqueid(), user.getEmail(), user.getAccessKey(), user.getPassword()])

        return 1


def getUsers(
    username: Optional[str],
    uniqueid: Optional[str],
    email: Optional[str],
    accessKey: Optional[str]
) -> list[User]:

    searchStatements: list[str] = []
    data: list[str] = []
    if type(username) == str:
        searchStatements.append("username = %s")
        data.append(username)
    if type(uniqueid) == str:
        searchStatements.append("uniqueid = %s")
        data.append(uniqueid)
    if type(email) == str:
        searchStatements.append("email = %s")
        data.append(email)
    if type(accessKey) == str:
        searchStatements.append("accessKey = %s")
        data.append(accessKey)

    searchStatement = " AND ".join(searchStatements)

    queryResult = serviceInstance.query_dict_data(("SELECT * FROM users WHERE " + searchStatement), data)
    
    users: list[User] = []

    for result in queryResult:
        userEnv = utils.envs[str(utils.uniqueIdToMap(result['uniqueid'])['env'])] # type: ignore
        user = User(
            username=result['username'], # type: ignore
            uniqueid=result['uniqueid'], # type: ignore
            email=result['email'], # type: ignore
            accessKey=result['accesskey'], # type: ignore
            password=REDACTED'password'], # type: ignore
            env=userEnv
        )
        users.append(user)

    return users


def updateUser(
    uniqueid: str,
    valuesToUpdate: dict[str, str]
):
    
    allowedValues: set[str] = {"email", "accessKey", "password"}

    setStatements: list[str] = []

    for key, value in valuesToUpdate.items():
        if key not in allowedValues:
            raise KeyError(f"Invalid key '{key}' in valuesToUpdate. Allowed keys are: {allowedValues}")
        if key == "email" and not utils.validateEmail(value):
            raise KeyError(f"Invalid email format for value: {value}")
        setStatements.append(str(key + " = '" + value + "'"))

    setStatement: str = ", ".join(setStatements)
    
    serviceInstance.modify_data(("UPDATE users SET " + setStatement + " WHERE users.uniqueID = %s"), [uniqueid])


def login(
    username: str,
    password: str
) -> str | None:
    
    queryResult = serviceInstance.query_dict_data(("SELECT * FROM users WHERE username=%s"), [username])

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
    identifier: str,
    content: str
) -> int:
    
    valueBlock: Block = Block(identifier, content)

    serviceInstance.modify_data("""
        INSERT INTO data (identifier, value)
        VALUES (%s, %s);
        """, 
        [valueBlock.getIdentifier(), valueBlock.getValue()])

    return 1


def getBlocks(
    identifier: str
):
    
    queryResult = serviceInstance.query_dict_data(("SELECT * FROM data WHERE identifier LIKE %s"), [(identifier + "%")])
    
    blocks: list[Block] = []

    for result in queryResult:
        block = Block(
            identifier=result['identifier'], # type: ignore
            value=result['value'] # type: ignore
        )
        blocks.append(block)

    return blocks


def updateBlock(
    identifier: str,
    value: str
):
    
    serviceInstance.modify_data(("UPDATE data SET value=%s WHERE data.identifier = %s"), [value, identifier])

def deleteBlock(
    identifier: str
):
    serviceInstance.modify_data(("DELETE FROM data WHERE data.identifier = %s"), [identifier])