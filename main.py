import asyncio

import logging
from logging.handlers import RotatingFileHandler
import traceback

from fastapi import FastAPI
import uvicorn
from routers.process_media import router as process_media_router
from routers.auth import router as auth_router

from pathlib import Path

import config

import media_looper


async def safe_run(coro, name):
    while True:
        try:
            logging.info(f"🔁 Starting task: {name}")
            await coro()
        except Exception:
            error = traceback.format_exc()
            logging.error(f"❌ Task '{name}' error; {error}")
            logging.exception(f"❌ Task '{name}' failed; restarting in 2 seconds")
            
            await asyncio.sleep(2)
        else:
            break

async def main():
    app = FastAPI(title="Renesandro Task API")
    app.include_router(process_media_router, prefix="/process_media", tags=["Media proccessing"])
    app.include_router(auth_router, prefix="/auth", tags=["Auth"])
    

    api_config = uvicorn.Config(
        app=app,
        host=config.HOST,
        port=3000,
        log_level="info",
    )

    api_server = uvicorn.Server(api_config)
    
    
    await asyncio.gather(
        safe_run(api_server.serve, "api"),
        safe_run(media_looper.init, "looper")
    )

    
    

if __name__ == "__main__":
    # Create folders
    folders = ["logs"]
    for f in folders:
        Path(f).mkdir(exist_ok=True, parents=True)



    # SETTING LOGS

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    fh = RotatingFileHandler(
        filename="logs/log.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    fh.setLevel(logging.INFO)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    fmt = logging.Formatter(
        "%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    fh.setFormatter(fmt)
    ch.setFormatter(fmt)

    class ExcludeGoogleGenAIModels(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            return all(name not in record.name for name in ["google_genai.models", "httpcore.http11", "oauthlib.oauth1"])
    fh.addFilter(ExcludeGoogleGenAIModels())
    ch.addFilter(ExcludeGoogleGenAIModels())

    root.addHandler(fh)
    root.addHandler(ch)



    # RUN

    asyncio.run(main())