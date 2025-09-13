from pydantic import BaseModel, Field
from typing import Optional
import utils

class CreateUserRequest(BaseModel):
    username: str = Field(title="Username", description="Required username of new user", examples=["johndoe"])
    email: str = Field(title="Email", description="Required email of new user", examples=["johndoe@email.com"])
    password: str = Field(title="Password", description="Required password of new user", examples=["notmybirthday123!"])
    test : bool = Field(title="isTestUser", description="Optional boolean whether user is meant for testing", examples=[True, False], default=False)

class GetUserRequest(BaseModel):
    username: Optional[str] = Field(title="Username", description="Optional username search param", examples=["johndoe"], default=None)
    uniqueid: Optional[str] = Field(title="UniqueID", description="Optional uniqueid search param", examples=["prod.johndoe"], default=None)
    email: Optional[str] = Field(title="Email", description="Optional email search param", examples=["johndoe@email.com"], default=None)
    accessKey: Optional[str] = Field(title="AccessKey", description="Optional accessKey search param", default=None)

class GetUserResponse(BaseModel):
    env: utils.envs = Field(title="User environment", description="The environment the user is on", examples=["prod"])
    username: str = Field(title="Username", description="Username of user", examples=["johndoe"])
    uniqueid: str = Field(title="UniqueID", description="Full uniqueid of user", examples=["prod.johndoe"])
    email: str = Field(title="Email", description="Users email", examples=["johndoe@email.com"])

class UpdateUserRequest(BaseModel):
    newValuesJSON: str = Field(title="NewValuesJSON", description="JSON model of new values to be updated in an identifier:value pair", examples=["{\"identifier\":\"value\"}"])

class LoginRequest(BaseModel):
    username: str = Field(title="Username", description="Username of user", examples=["johndoe"])
    password: str = Field(title="Password", description="Password of user", examples=["notmybirthday123!"])

class LoginResponse(BaseModel):
    accessKey: str = Field(title="AccessKey", description="User accessKey")

class CreateBlockRequest(BaseModel):
    extendedIdentifier: str = Field(title="ExtendedIdentifier", description="The extended identifier of the block to be added, excluding username and environment", examples=["identifier1"])
    value: str = Field(title="Value", description="The value of the new block; can be empty", examples=["value1"])

class GetBlocksRequest(BaseModel):
    extendedIdentifier: str = Field(title="ExtendedIdentifier", description="The extended identifier of blocks param, excluding username and environment", examples=["identifiers"])

class GetBlocksResponse(BaseModel):
    blockList: list[dict[str, str]] = Field(title="BlockList", description="A list of blocks in identifier:value pairs", examples=[[{"identifier":"value"}]])

class UpdateBlockRequest(BaseModel):
    extendedIdentifier: str = Field(title="ExtendedIdentifier", description="The extended identifier of the block to be updated, excluding username and environment", examples=["identifiers"])
    value: str = Field(title="Value", description="The value to update the block to", examples=["value1"])

class DeleteBlockRequest(BaseModel):
    extendedIdentifier: str = Field(title="ExtendedIdentifier", description="The extended identifier of the block to be deleted, excluding username and environment", examples=["identifiers"])