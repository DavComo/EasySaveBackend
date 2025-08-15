from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
from utils import *
from user import User
from dbService import *
import uvicorn
import asyncio
import json

app = FastAPI()
active = set()


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
    return json.dumps(user)


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
    #asyncio.run(get_user(username="davidcomor"))
    uvicorn.run("server:app", host="0.0.0.0", port=8000)