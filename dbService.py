from typing import Optional
from utils import *
from user import User
import psycopg2
import psycopg2.extras
import atexit
import asyncio

connection = psycopg2.connect(dbname='EasySaveDB', user='postgres', password='StrongPassword', host='localhost')
cursor = connection.cursor()
dictCursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

atexit.register(lambda: connection.close())


def createUser(username: str, email: str, password: str, test:bool = False):
    env = (envs.test if test else envs.prod)
    user = User(username=username, email=email, password=REDACTED env=env)

    cursor.execute("""
        INSERT INTO users (username, uniqueid, email, accessKey, password)
        VALUES (%s, %s, %s, %s, %s)
        """, 
        (user.username, user.uniqueid, user.email, user.accessKey, user.password))

    connection.commit()

    return 1


def getUsers(
    username: Optional[str],
    uniqueid: Optional[str],
    email: Optional[str],
    accessKey: Optional[str]
):

    searchStatements = []
    data = []
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
    queryResult = dictCursor.fetchall()
    if len(queryResult) > 1:
        raise RuntimeError("Unexpected number of users found: " + len(queryResult))
    elif len(queryResult) == 0:
        return None
    
    users = []

    for result in queryResult:
        userEnv = envs[str(mapUniqueId(result['uniqueid'])['env'])]
        user = User(username=result['username'], uniqueid=result['uniqueid'], email=result['email'], accessKey=result['accesskey'], password=REDACTED'password'], env=userEnv)
        users.append(user)

    return users
