from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, List
from ...core.supabase import get_supabase_client
from ...models.user import UserResponse
from ...models.service_request import ServiceRequestStatus
from ..v1.auth import get_current_user
import json

router = APIRouter()

active_connections: Dict[str, List[WebSocket]] = {}

async def get_service_request(service_request_id: str):
    supabase = get_supabase_client()
    req = supabase.table("service_requests").select("*").eq("id", service_request_id).single().execute()
    return req.data if req.data else None

async def get_service_messages(service_request_id: str):
    supabase = get_supabase_client()
    result = supabase.table("service_messages").select("*").eq("service_request_id", service_request_id).order("created_at").execute()
    return result.data if result.data else []

async def save_message(service_request_id: str, sender_id: str, message: str):
    supabase = get_supabase_client()
    data = {
        "service_request_id": service_request_id,
        "sender_id": sender_id,
        "message": message
    }
    supabase.table("service_messages").insert(data).execute()

@router.websocket("/ws/services/{service_request_id}/chat")
async def websocket_chat(websocket: WebSocket, service_request_id: str, token: str):
    await websocket.accept()
    # Validar usuario por token
    try:
        user = await get_current_user(token)
    except Exception:
        await websocket.send_json({"error": "UNAUTHORIZED"})
        await websocket.close()
        return
    # Validar que el usuario sea parte del service y que el status sea accepted
    req = await get_service_request(service_request_id)
    if not req or req["status"] != ServiceRequestStatus.accepted:
        await websocket.send_json({"error": "CHAT_DISABLED"})
        await websocket.close()
        return
    if user.id not in [req["client_id"], req["worker_id"]]:
        await websocket.send_json({"error": "FORBIDDEN"})
        await websocket.close()
        return
    # Enviar historial
    messages = await get_service_messages(service_request_id)
    await websocket.send_json({"history": messages})
    # Registrar conexión
    if service_request_id not in active_connections:
        active_connections[service_request_id] = []
    active_connections[service_request_id].append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Revalidar status antes de guardar/enviar
            req = await get_service_request(service_request_id)
            if req["status"] != ServiceRequestStatus.accepted:
                await websocket.send_json({"error": "CHAT_DISABLED"})
                await websocket.close()
                break
            # Guardar mensaje
            await save_message(service_request_id, user.id, data)
            msg_obj = {"sender_id": user.id, "message": data}
            # Reenviar a todos los conectados a este chat
            for conn in active_connections[service_request_id]:
                await conn.send_json(msg_obj)
    except WebSocketDisconnect:
        active_connections[service_request_id].remove(websocket)
        if not active_connections[service_request_id]:
            del active_connections[service_request_id] 