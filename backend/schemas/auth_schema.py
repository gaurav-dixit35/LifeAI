from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    name: str = Field(min_length=2, max_length=80)


class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    remember_me: bool = False


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str
    preview_reset_url: str | None = None


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=12, max_length=256)
    password: str = Field(min_length=6, max_length=128)


class GoogleAuthRequest(BaseModel):
    credential: str = Field(min_length=20)
    remember_me: bool = True


class UserResponse(UserBase):
    id: str
    is_active: bool
    is_admin: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class TokenData(BaseModel):
    sub: str | None = None
