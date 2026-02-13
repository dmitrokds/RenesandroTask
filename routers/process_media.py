from fastapi import APIRouter, Body, HTTPException, Header, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import redis_config
import config

from jose import jwt, JWTError

import logging
import traceback

import asyncio
import json
import uuid


def require_jwt(auth: str | None = Header(default=None)):
    logging.info(auth)
    token = auth.strip()

    try:
        payload = jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALG])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    return payload

router = APIRouter()

from pydantic import BaseModel, Field

class TextToSpeechScheme(BaseModel):
    text: str = Field(
        ...,
        description="Text that will be converted to speech.",
        examples=["Welcome to Plink — the ultimate platform for gamers."]
    )
    voice: str = Field(
        ...,
        description="Voice name or voice id (depends on your TTS provider).",
        examples=["Sarah"]
    )

class MediaScheme(BaseModel):
    task_name: str = Field(
        ...,
        description="Unique task name for this render job.",
        examples=["test_task_3blocks_with_audio"]
    )
    video_blocks: dict[str, list[str]] = Field(
        ...,
        description="Video blocks: each key is a block name, value is list of .mp4 URLs (order matters).",
        examples=[{
            "intro": [
                "https://cdn.example.com/video/intro_1.mp4",
                "https://cdn.example.com/video/intro_2.mp4"
            ],
            "outro": [
                "https://cdn.example.com/video/outro.mp4"
            ]
        }]
    )
    audio_blocks: dict[str, list[str]] = Field(
        ...,
        description="Audio blocks: each key is a block name, value is list of .mp3 URLs (order matters).",
        examples=[{
            "bgm": [
                "https://cdn.example.com/audio/bgm_1.mp3",
                "https://cdn.example.com/audio/bgm_2.mp3"
            ],
            "sfx": [
                "https://cdn.example.com/audio/click.mp3"
            ]
        }]
    )
    text_to_speech: list[TextToSpeechScheme] = Field(
        ...,
        description="List of TTS segments to generate and mix in order.",
        examples=[[
            {"text": "Welcome to Plink — the ultimate platform for gamers.", "voice": "Sarah"},
            {"text": "Plink makes finding the right teammates effortless.", "voice": "George"}
        ]]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "task_name": "test_task_3blocks_with_audio",
                "video_blocks": {
                    "block_1": [
                        "https://cdn.example.com/video/1.mp4",
                        "https://cdn.example.com/video/2.mp4"
                    ],
                    "block_2": [
                        "https://cdn.example.com/video/3.mp4"
                    ]
                },
                "audio_blocks": {
                    "bg": [
                        "https://cdn.example.com/audio/bg_1.mp3"
                    ]
                },
                "text_to_speech": [
                    {"text": "Welcome to Plink — the ultimate platform for gamers.", "voice": "Sarah"},
                    {"text": "Plink makes finding the right teammates effortless.", "voice": "George"}
                ]
            }
        }



@router.post(
    "/",
    summary="Catch new media"
)
async def catch(
    payload: MediaScheme = Body(),
    jwt_payload: dict = Depends(require_jwt)
):
    if len(payload.video_blocks)==0:
        return JSONResponse(
            status_code=400,
            content={
                "status": "ERROR",
                "response": "video_blocks contains nothing"
            }
        )
        
    
    for name, files in payload.video_blocks.items():
        for file in files:
            if not file.lower().endswith(".mp4"):
                return JSONResponse(
                    status_code=415,
                    content={
                        "status": "ERROR",
                        "response": f"video_blocks['{name}'] supports only .mp4 (got: {file})"
                    }
                )

    if len(payload.audio_blocks) == 0:
        return JSONResponse(
            status_code=400,
            content={
                "status": "ERROR",
                "response": "audio_blocks contains nothing"
            }
        )

    for name, files in payload.audio_blocks.items():
        for file in files:
            if not file.lower().endswith(".mp3"):
                return JSONResponse(
                    status_code=415,
                    content={
                        "status": "ERROR",
                        "response": f"audio_blocks['{name}'] supports only .mp3 (got: {file})"
                    }
                )
                
        
    data = payload.model_dump()
    data["id"] = uuid.uuid4().hex
    await redis_config.r.hset(data["id"], mapping={"status": "queued"})

    await redis_config.r.rpush("queue", json.dumps(data, ensure_ascii=False))
    # redis_config.r.expire(task_id, 3600)
    
    

    return JSONResponse(
        status_code=200,
        content={
            "status": "SUCCESS",
            "response": "Media successfully queued",
            "media_id": data["id"]
        }
    )
    

@router.get(
    "/status/{media_id}",
    summary="Get media status"
)
async def catch(
    media_id: str,
    jwt_payload: dict = Depends(require_jwt)
):
    info = await redis_config.r.hgetall(media_id)
    
    return JSONResponse(
        status_code=200,
        content={
            "status": "SUCCESS",
            "response": info
        }
    )