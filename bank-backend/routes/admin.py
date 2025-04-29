import redis
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.database import get_db
from src.models import Transaction, AtmDevice
from src.auth import admin_required
import asyncio
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, constr
from typing import Optional
from datetime import date

router = APIRouter()
r = redis.Redis(host='localhost', port=6379, db=0)

active_connections = []

@router.websocket("/ws/admin")
async def websocket_endpoint(websocket: WebSocket, current_user=Depends(admin_required)):
    # Sprawdzenie, czy użytkownik jest administratorem (np. user_id == 1)
    if current_user.get("role") != "admin":
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
def get_transactions(db: Session = Depends(get_db), current_user=Depends(admin_required)):
    """Zwraca listę transakcji dla administratora"""

    transactions = db.query(Transaction).all()
    return transactions

@router.get("/admin/atms")
def get_atms(db: Session = Depends(get_db), current_user=Depends(admin_required)):
    """Zwraca listę bankomatów dla administratora"""

    atms = db.query(AtmDevice).all()
    return atms

async def event_stream():
    while True:
        yield f"data: Nowa transakcja o wartości 100 PLN\n\n"
        await asyncio.sleep(2)  # Co 2 sekundy wysyła nową wiadomość

@router.get("/sse/logs")
async def sse_logs():
    return StreamingResponse(event_stream(), media_type="text/event-stream")


# Schemat danych wejściowych
class AtmDeviceCreate(BaseModel):
    localization: str #constr(min_length=1, max_length=20)
    status: str #constr(min_length=1, max_length=10)

@router.post("/admin/add-atm", response_model=dict)
def create_atm(atm: AtmDeviceCreate, db: Session = Depends(get_db), current_user=Depends(admin_required)):
    try:
        new_atm = AtmDevice(
            localization=atm.localization,
            status=atm.status
        )
        db.add(new_atm)
        db.commit()
        db.refresh(new_atm)
        return {"message": "ATM device created", "atm_id": new_atm.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

@router.delete("/admin/delete-atm", response_model=dict)
def delete_atm(atm_id: int, db: Session = Depends(get_db), current_user=Depends(admin_required)):
    atm = db.query(AtmDevice).filter(AtmDevice.id == atm_id).first()

    if not atm:
        raise HTTPException(status_code=404, detail="ATM device not found")

    db.delete(atm)
    db.commit()
    return {"message": f"ATM device with ID {atm_id} deleted"}


@router.get("/admin/transaction-stats")
def get_transaction_stats(
    granularity: str = Query('days', enum=['days', 'hours', 'minutes']),
    status: Optional[str] = Query(None, enum=['pending', 'success', 'rejected']),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db), current_user=Depends(admin_required)
):
    if granularity == 'days':
        group_by = "DATE_TRUNC('day', date)"
    elif granularity == 'hours':
        group_by = "DATE_TRUNC('hour', date)"
    elif granularity == 'minutes':
        group_by = "DATE_TRUNC('minute', date)"
    else:
        return JSONResponse(content={"detail": "Nieprawidłowa granulacja"}, status_code=400)

    query = f"""
        SELECT {group_by} as period, COUNT(*) as count
        FROM transactions
    """

    filters = []
    params = {}

    if status:
        filters.append("status = :status")
        params["status"] = status

    if start_date:
        filters.append("date >= :start_date")
        params["start_date"] = start_date.strftime('%Y-%m-%d')

    if end_date:
        filters.append("date <= :end_date")
        params["end_date"] = end_date.strftime('%Y-%m-%d')

    if filters:
        query += " WHERE " + " AND ".join(filters)

    query += """
        GROUP BY period
        ORDER BY period ASC
    """
    try:
        print(f"Executing query: {query}, with parameters: {params}")
        result = db.execute(text(query), params).fetchall()
        response = [
            {"time": row[0], "count": row[1]}
            for row in result
        ]
        if not result:
            return []
        return response
    except Exception as e:
        print(f"Error executing query: {e}")
        return JSONResponse(content={"detail": "Błąd zapytania do bazy danych"}, status_code=500)