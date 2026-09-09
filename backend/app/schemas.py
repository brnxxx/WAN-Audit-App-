from datetime import datetime
from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class AdminOut(BaseModel):
    id: int
    username: str
    email: str | None = None
    is_active: bool
    last_login: datetime | None = None

    class Config:
        from_attributes = True