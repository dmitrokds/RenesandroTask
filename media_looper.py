import logging
import config
import redis_config

from pathlib import Path

import traceback

import time
import asyncio
import json

async def init():
    while True:
        item = await redis_config.r.blpop("queue", timeout=5)
        if item == None:
            await asyncio.sleep(5)
            continue
        item=json.loads(item[1])
        
        await redis_config.r.hset(item["id"], mapping={"status": "processing"})
        
        try:
            await run(item["id"], item["video_blocks"], item["audio_blocks"], item["text_to_speech"], item["task_name"])
            await redis_config.r.hset(item["id"], mapping={
                "status": "done",
            })
        except Exception as e:
            await redis_config.r.hset(item["id"], mapping={
                "status": "error",
                "error": traceback.format_exc(),
            })

        await asyncio.sleep(5)
            
            
async def run(id: str, video_blocks: list, audio_blocks: list, text_to_speech: list, task_name: str):
    import media.video, media.audio, media.text
    
    start1 = time.time()
    videos = await media.video.connect(
        list(video_blocks.values())
    )
    
    start2 = time.time()
    logging.info(f"ID: {id} - video blocks proccessed; Len - {len(videos)}; Time - {start2-start1}")
    
    videos_with_audio = await media.audio.connect(
        videos, list(audio_blocks.values())
    )
    
    start3 = time.time()
    logging.info(f"ID: {id} - audio blocks proccessed; Len - {len(videos_with_audio)}; Time - {start3-start2}")
    
    resp = await media.text.connect(
        videos_with_audio, text_to_speech
    )
    
    start4 = time.time()
    logging.info(f"ID: {id} - speech blocks proccessed; Len - {len(resp)}; Time - {start4-start3}")
    
    Path(f"cache/{task_name}").mkdir(exist_ok=True, parents=True)
    for i, video in enumerate(resp):
        video.write_videofile(
            f"cache/{task_name}/out{i}.mp4",
            preset="ultrafast",
            threads=8,
            fps=config.FPS,
            audio=True
        )
    
    import google_drive
    FOLDER_NAME = f"{task_name}-{time.time()}"
    folder_id = google_drive.create_folder(FOLDER_NAME, config.MAIN_FOLDER_ID)
    for file in list(Path(f"cache/{task_name}/").glob("*.mp4")):
        google_drive.upload_file(str(file.absolute()), folder_id)
        
    logging.info(f"ID: {id} - res saved; OverallTime - {time.time()-start1}")