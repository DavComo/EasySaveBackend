from utils import *
import secrets

class User:
    env: envs
    username: str
    uniqueid: str
    email: str
    accessKey: str
    password: str

    def __init__(self, username, email, password, env=envs.prod):
        self.env = env
        self.username = username
        self.uniqueid = generateUniqueId(env, username)
        self.email = email
        self.accessKey = secrets.token_hex(64)
        self.password = password
