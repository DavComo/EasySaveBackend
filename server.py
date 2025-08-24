from fastapi import FastAPI, WebSocket, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import dbService
import uvicorn
import asyncio # type: ignore
import json

app = FastAPI()
active: set[WebSocket] = set()


MIDDLEWARE_EXCLUSIONS = ['/login', '/create_user']

origins = [
    "http://63.179.18.244:80",
    "http://63.179.18.244:8000",
    "http://0.0.0.0:8000"
           ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def verify_request_credentials(request: Request, call_next): # type: ignore
    if request.url.path not in MIDDLEWARE_EXCLUSIONS and request.method != "OPTIONS":
        if 'RequesterUsername' not in request.headers or 'RequesterAccessKey' not in request.headers:
            return JSONResponse(status_code=401, content={"detail": "Authorization credentials required."})
        username = request.headers['RequesterUsername']
        accessKey = request.headers['RequesterAccessKey']
        if not accessKey or not username:
            return JSONResponse(status_code=401, content={"detail": "Authorization credentials required."})
        if not dbService.verifyAccessKey(username, accessKey):
                        return JSONResponse(status_code=401, content={"detail": "Authorization credentials invalid."})

    try:
        response = await call_next(request) # type: ignore
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": type(e).__name__ + ": " + e.args[0]})
    return response # type: ignore


@app.post("/create_user")
async def create_user(username: str, email: str, password: str, test:bool = False):
    dbService.createUser(username, email, password, test)


@app.get("/get_user")
async def get_user(
    username: Optional[str] = None,
    uniqueid: Optional[str] = None,
    email: Optional[str] = None,
    accessKey: Optional[str] = None
) -> dict[str, str]:

    count = sum([bool(username), bool(uniqueid), bool(email), bool(accessKey)])
    if count > 1:
        raise RuntimeError("Cannot pass in more than one argument when searching for a user.")

    users = dbService.getUsers(username, uniqueid, email, accessKey)
    if len(users) == 0:
        return {} # type: ignore

    user = users[0].__dict__
    del user["password"]
    del user["accessKey"]
    return user


@app.patch("/update_user")
async def update_user(
    request: Request,
    newValuesJSON: str
):
    username = request.headers["RequesterUsername"]
    uniqueid: str = dbService.getUsers(username, None, None, None)[0].getUniqueid()
    try:
        dbService.updateUser(uniqueid, json.loads(newValuesJSON))
    except KeyError as e:
        raise HTTPException(422, e.args[0])

@app.get("/login")
async def login(username: str, password: str):
    print(username + ", " + password)
    try:
        accessKey: str | None = dbService.login(username, password)
    except RuntimeError as e:
        raise HTTPException(500, e.args[0])
    
    if (accessKey):
        return {"accessKey" : accessKey}
    else:
        raise HTTPException(401, "Invalid login details.")
    
@app.post("/create_block")
async def create_block(
    request: Request,
    extendedIdentifier: str,
    value: str
):
    username = request.headers["RequesterUsername"]
    uniqueid: str = dbService.getUsers(username, None, None, None)[0].getUniqueid()
    fullIdentifier = uniqueid + "." + extendedIdentifier
    
    dbService.createBlock(fullIdentifier, value)

@app.get("/get_blocks")
async def get_blocks(
    request: Request,
    extendedIdentifier: str
):
    
    username = request.headers["RequesterUsername"]
    uniqueid: str = dbService.getUsers(username, None, None, None)[0].getUniqueid()
    fullIdentifier = uniqueid + "." + extendedIdentifier

    blocks = dbService.getBlocks(fullIdentifier)
    blocksNormalized: list[dict[str, str]] = []
    for block in blocks:
        blocksNormalized.append(block.__dict__)
    return blocksNormalized

@app.patch("/update_block")
async def update_block(
    request: Request,
    extendedIdentifier: str,
    value: str
):

    username = request.headers["RequesterUsername"]
    uniqueid: str = dbService.getUsers(username, None, None, None)[0].getUniqueid()
    fullIdentifier = uniqueid + "." + extendedIdentifier

    dbService.updateBlock(fullIdentifier, value)

@app.post("/delete_block")
async def delete_block(
    request: Request,
    extendedIdentifier: str,
):

    username = request.headers["RequesterUsername"]
    uniqueid: str = dbService.getUsers(username, None, None, None)[0].getUniqueid()
    fullIdentifier = uniqueid + "." + extendedIdentifier

    dbService.deleteBlock(fullIdentifier)


if __name__ == "__main__":
    #print(type(verifyAccessKey("aavidcomor", "1b4e9929685af5f7d0ed681e067c85b99063c7bc6a8f3dba97d72b542d65bac46fe839d888c04c4fab78310e35c3d01279b4ac4c799ad4bc6fdf195a6e01a424")))
    uvicorn.run("server:app", host="0.0.0.0", port=8000)
