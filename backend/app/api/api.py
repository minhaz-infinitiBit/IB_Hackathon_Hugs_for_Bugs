from fastapi import APIRouter
from app.api.endpoints import upload_pdf, websocket

api_router = APIRouter()
api_router.include_router(upload_pdf.router, prefix="/files", tags=["files"])
api_router.include_router(websocket.router, tags=["websocket"])
