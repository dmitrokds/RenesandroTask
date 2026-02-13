from fastapi import APIRouter, Body
from pydantic import BaseModel, Field

import logging
import traceback

import config

from datetime import datetime, timedelta, timezone

from jose import jwt


router = APIRouter()

class User(BaseModel):
    user: str = Field(..., examples=["admin", "dima", "manager_01"])
    password: str = Field(..., examples=["StrongPass123!", "P@ssw0rd!"])

@router.post("/token")
async def generate_token(data: User = Body()):

    now = datetime.now(timezone.utc)
    payload = {
        "sub": data.user,
        "scope": data.password,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=config.JWT_EXPIRE_MIN)).timestamp()),
    }

    token = jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALG)
    return {"access_token": token, "token_type": "bearer"}