from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI()
active = set()

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
    # For many concurrent clients, prefer asyncio (this) over threads.
    uvicorn.run("server:app", host="0.0.0.0", port=8000)