from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from typing import Optional
from utils import *
from dbService import *
import uvicorn
import asyncio # type: ignore
import json

app = FastAPI()
active: set[WebSocket] = set()


MIDDLEWARE_EXCLUSIONS = ['/login', '/register']

@app.middleware("http")
async def verify_request_credentials(request: Request, call_next): # type: ignore
    if request.url.path not in MIDDLEWARE_EXCLUSIONS:
        username = request.headers['RequesterUsername']
        accessKey = request.headers['RequesterAccessKey']
        if not accessKey or not username:
            raise HTTPException(status_code=401, detail="Authorization credentials required.")
        if not verifyAccessKey(username, accessKey):
            raise HTTPException(status_code=401, detail="Authorization credentials invalid.")

    response = await call_next(request) # type: ignore
    return response # type: ignore


@app.post("/create_user")
async def create_user(username: str, email: str, password: str, test:bool = False):
    createUser(username, email, password, test)


@app.get("/get_user")
async def get_user(
    username: Optional[str] = None,
    uniqueid: Optional[str] = None,
    email: Optional[str] = None,
    accessKey: Optional[str] = None
):

    count = sum([bool(username), bool(uniqueid), bool(email), bool(accessKey)])
    if count > 1:
        raise RuntimeError("Cannot pass in more than one argument when searching for a user.")

    users = getUsers(username, uniqueid, email, accessKey)
    if len(users) == 0:
        return json.dumps({})

    user = users[0].__dict__
    del user["password"]
    return json.dumps(user)


@app.patch("/update_user")
async def update_user(
    uniqueid: str,
    newValuesJSON: str
):
    return updateUser(uniqueid, json.loads(newValuesJSON))


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    active.add(ws)
    try:
        while True:
            msg = await ws.receive_text()     # receive from a client
            # echo/process and broadcast to everyone:
            for peer in list(active):
                await peer.send_text(f"got: {msg}")
    except WebSocketDisconnect:
        active.discard(ws)


if __name__ == "__main__":
    #print(type(verifyAccessKey("aavidcomor", "1b4e9929685af5f7d0ed681e067c85b99063c7bc6a8f3dba97d72b542d65bac46fe839d888c04c4fab78310e35c3d01279b4ac4c799ad4bc6fdf195a6e01a424")))
    uvicorn.run("server:app", host="0.0.0.0", port=8000)