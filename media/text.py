import web.get, web.post

from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip

import logging

import random

import config


async def connect(videos: list[VideoFileClip], textes: list[str]):
    resp = []
    
    
    speech_textes = {}
    
    for video in videos:
        text_index = random.randint(0, len(textes)-1)
        text, voice = textes[text_index]["text"], textes[text_index]["voice"]
        
        speech_text = speech_textes.get(text_index, None)
        if speech_text is None:
            status, voice_id = await web.get.init(
                f"https://api.elevenlabs.io/v2/voices?search={voice}", 
                {"xi-api-key": config.ELEVEN_LABS_APIKEY, "accept": "application/json"},
            )
            if status!=200 or len( voice_id["voices"])==0:
                logging.info(f"Problem with getting id of {voice}; status - {status}")
                continue
            voice_id = voice_id["voices"][0]["voice_id"]
            
            status, speech_path = await web.post.file(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}", 
                "mp3",
                {"xi-api-key": config.ELEVEN_LABS_APIKEY, "accept": "application/json"},
                {
                    "text": text
                }
            )
            if status!=200:
                logging.info(f"Text wasnt successfully proccessed to speech; status - {status}")
                continue
            
            speech_text = AudioFileClip(speech_path)
            
        video = video.with_audio(
            CompositeAudioClip([video.audio.with_volume_scaled(0.2), speech_text])
        )
        resp.append(video)
            
        
    return resp
        
    for i, video in enumerate(resp):
        video.write_videofile(
            f"test/out{i}.mp4",
            preset="ultrafast",
            threads=8,
            fps=config.FPS,
            audio=True
        )