"""
FastAPI server for the EasySave Backend API.

This module defines the main FastAPI application with RESTful endpoints for:
- User account management (create, read, update, login)
- Data block management (create, read, update, delete)
- Authentication middleware
- CORS configuration
- Custom OpenAPI schema generation

The API uses access key authentication for protected endpoints and provides
comprehensive error handling and validation.
"""

from fastapi import FastAPI, WebSocket, HTTPException, Request, Query, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from typing import Annotated
from customExceptions import NonuniqueUsername, InvalidEmail
from dbService import DBService
import json
from api_schemas import (
    CreateUserRequest,
    GetUserRequest,
    GetUserResponse,
    UpdateUserRequest,
    LoginRequest,
    LoginResponse,
    CreateBlockRequest,
    GetBlocksRequest,
    GetBlocksResponse,
    UpdateBlockRequest,
    DeleteBlockRequest
)


app = FastAPI(root_path="/api")
active: set[WebSocket] = set()


def custom_openapi():
    """
    Generate custom OpenAPI schema with all request/response models.
    
    This function extends the default FastAPI OpenAPI schema generation
    to include all Pydantic model schemas in the components section.
    This ensures complete API documentation in the /docs endpoint.
    
    Returns:
        dict: The complete OpenAPI schema dictionary.
    """
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

dbServiceInstance = DBService()

@app.middleware("http")
async def verify_request_credentials(request: Request, call_next): # type: ignore
    """
    Authentication middleware for protected endpoints.
    
    This middleware runs before all HTTP requests (except those in
    MIDDLEWARE_EXCLUSIONS). It verifies that protected endpoints receive
    valid RequesterUsername and RequesterAccessKey headers.
    
    Args:
        request (Request): The incoming HTTP request.
        call_next: The next middleware or endpoint handler.
    
    Returns:
        Response: Either an error response or the result from the next handler.
    
    Excluded paths (no auth required):
        - /login
        - /create_user
        - /docs
        - /openapi.json
    """
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
    """
    Create a new user account.
    
    This is a public endpoint (no authentication required). Creates a new user
    with the provided credentials. The password is hashed before storage, and
    a unique access key is generated.
    
    Args:
        request (CreateUserRequest): User creation parameters including:
            - username: Desired username (must be unique)
            - email: Email address (must be valid format)
            - password: Plain-text password (will be hashed)
            - test: Whether this is a test user (default: False)
    
    Returns:
        HTTP 204: No content on success.
        HTTP 409: If username already exists.
        HTTP 422: If email format is invalid.
    
    Example:
        POST /create_user?username=johndoe&email=john@example.com&password=pass123
    """
    try:
        dbServiceInstance.createUser(request.username, request.email, request.password, request.test)
        return None
    except NonuniqueUsername as e:
        return JSONResponse(status_code=409, content={"detail": str(e)})
    except InvalidEmail as e:
        return JSONResponse(status_code=422, content={"detail": str(e)})


@app.get("/get_user", response_model=GetUserResponse)
async def get_user( request: Annotated[GetUserRequest, Query()] ):
    """
    Retrieve user information.
    
    Protected endpoint. At least one search parameter must be provided.
    Returns the first matching user's profile data (excluding password and accessKey).
    
    Args:
        request (GetUserRequest): Search parameters (at least one required):
            - username: Search by username
            - uniqueid: Search by unique ID
            - email: Search by email
            - accessKey: Search by access key
    
    Returns:
        GetUserResponse: User profile data if found.
        None: If no matching user found.
    
    Raises:
        RuntimeError: If no search parameters provided.
    
    Example:
        GET /get_user?username=johndoe
        Headers: RequesterUsername, RequesterAccessKey
    """

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
    """
    Update user profile information.
    
    Protected endpoint. Updates the authenticated user's profile with the
    provided field values. Only email, accessKey, and password can be updated.
    
    Args:
        request (Request): HTTP request containing authentication headers.
        userRequest (UpdateUserRequest): Update parameters:
            - newValuesJSON: JSON string with field:value pairs to update
    
    Returns:
        HTTP 204: No content on success.
        HTTP 422: If invalid field name or email format.
    
    Example:
        PATCH /update_user?newValuesJSON={"email":"new@example.com"}
        Headers: RequesterUsername, RequesterAccessKey
    """
    username = request.headers["RequesterUsername"]
    uniqueid: str = dbServiceInstance.getUsers(username, None, None, None)[0].getUniqueid()
    try:
        dbServiceInstance.updateUser(uniqueid, json.loads(userRequest.newValuesJSON))
    except KeyError as e:
        raise HTTPException(422, e.args[0])


