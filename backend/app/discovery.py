import os
import json
import logging
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import Service, ServiceDependency, GraphSnapshot
from .graph_engine import build_graph

logger = logging.getLogger(__name__)

MOCK_LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mock_logs.txt")

def parse_mock_logs():
    """Parse mock logs to find dependencies."""
    dependencies = []
    if not os.path.exists(MOCK_LOG_FILE):
        return dependencies
    
    with open(MOCK_LOG_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "->" in line:
                parts = line.split("->")
                if len(parts) == 2:
                    from_svc = parts[0].strip()
                    to_svc = parts[1].strip()
                    dependencies.append((from_svc, to_svc))
    return dependencies

def run_discovery():
    """Scan logs, update dependencies, save graph snapshot."""
    logger.info("Running continuous discovery...")
    db: Session = SessionLocal()
    try:
        discovered_deps = parse_mock_logs()
        
        # We only consider services that already exist in the DB for simplicity.
        services = {s.name: s for s in db.query(Service).all()}
        
        # Get existing dependencies
        existing_deps = db.query(ServiceDependency).all()
        existing_dep_names = set()
        for dep in existing_deps:
            from_name = dep.from_service.name
            to_name = dep.to_service.name
            existing_dep_names.add((from_name, to_name))
        
        discovered_dep_names = set()
        for from_name, to_name in discovered_deps:
            if from_name in services and to_name in services:
                discovered_dep_names.add((from_name, to_name))
                
        # Find new dependencies
        new_deps = discovered_dep_names - existing_dep_names
        for from_name, to_name in new_deps:
            logger.info(f"Discovery: New dependency {from_name} -> {to_name}")
            new_dep = ServiceDependency(
                from_id=services[from_name].id,
                to_id=services[to_name].id
            )
            db.add(new_dep)
            
        # Find removed dependencies
        removed_deps = existing_dep_names - discovered_dep_names
        for from_name, to_name in removed_deps:
            logger.info(f"Discovery: Removed dependency {from_name} -> {to_name}")
            dep_to_remove = db.query(ServiceDependency).filter(
                ServiceDependency.from_id == services[from_name].id,
                ServiceDependency.to_id == services[to_name].id
            ).first()
            if dep_to_remove:
                db.delete(dep_to_remove)
                
        if new_deps or removed_deps:
            db.commit()

        # Save snapshot
        graph = build_graph(db)
        nodes_json = json.dumps([
            {"id": node_id, "name": data["name"], "service_type": data["service_type"]}
            for node_id, data in graph.nodes(data=True)
        ])
        edges_json = json.dumps([
            {"from_id": u, "to_id": v}
            for u, v in graph.edges()
        ])
        
        snapshot = GraphSnapshot(nodes_json=nodes_json, edges_json=edges_json)
        db.add(snapshot)
        db.commit()

        return {
            "new_dependencies": list(new_deps),
            "removed_dependencies": list(removed_deps),
            "graph": {
                "nodes": [
                    {"id": node_id, "name": data["name"], "service_type": data["service_type"]}
                    for node_id, data in graph.nodes(data=True)
                ],
                "edges": [
                    {
                        "from_id": from_id, 
                        "to_id": to_id,
                        "from_name": graph.nodes[from_id]["name"],
                        "to_name": graph.nodes[to_id]["name"]
                    }
                    for from_id, to_id in graph.edges()
                ]
            }
        }
    except Exception as e:
        logger.error(f"Discovery error: {e}")
        db.rollback()
        raise e
    finally:
        db.close()

async def run_discovery_task():
    from .websockets import manager
    from .alerts import create_alert
    import asyncio
    import datetime
    
    # Run synchronous DB code in a thread pool to avoid blocking the event loop
    result = await asyncio.to_thread(run_discovery)
    
    # Broadcast new dependencies
    for source, target in result["new_dependencies"]:
        await create_alert(
            type="dependency_added",
            message=f"New connection detected: {source} → {target}",
            severity="orange",
            meta_dict={"source": source, "target": target}
        )
        await manager.broadcast_event("dependency_added", {
            "source": source,
            "target": target
        })
        
    # Broadcast removed dependencies
    for source, target in result["removed_dependencies"]:
        await manager.broadcast_event("dependency_removed", {
            "source": source,
            "target": target
        })
        
    # Broadcast graph updated if there were changes, or maybe always send it to update last_scanned_at
    # The prompt says: Also send graph_updated containing the complete diff and last_scanned_at.
    await manager.broadcast_event("graph_updated", {
        "graph": result["graph"],
        "new_dependencies": result["new_dependencies"],
        "removed_dependencies": result["removed_dependencies"],
        "last_scanned_at": datetime.datetime.utcnow().isoformat() + "Z"
    })
    
    return result
