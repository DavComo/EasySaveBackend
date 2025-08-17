from utils import *
import secrets

class User:
    env: envs
    username: str
    uniqueid: str
    email: str
    accessKey: str
    password: str

    def __init__(self, username, email, password, env=envs.prod, uniqueid=None, accessKey=None):
        self.env = env
        self.username = username
        if uniqueid:
            self.uniqueid = uniqueid
        else:
            self.uniqueid = generateUniqueId(env, username)
        self.email = email
        if accessKey:
            self.accessKey = accessKey
        else:
            self.accessKey = generateAccessKey()
        self.password = password
