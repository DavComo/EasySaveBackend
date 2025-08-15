from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import JSONResponse
from typing import Optional
from utils import *
from user import User
import uvicorn
import psycopg2
import secrets
import atexit
import asyncio

app = FastAPI()
active = set()

connection = psycopg2.connect(dbname='EasySaveDB', user='postgres', password='StrongPassword', host='localhost')
cursor = connection.cursor()

atexit.register(lambda: connection.close())


@app.post("/create_user")
async def create_user(username: str, email: str, password: str, test:bool = False):
    env = (envs.test if test else envs.prod)
    user = User(username, email, password, env)

    cursor.execute("""
        INSERT INTO users (username, uniqueid, email, accessKey, password)
        VALUES (%s, %s, %s, %s, %s)
        """, 
        (user.username, user.uniqueid, user.email, user.accessKey, user.password))

    connection.commit()


@app.get("/get_user")
async def get_user(
    username: Optional[str] = Query(None),
    uniqueid: Optional[str] = Query(None),
    email: Optional[str] = Query(None),
    accessKey: Optional[str] = Query(None)
):
    # do async work here (db, http calls, etc.)
    result = q.upper()
    return JSONResponse({"input": q, "result": result})


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
    asyncio.run(create_user("davidcomor", "david.comor@gmail.com", "12345", test=True))
    #uvicorn.run("server:app", host="0.0.0.0", port=8000)