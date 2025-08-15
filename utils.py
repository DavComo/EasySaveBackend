from enum import Enum
from functools import singledispatch
from typing import Any

class envs(str, Enum):
    test = "test"
    prod = "prod"

    def __str__(self):
        return self.name


@singledispatch
def generateUniqueId(arg: Any, *args, **kwargs) -> str:
    raise NotImplementedError(f"Unsupported type: {type(arg)}")

@generateUniqueId.register
def _(path: list) -> str:
    if len(path) > 0:
        id = ".".join(path)
        if isUniqueIdValid(id):
            return id
        else:
            raise RuntimeError("Error when generating unique ID")
        
    raise ValueError("ID Path list cannot be empty.")

@generateUniqueId.register
def _(env: envs, user: str, *folders) -> str:
    path = [str(env), user, *folders]
    return generateUniqueId(path)


def separateUniqueId(id: str) -> list:
    if not (isUniqueIdValid(id)):
        raise ValueError("Invalid Unique ID")
    
    id = id.split(".")
    id[0] = envs[id[0]]

    return id


def mapUniqueId(id: str) -> dict:
    id = separateUniqueId(id)
    
    mapping = {
        "env" : None,
        "username" : None,
        "folders" : []
    }

    mapping["env"] = id[0]
    mapping["username"] = id[1]
    mapping["folders"] = id[2:]

    return mapping


def isUniqueIdValid(id: str) -> bool:
    id = id.split(".")
    
    if len(id) < 2:
        return False
    
    try:
        env = envs[id[0]]
    except KeyError:
        return False

    for directory in id:
        if not directory.strip():
            return False
    
    return True
    