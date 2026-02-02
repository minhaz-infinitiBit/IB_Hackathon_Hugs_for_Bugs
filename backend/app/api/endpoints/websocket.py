import json
import os
from urllib.parse import urlparse
import redis.asyncio as aioredis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

# Parse Redis URL from environment
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
parsed_redis = urlparse(REDIS_URL)

@router.websocket("/ws/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: int):
    await websocket.accept()
    redis_client = aioredis.Redis(
        host=parsed_redis.hostname or 'localhost',
        port=parsed_redis.port or 6379,
        db=int(parsed_redis.path.lstrip('/') or 0),
        decode_responses=True
    )
    sub = redis_client.pubsub()                          # no await
    await sub.subscribe(f"project:{project_id}:status")  # await here

    try:
        async for message in sub.listen():
            if message["type"] == "message":
                await websocket.send_json(json.loads(message["data"]))
    except WebSocketDisconnect:
        pass
    finally:
        await sub.unsubscribe()
        await redis_client.close()