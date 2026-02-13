import web.get

from moviepy import VideoFileClip, AudioFileClip, concatenate_audioclips, afx


import logging

import random


async def connect(videos: list[VideoFileClip], audio_urls: list[str]):
    resp = []
    
    
    audios = {}
    
    for video in videos:
        audio_index = random.randint(0, len(audio_urls[0])-1)
        audio_url = audio_urls[0][audio_index]
        
        main_audio = audios.get(audio_url, None)
        if main_audio is None:
            status, audio_path = await web.get.file(audio_url, "mp3")
            if status!=200:
                logging.info(f"File {audio_path} wasnt successfully proccessed; status - {status}")
                continue
            
            main_audio = AudioFileClip(audio_path)
            
            
        for audio_group in audio_urls[1:]:
            audio_index = random.randint(0, len(audio_group)-1)
            audio_url = audio_group[audio_index]
            
            audio = audios.get(audio_url, None)
            if audio is None:
                status, audio_path = await web.get.file(audio_url, "mp3")
                if status!=200:
                    logging.info(f"File {audio_path} wasnt successfully proccessed; status - {status}")
                    continue
                
                audio = AudioFileClip(audio_path)
                main_audio = concatenate_audioclips(main_audio, audio)
                
        main_audio = main_audio.with_effects([
            afx.MultiplyVolume(0.2),
            afx.AudioLoop(duration=video.duration),
        ])
            
        video = video.with_audio(
            main_audio
        )
        resp.append(video)
            
        
    return resp
        
    for i, video in enumerate(resp):
        video.write_videofile(
            f"test/out{i}.mp4",
            preset="ultrafast"
        )