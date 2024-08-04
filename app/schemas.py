from pydantic import BaseModel, EmailStr, constr
from datetime import datetime

class UserCreate(BaseModel):
    username: constr(min_length=3, max_length=255)
    email: EmailStr
    password: constr(min_length=8)

class UserUpdate(BaseModel):
    username: constr(min_length=3, max_length=255)
    email: EmailStr

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None
