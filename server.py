from fastapi import FastAPI, WebSocket, HTTPException, Request, Query, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from api_schemas import *
from typing import Annotated
import dbService
import json


app = FastAPI(root_path="/api")
active: set[WebSocket] = set()


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(title="EasySave API", version="0.1.0", routes=app.routes)
    schema["components"]["schemas"]["CreateUserRequest"] = CreateUserRequest.model_json_schema()
    schema["components"]["schemas"]["GetUserRequest"] = GetUserRequest.model_json_schema()
    schema["components"]["schemas"]["GetUserResponse"] = GetUserResponse.model_json_schema()
    schema["components"]["schemas"]["UpdateUserRequest"] = UpdateUserRequest.model_json_schema()
    schema["components"]["schemas"]["LoginRequest"] = LoginRequest.model_json_schema()
    schema["components"]["schemas"]["LoginResponse"] = LoginResponse.model_json_schema()
    schema["components"]["schemas"]["CreateBlockRequest"] = CreateBlockRequest.model_json_schema()
    schema["components"]["schemas"]["GetBlocksRequest"] = GetBlocksRequest.model_json_schema()
    schema["components"]["schemas"]["GetBlocksResponse"] = GetBlocksResponse.model_json_schema()
    schema["components"]["schemas"]["UpdateBlockRequest"] = UpdateBlockRequest.model_json_schema()
    schema["components"]["schemas"]["DeleteBlockRequest"] = DeleteBlockRequest.model_json_schema()
    app.openapi_schema = schema
    return app.openapi_schema

app.openapi = custom_openapi


MIDDLEWARE_EXCLUSIONS = ['/login', '/create_user', '/docs', '/openapi.json']

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
        return JSONResponse(status_code=500, content={"detail": type(e).__name__ + ": " + str(e)})
    return response # type: ignore



@app.post("/create_user", status_code=status.HTTP_204_NO_CONTENT)
async def create_user( request: Annotated[CreateUserRequest, Query()] ) -> None:
    dbService.createUser(request.username, request.email, request.password, request.test)
    return None


@app.get("/get_user", response_model=GetUserResponse)
async def get_user( request: Annotated[GetUserRequest, Query()] ):

    count = sum([bool(request.username), bool(request.uniqueid), bool(request.email), bool(request.accessKey)])
    if count < 1:
        raise RuntimeError("Must pass in at least ONE search parameter.")

    users = dbService.getUsers(request.username, request.uniqueid, request.email, request.accessKey)
    if len(users) == 0:
        return None

    user = users[0].__dict__
    del user["password"]
    del user["accessKey"]
    return user


@app.patch("/update_user", status_code=status.HTTP_204_NO_CONTENT)
async def update_user( request: Request, userRequest: Annotated[UpdateUserRequest, Query()] ):
    username = request.headers["RequesterUsername"]
    uniqueid: str = dbService.getUsers(username, None, None, None)[0].getUniqueid()
    try:
        dbService.updateUser(uniqueid, json.loads(userRequest.newValuesJSON))
    except KeyError as e:
        raise HTTPException(422, e.args[0])


@app.get("/login", response_model=LoginResponse)
async def login( request: Annotated[LoginRequest, Query()] ):
    print(request.username + ", " + request.password)
    try:
        accessKey: str | None = dbService.login(request.username, request.password)
    except RuntimeError as e:
        raise HTTPException(500, e.args[0])
    
    if (accessKey):
        return {"accessKey" : accessKey}
    else:
        raise HTTPException(401, "Invalid login details.")
    

@app.post("/create_block", status_code=status.HTTP_204_NO_CONTENT)
async def create_block( request: Request, userRequest: Annotated[CreateBlockRequest, Query()] ):
    username = request.headers["RequesterUsername"]
    uniqueid: str = dbService.getUsers(username, None, None, None)[0].getUniqueid()
    fullIdentifier = uniqueid + "." + userRequest.extendedIdentifier
    
    dbService.createBlock(fullIdentifier, userRequest.value)


@app.get("/get_blocks", response_model=GetBlocksResponse)
async def get_blocks( request: Request, userRequest: Annotated[GetBlocksRequest, Query()] ):
    
    username = request.headers["RequesterUsername"]
    uniqueid: str = dbService.getUsers(username, None, None, None)[0].getUniqueid()
    fullIdentifier = uniqueid + "." + userRequest.extendedIdentifier

    blocks = dbService.getBlocks(fullIdentifier)
    blocksNormalized: list[dict[str, str]] = []
    for block in blocks:
        blocksNormalized.append(block.__dict__)
    return {"blockList" : blocksNormalized}


@app.patch("/update_block", status_code=status.HTTP_204_NO_CONTENT)
async def update_block( request: Request, userRequest: Annotated[UpdateBlockRequest, Query()] ):

    username = request.headers["RequesterUsername"]
    uniqueid: str = dbService.getUsers(username, None, None, None)[0].getUniqueid()
    fullIdentifier = uniqueid + "." + userRequest.extendedIdentifier

    dbService.updateBlock(fullIdentifier, userRequest.value)


@app.post("/delete_block", status_code=status.HTTP_204_NO_CONTENT)
async def delete_block( request: Request, userRequest: Annotated[DeleteBlockRequest, Query()] ):

    username = request.headers["RequesterUsername"]
    uniqueid: str = dbService.getUsers(username, None, None, None)[0].getUniqueid()
    fullIdentifier = uniqueid + "." + userRequest.extendedIdentifier

    dbService.deleteBlock(fullIdentifier)


#if __name__ == "__main__":
    #print(type(verifyAccessKey("aavidcomor", "1b4e9929685af5f7d0ed681e067c85b99063c7bc6a8f3dba97d72b542d65bac46fe839d888c04c4fab78310e35c3d01279b4ac4c799ad4bc6fdf195a6e01a424")))
    #uvicorn.run("server:app", host="0.0.0.0", port=8000)
