from typing import Optional
import utils
from user import User
from block import Block
import psycopg2
import psycopg2.extras
import atexit

connection = psycopg2.connect(dbname='EasySaveDB', user='postgres', password='StrongPassword', host='localhost')
cursor = connection.cursor()
dictCursor: psycopg2.extensions.cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

atexit.register(lambda: connection.close())


def verifyAccessKey(username: str, accessKey: str) -> str | None:
    if (len(accessKey) != 64*2) or (not accessKey.isalnum()):
        return None
    
    cursor.execute("""
        SELECT accessKey
        FROM users
        WHERE (
            users.username = %s AND
            users.accessKey = %s
        );""",
        (username, accessKey)
        )

    queryResult = cursor.fetchone()

    if (bool(queryResult)):
        return queryResult[0]
    return None


def createUser(username: str, email: str, password: str, test:bool = False) -> int:
    env = (utils.envs.test if test else utils.envs.prod)
    user = User(username=username, email=email, password=REDACTED env=env)

    cursor.execute("""
        INSERT INTO users (username, uniqueid, email, accessKey, password)
        VALUES (%s, %s, %s, %s, %s);
        """, 
        (user.getUsername(), user.getUniqueid(), user.getEmail(), user.getAccessKey(), user.getPassword()))

    connection.commit()

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

    dictCursor.execute(("SELECT * FROM users WHERE " + searchStatement), data)
    queryResult: list[tuple[str, str]] = dictCursor.fetchall()
    
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
    
    cursor.execute(("UPDATE users SET " + setStatement + " WHERE users.uniqueID = %s"), [uniqueid])
    
    connection.commit()


def login(
    username: str,
    password: str
) -> str | None:
    
    hashedPassword: str = utils.hashPassword(password)

    dictCursor.execute(("SELECT * FROM users WHERE username=%s AND password=REDACTED"), [username, hashedPassword])
    queryResult: list[tuple[str, str]] = dictCursor.fetchall()

    if len(queryResult) == 1:
        return queryResult[0]['accesskey'] # type: ignore
    elif len(queryResult) == 0:
        return None
    else:
        raise RuntimeError("Unusual amount of users found when logging in.")


def createBlock(
    identifier: str,
    content: str
) -> int:
    
    valueBlock: Block = Block(identifier, content)

    cursor.execute("""
        INSERT INTO data (identifier, value)
        VALUES (%s, %s);
        """, 
        (valueBlock.getIdentifier(), valueBlock.getValue()))

    connection.commit()

    return 1


def getBlocks(
    identifier: str
):
    
    dictCursor.execute(("SELECT * FROM data WHERE identifier LIKE %s"), [(identifier + "%")])
    queryResult: list[tuple[str, str]] = dictCursor.fetchall()
    
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
    
    cursor.execute(("UPDATE data SET value=%s WHERE data.identifier = %s"), [value, identifier])
    
    connection.commit()