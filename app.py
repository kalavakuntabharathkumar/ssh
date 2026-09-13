from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, String, DateTime, select, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

engine = create_engine("sqlite:///incidents.db", connect_args={"check_same_thread": False})

class Base(DeclarativeBase):
    pass

class Incident(Base):
    __tablename__ = "incidents"
    id: Mapped[int] = mapped_column(primary_key=True)
    service: Mapped[str] = mapped_column(String(80), index=True)
    state: Mapped[str] = mapped_column(String(20), index=True)
    severity: Mapped[str] = mapped_column(String(20), index=True)
    message: Mapped[str] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    __table_args__ = (Index("ix_incident_service_created", "service", "created_at"),)

Base.metadata.create_all(engine)
app = FastAPI(title="Software Service Health & Incident Tracker", version="1.0")

class IncidentIn(BaseModel):
    service: str = Field(min_length=2, max_length=80)
    state: str = Field(pattern="^(healthy|degraded|unavailable|recovered)$")
    severity: str = Field(pattern="^(low|medium|high)$")
    message: str = Field(min_length=3, max_length=300)

class IncidentOut(IncidentIn):
    id: int
    created_at: datetime

@app.get("/health")
def health():
    return {"service": "incident-tracker", "status": "healthy"}

@app.post("/incidents", response_model=IncidentOut, status_code=201)
def create_incident(item: IncidentIn):
    with Session(engine) as db:
        row = Incident(**item.model_dump(), created_at=datetime.utcnow())
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

@app.get("/incidents", response_model=list[IncidentOut])
def list_incidents(state: Optional[str] = Query(None, pattern="^(healthy|degraded|unavailable|recovered)$")):
    with Session(engine) as db:
        query = select(Incident).order_by(Incident.created_at.desc())
        if state:
            query = query.where(Incident.state == state)
        return list(db.scalars(query))

@app.get("/incidents/{incident_id}", response_model=IncidentOut)
def get_incident(incident_id: int):
    with Session(engine) as db:
        row = db.get(Incident, incident_id)
        if not row:
            raise HTTPException(404, "Incident not found")
        return row

@app.patch("/incidents/{incident_id}/recover", response_model=IncidentOut)
def recover_incident(incident_id: int):
    with Session(engine) as db:
        row = db.get(Incident, incident_id)
        if not row:
            raise HTTPException(404, "Incident not found")
        if row.state == "recovered":
            raise HTTPException(409, "Incident is already recovered")
        row.state = "recovered"
        row.severity = "low"
        db.commit()
        db.refresh(row)
        return row

@app.get("/services/{service}/summary")
def service_summary(service: str):
    with Session(engine) as db:
        rows = list(db.scalars(select(Incident).where(Incident.service == service)))
        return {"service": service, "checks": len(rows), "open_incidents": sum(r.state in {"degraded", "unavailable"} for r in rows), "latest_state": rows[0].state if rows else "unknown"}
