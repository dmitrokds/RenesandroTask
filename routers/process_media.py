from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import config

import logging
import traceback

import asyncio

import time
from pathlib import Path



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
                
    import media.video, media.audio, media.text
    
    videos = await media.video.connect(
        list(payload.video_blocks.values())
    )
    
    videos_with_audio = await media.audio.connect(
        videos, list(payload.audio_blocks.values())
    )
    
    resp = await media.text.connect(
        videos_with_audio, [{"text": block.text, "voice": block.voice}for block in payload.text_to_speech]
    )
    
    Path(f"cache/{payload.task_name}").mkdir(exist_ok=True, parents=True)
    for i, video in enumerate(resp):
        video.write_videofile(
            f"cache/{payload.task_name}/out{i}.mp4",
            preset="ultrafast",
            threads=8,
            fps=config.FPS,
            audio=True
        )
    
    import google_drive
    FOLDER_NAME = f"{payload.task_name}-{time.time()}"
    folder_id = google_drive.create_folder(FOLDER_NAME, config.MAIN_FOLDER_ID)
    for file in list(Path(f"cache/{payload.task_name}/").glob("*.mp4")):
        google_drive.upload_file(str(file.absolute()), folder_id)
    

    return JSONResponse(
        status_code=200,
        content={
            "status": "SUCCESS",
            "response": "Media queued for proccessing"
        }
    )
    