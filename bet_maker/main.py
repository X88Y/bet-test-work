import uuid
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import httpx
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import Column, String, Float, DateTime, Enum
from sqlalchemy.orm import declarative_base, sessionmaker
import enum

DATABASE_URL = "postgresql+asyncpg://user:password@db:5432/betdb"

engine = create_async_engine(DATABASE_URL, echo=True)
Base = declarative_base()
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

app = FastAPI()

class BetStatus(str, enum.Enum):
    PENDING = "ещё не сыграла"
    WON = "выиграла"
    LOST = "проиграла"

class Bet(Base):
    __tablename__ = "bets"

    id = Column(String, primary_key=True)
    event_id = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(Enum(BetStatus), default=BetStatus.PENDING)

class BetCreate(BaseModel):
    event_id: str
    amount: float = Field(..., gt=0)

class BetResponse(BaseModel):
    id: str
    event_id: str
    amount: float
    status: BetStatus

line_provider_url = "http://line-provider:8000"

@app.get("/events")
async def get_events():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{line_provider_url}/events")
    events = response.json()
    available_events = [
        event for event in events
        if datetime.fromisoformat(event['deadline']) > datetime.utcnow()
    ]
    return available_events

@app.post("/bet", response_model=BetResponse)
async def place_bet(bet: BetCreate):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{line_provider_url}/events")
    events = response.json()
    event = next((e for e in events if e['id'] == bet.event_id), None)
    if not event:
        raise HTTPException(status_code=404, detail="Событие не найдено.")
    if datetime.fromisoformat(event['deadline']) < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Дедлайн для ставок на это событие истёк.")

    new_bet = Bet(
        id=str(uuid.uuid4()),
        event_id=bet.event_id,
        amount=bet.amount,
        status=BetStatus.PENDING
    )
    async with async_session() as session:
        session.add(new_bet)
        await session.commit()
    return BetResponse(
        id=new_bet.id,
        event_id=new_bet.event_id,
        amount=new_bet.amount,
        status=new_bet.status
    )

@app.get("/bets", response_model=List[BetResponse])
async def get_bets():
    async with async_session() as session:
        result = await session.execute(
            Bet.__table__.select()
        )
        bets = result.fetchall()
    return [
        BetResponse(
            id=bet.id,
            event_id=bet.event_id,
            amount=bet.amount,
            status=bet.status
        ) for bet in bets
    ]

async def update_bet_statuses():
    while True:
        async with async_session() as session:
            result = await session.execute(
                Bet.__table__.select().where(Bet.status == BetStatus.PENDING)
            )
            pending_bets = result.fetchall()
            if pending_bets:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{line_provider_url}/events")
                events = response.json()
                event_status_map = {e['id']: e['status'] for e in events}
                for bet in pending_bets:
                    event_status = event_status_map.get(bet.event_id)
                    if event_status == "выигрыш первой команды":
                        bet.status = BetStatus.WON
                    elif event_status == "выигрыш второй команды":
                        bet.status = BetStatus.LOST
                    session.add(bet)
                await session.commit()
        await asyncio.sleep(10)

@asynccontextmanager
async def startup_event():
    asyncio.create_task(update_bet_statuses())
