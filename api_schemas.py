"""
Pydantic models for API request and response validation.

This module defines all the request and response schemas used by the FastAPI
endpoints. These models provide automatic validation, serialization, and
documentation for the API.
"""

from pydantic import BaseModel, Field
from typing import Optional
import utils


class CreateUserRequest(BaseModel):
    """
    Request model for creating a new user account.
    
    Attributes:
        username (str): The desired username (must be unique).
        email (str): The user's email address (must be valid format).
        password (str): The user's password (will be hashed before storage).
        test (bool): Whether this is a test user. Defaults to False.
    """
    username: str = Field(title="Username", description="Required username of new user", examples=["johndoe"])
    email: str = Field(title="Email", description="Required email of new user", examples=["johndoe@email.com"])
    password: str = Field(title="Password", description="Required password of new user", examples=["notmybirthday123!"])
    test : bool = Field(title="isTestUser", description="Optional boolean whether user is meant for testing", examples=[True, False], default=False)


class GetUserRequest(BaseModel):
    """
    Request model for retrieving user information.
    
    At least one search parameter must be provided. The first matching user
    will be returned.
    
    Attributes:
        username (Optional[str]): Search by username.
        uniqueid (Optional[str]): Search by unique ID.
        email (Optional[str]): Search by email address.
        accessKey (Optional[str]): Search by access key.
    """
    username: Optional[str] = Field(title="Username", description="Optional username search param", examples=["johndoe"], default=None)
    uniqueid: Optional[str] = Field(title="UniqueID", description="Optional uniqueid search param", examples=["prod.johndoe"], default=None)
    email: Optional[str] = Field(title="Email", description="Optional email search param", examples=["johndoe@email.com"], default=None)
    accessKey: Optional[str] = Field(title="AccessKey", description="Optional accessKey search param", default=None)


class GetUserResponse(BaseModel):
    """
    Response model for user information.
    
    Returns user profile data excluding sensitive information (password and accessKey).
    
    Attributes:
        env (utils.envs): The user's environment (prod or test).
        username (str): The username.
        uniqueid (str): The full hierarchical unique identifier.
        email (str): The user's email address.
    """
    env: utils.envs = Field(title="User environment", description="The environment the user is on", examples=["prod"])
    username: str = Field(title="Username", description="Username of user", examples=["johndoe"])
    uniqueid: str = Field(title="UniqueID", description="Full uniqueid of user", examples=["prod.johndoe"])
    email: str = Field(title="Email", description="Users email", examples=["johndoe@email.com"])


class UpdateUserRequest(BaseModel):
    """
    Request model for updating user information.
    
    Attributes:
        newValuesJSON (str): JSON string containing field-value pairs to update.
            Allowed fields: email, accessKey, password.
    """
    newValuesJSON: str = Field(title="NewValuesJSON", description="JSON model of new values to be updated in an identifier:value pair", examples=["{\"identifier\":\"value\"}"])


class LoginRequest(BaseModel):
    """
    Request model for user authentication.
    
    Attributes:
        username (str): The username to authenticate.
        password (str): The password to verify.
    """
    username: str = Field(title="Username", description="Username of user", examples=["johndoe"])
    password: str = Field(title="Password", description="Password of user", examples=["notmybirthday123!"])


class LoginResponse(BaseModel):
    """
    Response model for successful authentication.
    
    Attributes:
        accessKey (str): The 128-character access key for future API requests.
    """
    accessKey: str = Field(title="AccessKey", description="User accessKey")


class CreateBlockRequest(BaseModel):
    """
    Request model for creating a new data block.
    
    The full identifier will be constructed as: {env}.{username}.{extendedIdentifier}
    
    Attributes:
        extendedIdentifier (str): The path after username (e.g., "documents.report1").
        value (str): The data content to store (can be empty string).
    """
    extendedIdentifier: str = Field(title="ExtendedIdentifier", description="The extended identifier of the block to be added, excluding username and environment", examples=["identifier1"])
    value: str = Field(title="Value", description="The value of the new block; can be empty", examples=["value1"])


class GetBlocksRequest(BaseModel):
    """
    Request model for retrieving data blocks.
    
    Retrieves all blocks matching the identifier prefix pattern.
    
    Attributes:
        extendedIdentifier (str): The path prefix to search for (e.g., "documents"
            will match "documents.report1", "documents.report2", etc.).
    """
    extendedIdentifier: str = Field(title="ExtendedIdentifier", description="The extended identifier of blocks param, excluding username and environment", examples=["identifiers"])


class GetBlocksResponse(BaseModel):
    """
    Response model for block retrieval.
    
    Attributes:
        blockList (list[dict[str, str]]): List of blocks, each containing
            identifier and value fields.
    """
    blockList: list[dict[str, str]] = Field(title="BlockList", description="A list of blocks in identifier:value pairs", examples=[[{"identifier":"value"}]])


class UpdateBlockRequest(BaseModel):
    """
    Request model for updating an existing block's value.
    
    Attributes:
        extendedIdentifier (str): The path to the block to update.
        value (str): The new data content.
    """
    extendedIdentifier: str = Field(title="ExtendedIdentifier", description="The extended identifier of the block to be updated, excluding username and environment", examples=["identifiers"])
    value: str = Field(title="Value", description="The value to update the block to", examples=["value1"])


class DeleteBlockRequest(BaseModel):
    """
    Request model for deleting a data block.
    
    Attributes:
        extendedIdentifier (str): The path to the block to delete.
    """
    extendedIdentifier: str = Field(title="ExtendedIdentifier", description="The extended identifier of the block to be deleted, excluding username and environment", examples=["identifiers"])