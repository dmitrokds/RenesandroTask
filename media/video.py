import web.get

from moviepy import VideoFileClip, concatenate_videoclips

import logging


async def connect(video_urls: list):
    stack_open = []
    stack_result = []
    for video_url in video_urls[0]:
        status, video_path = await web.get.file(video_url, "mp4")
        if status!=200:
            logging.info(f"File {video_url} wasnt successfully proccessed; status - {status}")
            continue
        
        stack_open.append(VideoFileClip(video_path, audio=False))
    
    for block in video_urls[1:]:
        for video_url in block:
            status, video_path = await web.get.file(video_url, "mp4")
            if status!=200:
                logging.info(f"File {video_url} wasnt successfully proccessed; status - {status}")
                continue
            
            video = VideoFileClip(video_path)
            stack_result.extend(
                [
                    concatenate_videoclips([clip1, video], method="compose")
                    for clip1 in stack_open
                ]
            )
            
        stack_open = stack_result.copy()
        stack_result.clear()
        
    return stack_open