from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import uvicorn
import psycopg2
import secrets
from utils import *
import atexit
import asyncio

app = FastAPI()
active = set()

connection = psycopg2.connect(dbname='EasySaveDB', user='postgres', password='StrongPassword', host='localhost')
cursor = connection.cursor()

atexit.register(lambda: connection.close())


@app.get("/create_user")
async def create_user(username: str, email: str, password: str, test:bool = False):
    env = (envs.test if test else envs.prod)
    uniqueid = generateUniqueId(env, username)
    accessKey = secrets.token_hex(64)

    cursor.execute("""
        INSERT INTO users (username, uniqueid, email, accessKey, password)
        VALUES (%s, %s, %s, %s, %s)
        """, 
        (username, uniqueid, email, accessKey, password))

    connection.commit()

@app.get("/process")
async def process(q: str):
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