import logging

import aiohttp

import asyncio

session: None|aiohttp.ClientSession = None
lock = asyncio.Lock()
semaphore = asyncio.Semaphore(50)

async def get_session() -> aiohttp.ClientSession:
    global session
    if session is None or session.closed:
        async with lock:
            if session is None or session.closed:
                session = aiohttp.ClientSession(
                    connector=aiohttp.TCPConnector(
                        limit=100,
                        limit_per_host=20,
                        enable_cleanup_closed=True,
                    )
                )
    return session
    


async def init(url: str, headers: dict, data: dict|None = None):
    MAX_TRIES = 5
    for time in range(MAX_TRIES):
        try:
            session = await get_session()
            async with semaphore:
                async with session.post(url, headers=headers, json=data) as resp:
                    try:
                        response_json = await resp.json()
                    except:
                        response_json = await resp.text()
            break
        except Exception as e:
            if time==MAX_TRIES-1:
                raise e
            await asyncio.sleep(1)


    if resp.status not in [200, 204]:
        logging.warning(f"❌ Error POST ({url}) [{data}]\n{response_json}")
    
    return resp.status, response_json