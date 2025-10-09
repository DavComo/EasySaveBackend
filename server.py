from fastapi import FastAPI, WebSocket, HTTPException, Request, Query, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from api_schemas import *
from typing import Annotated
from customExceptions import *
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

dbServiceInstance = dbService.DBService()

@app.middleware("http")
async def verify_request_credentials(request: Request, call_next): # type: ignore
    if request.url.path not in MIDDLEWARE_EXCLUSIONS and request.method != "OPTIONS":
        if 'RequesterUsername' not in request.headers or 'RequesterAccessKey' not in request.headers:
            return JSONResponse(status_code=401, content={"detail": "Authorization credentials required."})
        username = request.headers['RequesterUsername']
        accessKey = request.headers['RequesterAccessKey']
        if not accessKey or not username:
            return JSONResponse(status_code=401, content={"detail": "Authorization credentials required."})
        if not dbServiceInstance.verifyAccessKey(username, accessKey):
                        return JSONResponse(status_code=401, content={"detail": "Authorization credentials invalid."})

    try:
        response = await call_next(request) # type: ignore
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": type(e).__name__ + ": " + str(e)})
    return response # type: ignore



@app.post("/create_user", status_code=status.HTTP_204_NO_CONTENT)
async def create_user( request: Annotated[CreateUserRequest, Query()] ):
    try:
        dbServiceInstance.createUser(request.username, request.email, request.password, request.test)
        return None
    except NonuniqueUsername as e:
        return JSONResponse(status_code=409, content={"detail": str(e)})
    except InvalidEmail as e:
        return JSONResponse(status_code=422, content={"detail": str(e)})


@app.get("/get_user", response_model=GetUserResponse)
async def get_user( request: Annotated[GetUserRequest, Query()] ):

    count = sum([bool(request.username), bool(request.uniqueid), bool(request.email), bool(request.accessKey)])
    if count < 1:
        raise RuntimeError("Must pass in at least ONE search parameter.")

    users = dbServiceInstance.getUsers(request.username, request.uniqueid, request.email, request.accessKey)
    if len(users) == 0:
        return None

    user = users[0].__dict__
    del user["password"]
    del user["accessKey"]
    return user


@app.patch("/update_user", status_code=status.HTTP_204_NO_CONTENT)
async def update_user( request: Request, userRequest: Annotated[UpdateUserRequest, Query()] ):
    username = request.headers["RequesterUsername"]
    uniqueid: str = dbServiceInstance.getUsers(username, None, None, None)[0].getUniqueid()
    try:
        dbServiceInstance.updateUser(uniqueid, json.loads(userRequest.newValuesJSON))
    except KeyError as e:
        raise HTTPException(422, e.args[0])


@app.get("/login", response_model=LoginResponse)
async def login( request: Annotated[LoginRequest, Query()] ):
    print(request.username + ", " + request.password)
    try:
        accessKey: str | None = dbServiceInstance.login(request.username, request.password)
    except RuntimeError as e:
        raise HTTPException(500, e.args[0])
    
    if (accessKey):
        return {"accessKey" : accessKey}
    else:
        raise HTTPException(401, "Invalid login details.")
    

@app.post("/create_block", status_code=status.HTTP_204_NO_CONTENT)
async def create_block( request: Request, userRequest: Annotated[CreateBlockRequest, Query()] ):
    username = request.headers["RequesterUsername"]
    uniqueid: str = dbServiceInstance.getUsers(username, None, None, None)[0].getUniqueid()
    fullIdentifier = uniqueid + "." + userRequest.extendedIdentifier
    
    dbServiceInstance.createBlock(fullIdentifier, userRequest.value)


@app.get("/get_blocks", response_model=GetBlocksResponse)
async def get_blocks( request: Request, userRequest: Annotated[GetBlocksRequest, Query()] ):
    
    username = request.headers["RequesterUsername"]
    uniqueid: str = dbServiceInstance.getUsers(username, None, None, None)[0].getUniqueid()
    fullIdentifier = uniqueid + "." + userRequest.extendedIdentifier

    blocks = dbServiceInstance.getBlocks(fullIdentifier)
    blocksNormalized: list[dict[str, str]] = []
    for block in blocks:
        blocksNormalized.append(block.__dict__)
    return {"blockList" : blocksNormalized}


@app.patch("/update_block", status_code=status.HTTP_204_NO_CONTENT)
async def update_block( request: Request, userRequest: Annotated[UpdateBlockRequest, Query()] ):

    username = request.headers["RequesterUsername"]
    uniqueid: str = dbServiceInstance.getUsers(username, None, None, None)[0].getUniqueid()
    fullIdentifier = uniqueid + "." + userRequest.extendedIdentifier

    dbServiceInstance.updateBlock(fullIdentifier, userRequest.value)


@app.post("/delete_block", status_code=status.HTTP_204_NO_CONTENT)
async def delete_block( request: Request, userRequest: Annotated[DeleteBlockRequest, Query()] ):

    username = request.headers["RequesterUsername"]
    uniqueid: str = dbServiceInstance.getUsers(username, None, None, None)[0].getUniqueid()
    fullIdentifier = uniqueid + "." + userRequest.extendedIdentifier

    dbServiceInstance.deleteBlock(fullIdentifier)
