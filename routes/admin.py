import redis
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import get_db
from src.auth import get_current_user
from src.models import Transaction
import asyncio
from fastapi.responses import StreamingResponse

router = APIRouter()
r = redis.Redis(host='localhost', port=6379, db=0)

active_connections = []

@router.websocket("/ws/admin")
async def websocket_endpoint(websocket: WebSocket, user_id: int = Depends(get_current_user)):
    # Sprawdzenie, czy użytkownik jest administratorem (np. user_id == 1)
    if user_id != 1:
        raise HTTPException(status_code=403, detail="Access forbidden")

    await websocket.accept()
    active_connections.append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Received: {data}")  # Echo testowe
    except WebSocketDisconnect:
        active_connections.remove(websocket)

def broadcast_transaction(transaction: dict):
    """Wysyła transakcję do wszystkich połączonych klientów WebSocket"""
    for connection in active_connections:
        try:
            connection.send_text(json.dumps(transaction))
        except:
            active_connections.remove(connection)

@router.get("/admin/transactions")
def get_transactions(db: Session = Depends(get_db), user_id: int = Depends(get_current_user)):
    """Zwraca listę transakcji dla administratora"""
    if user_id != 1:
        raise HTTPException(status_code=403, detail="Access forbidden")

    transactions = db.query(Transaction).all()
    return transactions
async def event_stream():
    while True:
        yield f"data: Nowa transakcja o wartości 100 PLN\n\n"
        await asyncio.sleep(2)  # Co 2 sekundy wysyła nową wiadomość

@router.get("/sse/logs")
async def sse_logs():
    return StreamingResponse(event_stream(), media_type="text/event-stream")