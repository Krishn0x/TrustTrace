import asyncio
import logging
import random
from .alerts import create_alert
from .database import SessionLocal
from .models import Service

logger = logging.getLogger(__name__)

MOCK_THREATS = [
    {
        "type": "threat_intel",
        "severity": "red",
        "template": "High-volume credential stuffing attack detected against {service_name}.",
        "target_type": "auth",
        "metadata": {"attack_vector": "credential_stuffing"}
    },
    {
        "type": "threat_intel",
        "severity": "orange",
        "template": "Unusual outbound traffic spike originating from {service_name}.",
        "target_type": "database",
        "metadata": {"anomaly": "data_exfiltration_attempt"}
    },
    {
        "type": "threat_intel",
        "severity": "red",
        "template": "Multiple failed API key validations at {service_name} from TOR exit nodes.",
        "target_type": "payment",
        "metadata": {"source": "tor_network"}
    },
    {
        "type": "threat_intel",
        "severity": "orange",
        "template": "Known malicious IP observed probing {service_name} for SSRF vulnerabilities.",
        "target_type": "api",
        "metadata": {"cve": "SSRF_PROBE"}
    }
]

async def run_threat_feed_task():
    db = SessionLocal()
    try:
        # Pick a random threat
        threat = random.choice(MOCK_THREATS)
        
        # Find a suitable service
        services = db.query(Service).filter(Service.service_type == threat["target_type"]).all()
        if not services:
            services = db.query(Service).all()
            
        if not services:
            return
            
        target = random.choice(services)
        message = threat["template"].format(service_name=target.name)
        
        meta = threat["metadata"].copy()
        meta["service_id"] = target.id
        meta["service_name"] = target.name
        meta["is_mock"] = True
        
        await create_alert(
            type=threat["type"],
            message=message,
            severity=threat["severity"],
            meta_dict=meta
        )
        
    except Exception as e:
        logger.error(f"Error in threat feed task: {e}")
    finally:
        db.close()
