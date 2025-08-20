from enum import Enum
from functools import singledispatch
from typing import Any
import secrets

class envs(str, Enum):
    test = "test"
    prod = "prod"

    def __str__(self):
        return self.name


@singledispatch
def generateUniqueId(arg: Any, *args, **kwargs) -> str: # type: ignore
    raise NotImplementedError(f"Unsupported type: {type(arg)}")

@generateUniqueId.register
def _(path: list) -> str: # type: ignore
    print(path)
    if len(path) > 0: # type: ignore
        id = ".".join(path) # type: ignore
        if isUniqueIdValid(id):
            return id
        else:
            raise RuntimeError("Error when generating unique ID")
        
    raise ValueError("ID Path list cannot be empty.")

@generateUniqueId.register
def _(env: envs, user: str, *folders: list[str]) -> str:
    path: list[str] = ([str(env), user, *folders]) if len(folders) > 0 else ([str(env), user]) # type: ignore
    return generateUniqueId(path)


def separateUniqueId(id: str) -> list[str]:
    if not (isUniqueIdValid(id)):
        raise ValueError("Invalid Unique ID")
    
    idList = id.split(".")
    idList[0] = envs[idList[0]]

    return idList


def uniqueIdToMap(id: str) -> dict[str, str | list[str]]:
    idList = separateUniqueId(id)
    
    mapping: dict[str, str | list[str]] = {
        "env" : idList[0],
        "username" : idList[1],
        "folders" : idList[2:]
    }

    return mapping

def mapToUniqueId(map: dict[str, str | list[str]]):
    return generateUniqueId(map["env"], map["username"], map["folders"])

def isUniqueIdValid(id: str) -> bool:
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
    return secrets.token_hex(64)