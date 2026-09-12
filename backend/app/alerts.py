import json
import logging
from .database import SessionLocal
from .models import Alert
from .websockets import manager
import datetime

logger = logging.getLogger(__name__)

async def create_alert(type: str, message: str, severity: str, meta_dict: dict = None):
    db = SessionLocal()
    try:
        alert = Alert(
            type=type,
            message=message,
            severity=severity,
            metadata_json=json.dumps(meta_dict) if meta_dict else None,
            timestamp=datetime.datetime.utcnow()
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        
        # Broadcast the alert via WebSocket
        await manager.broadcast_event("alert_created", {
            "id": alert.id,
            "type": alert.type,
            "message": alert.message,
            "severity": alert.severity,
            "timestamp": alert.timestamp.isoformat() + "Z",
            "metadata": meta_dict
        })
        return alert
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
    finally:
        db.close()