@app.get("/login", response_model=LoginResponse)
async def login( request: Annotated[LoginRequest, Query()] ):
    """
    Authenticate user and receive access key.
    
    Public endpoint. Verifies username and password, returns access key on success.
    The access key should be used in the RequesterAccessKey header for subsequent
    protected endpoint requests.
    
    Args:
        request (LoginRequest): Login credentials:
            - username: The username
            - password: The plain-text password
    
    Returns:
        LoginResponse: Contains the access key for authenticated requests.
    
    Raises:
        HTTPException 401: If credentials are invalid.
        HTTPException 500: If database error occurs.
    
    Example:
        GET /login?username=johndoe&password=pass123
        Response: {"accessKey": "a3f5d2e8..."}
    """
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
    """
    Create a new data block.
    
    Protected endpoint. Creates a new block under the authenticated user's
    namespace. The full identifier is constructed as: {env}.{username}.{extendedIdentifier}
    
    Args:
        request (Request): HTTP request containing authentication headers.
        userRequest (CreateBlockRequest): Block creation parameters:
            - extendedIdentifier: Path after username (e.g., "documents.report1")
            - value: The data content to store
    
    Returns:
        HTTP 204: No content on success.
    
    Example:
        POST /create_block?extendedIdentifier=docs.report1&value=content
        Headers: RequesterUsername, RequesterAccessKey
    """
    username = request.headers["RequesterUsername"]
    uniqueid: str = dbServiceInstance.getUsers(username, None, None, None)[0].getUniqueid()
    fullIdentifier = uniqueid + "." + userRequest.extendedIdentifier
    
    dbServiceInstance.createBlock(fullIdentifier, userRequest.value)


@app.get("/get_blocks", response_model=GetBlocksResponse)
async def get_blocks( request: Request, userRequest: Annotated[GetBlocksRequest, Query()] ):
    """
    Retrieve data blocks matching a path prefix.
    
    Protected endpoint. Returns all blocks under the authenticated user's
    namespace that match the given identifier prefix.
    
    Args:
        request (Request): HTTP request containing authentication headers.
        userRequest (GetBlocksRequest): Query parameters:
            - extendedIdentifier: Path prefix to search (e.g., "documents")
    
    Returns:
        GetBlocksResponse: List of matching blocks with identifier and value.
    
    Example:
        GET /get_blocks?extendedIdentifier=documents
        Headers: RequesterUsername, RequesterAccessKey
        Response: {"blockList": [{"identifier": "...", "value": "..."}]}
    """
    
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
    """
    Update an existing data block's value.
    
    Protected endpoint. Updates the content of a block under the authenticated
    user's namespace.
    
    Args:
        request (Request): HTTP request containing authentication headers.
        userRequest (UpdateBlockRequest): Update parameters:
            - extendedIdentifier: Path to the block
            - value: New content for the block
    
    Returns:
        HTTP 204: No content on success.
    
    Example:
        PATCH /update_block?extendedIdentifier=docs.report1&value=newcontent
        Headers: RequesterUsername, RequesterAccessKey
    """

    username = request.headers["RequesterUsername"]
    uniqueid: str = dbServiceInstance.getUsers(username, None, None, None)[0].getUniqueid()
    fullIdentifier = uniqueid + "." + userRequest.extendedIdentifier

    dbServiceInstance.updateBlock(fullIdentifier, userRequest.value)


@app.post("/delete_block", status_code=status.HTTP_204_NO_CONTENT)
async def delete_block( request: Request, userRequest: Annotated[DeleteBlockRequest, Query()] ):
    """
    Delete a data block.
    
    Protected endpoint. Removes a block from the authenticated user's namespace.
    Note: This only deletes the specific block, not child blocks in the hierarchy.
    
    Args:
        request (Request): HTTP request containing authentication headers.
        userRequest (DeleteBlockRequest): Delete parameters:
            - extendedIdentifier: Path to the block to delete
    
    Returns:
        HTTP 204: No content on success.
    
    Example:
        POST /delete_block?extendedIdentifier=docs.report1
        Headers: RequesterUsername, RequesterAccessKey
    """

    username = request.headers["RequesterUsername"]
    uniqueid: str = dbServiceInstance.getUsers(username, None, None, None)[0].getUniqueid()
    fullIdentifier = uniqueid + "." + userRequest.extendedIdentifier

    dbServiceInstance.deleteBlock(fullIdentifier)
