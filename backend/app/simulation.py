import asyncio
import logging
import uuid
from sqlalchemy.orm import Session
from .database import SessionLocal
from .graph_engine import simulate_compromise
from .websockets import manager
from . import schemas
from . import models
from .alerts import create_alert

logger = logging.getLogger(__name__)

async def run_simulation_task(service_id: int, simulation_id: str):
    db = SessionLocal()
    import json
    try:
        service, affected, summary = simulate_compromise(db, service_id)
        total_services = db.query(models.Service).count()
        
        sim_record = models.SimulationRecord(
            id=simulation_id,
            service_id=service_id,
            status="running"
        )
        db.add(sim_record)
        db.commit()
    except Exception as e:
        logger.error(f"Simulation failed to start: {e}")
        db.close()
        return
        
    try:
        await manager.broadcast_event("simulation_started", {
            "simulation_id": simulation_id,
            "service_id": service_id,
            "service_name": service.name,
            "total_services": total_services
        })
        
        current_risk = 0
        threshold_crossed = False
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        
        # Stream each step
        accumulated_affected = []
        
        for index, item in enumerate(affected):
            await asyncio.sleep(0.5)
            
            accumulated_affected.append(item)
            counts[item["severity"]] = counts.get(item["severity"], 0) + 1
            
            # Recalculate risk score
            # CRITICAL service = 40 points, HIGH = 20, MEDIUM = 10
            new_risk = counts.get("critical", 0) * 40 + counts.get("high", 0) * 20 + counts.get("medium", 0) * 10
            if new_risk > 100:
                new_risk = 100
                
            current_risk = new_risk
                
            blast_percentage = round((len(accumulated_affected) / total_services) * 100) if total_services > 0 else 0
            
            step_data = {
                "simulation_id": simulation_id,
                "service_id": item["id"],
                "service_name": item["name"],
                "impact_type": item["relationship"],
                "affected_count": len(accumulated_affected),
                "total_services": total_services,
                "blast_radius_percentage": blast_percentage,
                "risk_score": new_risk,
                "severity": item["severity"],
                "step_index": index,
                "accumulated_affected": accumulated_affected.copy(),
                "severity_counts": counts.copy(),
                "compromised_service": schemas.ServiceOut(
                    id=service.id,
                    name=service.name,
                    service_type=service.service_type,
                    description=service.description or "",
                    connects_to=[] # We don't necessarily need connects_to here for the UI
                ).dict()
            }
            
            # Persist step
            step_record = models.SimulationStep(
                simulation_id=simulation_id,
                step_index=index,
                service_id=item["id"],
                risk_score=new_risk,
                step_data_json=json.dumps(step_data)
            )
            db.add(step_record)
            db.commit()
            
            await manager.broadcast_event("simulation_step", step_data)
            
            if not threshold_crossed and new_risk > 70:
                threshold_crossed = True
                await create_alert(
                    type="risk_threshold",
                    message=f"Simulation {simulation_id[:8]} risk score exceeded 70! Triggered by {item['name']}.",
                    severity="red",
                    meta_dict={"simulation_id": simulation_id, "risk_score": new_risk}
                )
                
        # Final broadcast
        await asyncio.sleep(0.5)
        
        sim_record.status = "completed"
        sim_record.final_risk_score = current_risk
        db.commit()
        
        await create_alert(
            type="simulation_completed",
            message=f"Simulation {simulation_id[:8]} completed. Blast radius: {len(affected)} services.",
            severity="orange" if current_risk > 40 else "green",
            meta_dict={"simulation_id": simulation_id, "risk_score": current_risk}
        )
        
        await manager.broadcast_event("simulation_completed", {
            "simulation_id": simulation_id,
            "compromised_service": schemas.ServiceOut(
                id=service.id,
                name=service.name,
                service_type=service.service_type,
                description=service.description or "",
                connects_to=[]
            ).dict(),
            "affected_count": len(affected),
            "severity_counts": counts,
            "affected_services": affected,
            "summary": summary,
            "final_risk_score": current_risk
        })
        
    except Exception as e:
        logger.error(f"Error streaming simulation: {e}")
        sim_record.status = "failed"
        db.commit()
        # Make sure frontend leaves 'running' state even on error
        await manager.broadcast_event("simulation_completed", {
            "simulation_id": simulation_id,
            "error": "Simulation failed mid-stream"
        })
    finally:
        db.close()
