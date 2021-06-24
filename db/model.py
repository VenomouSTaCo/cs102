from typing import Optional

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class NoteModel(BaseModel):
    title: str
    text: str


class NoteModelDb(NoteModel):
    id: int


class TokenData(BaseModel):
    username: Optional[str] = None


class UserModel(BaseModel):
    id: int
    username: str


class UserInDB(UserModel):
    password: str
