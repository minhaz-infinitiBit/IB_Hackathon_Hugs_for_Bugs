import json
import redis.asyncio as aioredis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

@router.websocket("/ws/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: int):
    await websocket.accept()
    redis_client = aioredis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
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