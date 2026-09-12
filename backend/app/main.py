"""
TrustTrace API.

Run from the backend folder:
    uvicorn app.main:app --reload --port 8000
"""

import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from . import crud, models, schemas, x402_payment
from .database import Base, SessionLocal, engine, get_db
from .graph_engine import build_graph, simulate_compromise
from .seed import seed_if_empty
from .discovery import run_discovery_task
from .websockets import manager

# Create tables on startup (simple for a beginner local app)
Base.metadata.create_all(bind=engine)

DISCOVERY_INTERVAL_SECONDS = int(os.environ.get("DISCOVERY_INTERVAL_SECONDS", "60"))
scheduler = AsyncIOScheduler()

from .threat_feed import run_threat_feed_task

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once when the API starts: load demo services if the DB is empty
    db = SessionLocal()
    try:
        seed_if_empty(db)
    finally:
        db.close()
        
    scheduler.add_job(run_discovery_task, 'interval', seconds=DISCOVERY_INTERVAL_SECONDS)
    scheduler.add_job(run_threat_feed_task, 'interval', seconds=45) # Every 45s
    scheduler.start()
    
    yield
    
    scheduler.shutdown()


app = FastAPI(
    title="TrustTrace",
    description="Map service dependencies and simulate compromise blast radius.",
    version="1.0.0",
    lifespan=lifespan,
)

import os

# Allow the Next.js frontend (http://localhost:3000) or production URL to call this API
allowed_origins_env = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(x402_payment.router, prefix="/x402")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # We don't expect much from the client, but we must receive to keep connection alive
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        manager.disconnect(websocket)


def to_service_out(db: Session, service: models.Service) -> schemas.ServiceOut:
    return schemas.ServiceOut(
        id=service.id,
        name=service.name,
        service_type=service.service_type,
        description=service.description or "",
        connects_to=crud.connects_to_names(db, service),
    )


@app.get("/")
def health():
    return {"name": "TrustTrace", "status": "ok"}


@app.get("/services", response_model=list[schemas.ServiceOut])
def list_services(db: Session = Depends(get_db)):
    return [to_service_out(db, service) for service in crud.list_services(db)]


@app.post("/discovery/scan")
async def manual_discovery_scan():
    result = await run_discovery_task()
    return {"status": "ok", "result": result}


@app.post("/services", response_model=schemas.ServiceOut)
def create_service(payload: schemas.ServiceCreate, db: Session = Depends(get_db)):
    try:
        service = crud.create_service(
            db=db,
            name=payload.name,
            service_type=payload.service_type,
            description=payload.description or "",
            connects_to=payload.connects_to,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    return to_service_out(db, service)


@app.put("/services/{service_id}", response_model=schemas.ServiceOut)
def update_service(
    service_id: int,
    payload: schemas.ServiceUpdate,
    db: Session = Depends(get_db),
):
    service = crud.get_service(db, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    try:
        service = crud.update_service(
            db=db,
            service=service,
            name=payload.name,
            service_type=payload.service_type,
            description=payload.description,
            connects_to=payload.connects_to,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    return to_service_out(db, service)


@app.delete("/services/{service_id}")
def delete_service(service_id: int, db: Session = Depends(get_db)):
    service = crud.get_service(db, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    crud.delete_service(db, service)
    return {"ok": True}


@app.get("/graph", response_model=schemas.GraphOut)
def get_graph(db: Session = Depends(get_db)):
    graph = build_graph(db)
    nodes = [
        schemas.GraphNode(
            id=node_id,
            name=data["name"],
            service_type=data["service_type"],
        )
        for node_id, data in graph.nodes(data=True)
    ]
    edges = []
    for from_id, to_id in graph.edges():
        edges.append(
            schemas.GraphEdge(
                from_id=from_id,
                to_id=to_id,
                from_name=graph.nodes[from_id]["name"],
                to_name=graph.nodes[to_id]["name"],
            )
        )
    return schemas.GraphOut(nodes=nodes, edges=edges)


from fastapi import BackgroundTasks
import uuid
from .simulation import run_simulation_task

@app.post("/simulate/{service_id}")
async def simulate(service_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Validate service exists
    service = crud.get_service(db, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
        
    simulation_id = str(uuid.uuid4())
    background_tasks.add_task(run_simulation_task, service_id, simulation_id)
    return {"simulation_id": simulation_id, "status": "started"}

import json

@app.get("/alerts")
def get_alerts(db: Session = Depends(get_db)):
    alerts = db.query(models.Alert).order_by(models.Alert.timestamp.desc()).limit(10).all()
    return [
        {
            "id": a.id,
            "type": a.type,
            "message": a.message,
            "severity": a.severity,
            "timestamp": a.timestamp.isoformat() + "Z",
            "metadata": json.loads(a.metadata_json) if a.metadata_json else None
        } for a in alerts
    ]

@app.get("/simulations")
def get_simulations(db: Session = Depends(get_db)):
    sims = db.query(models.SimulationRecord).order_by(models.SimulationRecord.started_at.desc()).limit(5).all()
    return [
        {
            "id": s.id,
            "service_id": s.service_id,
            "started_at": s.started_at.isoformat() + "Z",
            "status": s.status,
            "final_risk_score": s.final_risk_score
        } for s in sims
    ]

@app.get("/simulations/{simulation_id}/steps")
def get_simulation_steps(simulation_id: str, db: Session = Depends(get_db)):
    sim = db.query(models.SimulationRecord).filter(models.SimulationRecord.id == simulation_id).first()
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
        
    steps = db.query(models.SimulationStep).filter(models.SimulationStep.simulation_id == simulation_id).order_by(models.SimulationStep.step_index).all()
    
    return {
        "simulation": {
            "id": sim.id,
            "service_id": sim.service_id,
            "status": sim.status,
            "final_risk_score": sim.final_risk_score
        },
        "steps": [
            {
                "step_index": step.step_index,
                "service_id": step.service_id,
                "risk_score": step.risk_score,
                "step_data": json.loads(step.step_data_json)
            } for step in steps
        ]
    }

