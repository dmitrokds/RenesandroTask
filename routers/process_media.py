from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import logging
import traceback

import asyncio




router = APIRouter()


class TextToSpeechScheme(BaseModel):
    text: str
    voice: str


class MediaScheme(BaseModel):
    task_name: str
    video_blocks: dict[str, list[str]]
    audio_blocks: dict[str, list[str]]
    text_to_speech: list[TextToSpeechScheme]




@router.post(
    "/",
    summary="Catch new media"
)
async def catch(
    payload: MediaScheme = Body()
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
                
    import media.video
    
    videos = await media.video.connect(
        list(payload.video_blocks.values())
    )
                
    

    return JSONResponse(
        status_code=200,
        content={
            "status": "SUCCESS",
            "response": "Media queued for proccessing"
        }
    )
    