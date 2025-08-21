import utils

class User:
    env: utils.envs
    username: str
    uniqueid: str
    email: str
    accessKey: str
    password: str

    def __init__(self, username: str, email: str, password: str, env: utils.envs=utils.envs.prod, uniqueid: str | None =None, accessKey: str | None =None):
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
        return f"User(env={self.env}, username={self.username}, uniqueid={self.uniqueid}, email={self.email}, accessKey={self.accessKey})"
    
    def getEnv(self) -> utils.envs:
        return self.env
    
    def setEnv(self, env: utils.envs) -> None:
        self.env = env

    def getUsername(self) -> str:
        return self.username
    
    def setUsername(self, username: str) -> None:
        self.username = username

    def getUniqueid(self) -> str:
            return self.uniqueid
        
    def setUniqueid(self, uniqueid: str) -> None:
            self.uniqueid = uniqueid

    def getEmail(self) -> str:
        return self.email
    
    def setEmail(self, email: str) -> None:
        self.email = email

    def getAccessKey(self) -> str:
        return self.accessKey
    
    def setAccessKey(self, accessKey: str) -> None:
        self.accessKey = accessKey
    
    def getPassword(self) -> str:
        return self.password
    
    def setPassword(self, password: str) -> None:
        self.password = password