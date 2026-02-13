import web.get

from moviepy import VideoFileClip, AudioFileClip

import logging

import random


async def connect(videos: list[VideoFileClip], audio_urls: list[str]):
    audios = {}
    
    for video in videos:
        audio_index = random.randint(0, len(audio_urls)-1)
        audio_url = audio_urls[audio_index]
        
        audio = audios.get(audio_url, None)
        if audio is None:
            status, audio_path = await web.get.file(audio_url, "mp3")
            if status!=200:
                logging.info(f"File {audio_path} wasnt successfully proccessed; status - {status}")
                continue
            
            audio = AudioFileClip(audio_path)
    
        
    for i, video in enumerate(stack_open):
        video.write_videofile(f"test/out{i}.mp4", codec="libx264", audio_codec="aac")