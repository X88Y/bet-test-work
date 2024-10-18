from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict
from datetime import datetime
from enum import Enum  # Import Enum
import uuid

app = FastAPI()

class EventStatus(str, Enum):  # Inherit from Enum
    ONGOING = "незавершённое"
    TEAM1_WON = "выигрыш первой команды"
    TEAM2_WON = "выигрыш второй команды"

class Event(BaseModel):
    id: str
    odds: float = Field(..., gt=0)
    deadline: datetime
    status: EventStatus = EventStatus.ONGOING

events: Dict[str, Event] = {}

@app.get("/events")
async def get_events():
    return list(events.values())

@app.post("/events")
async def create_event(event: Event):
    if event.id in events:
        raise HTTPException(status_code=400, detail="Событие с таким ID уже существует.")
    events[event.id] = event
    return event

@app.put("/events/{event_id}/status")
async def update_event_status(event_id: str, status: EventStatus):
    if event_id not in events:
        raise HTTPException(status_code=404, detail="Событие не найдено.")
    events[event_id].status = status
    return events[event_id]
