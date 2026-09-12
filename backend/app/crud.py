"""
CRUD helpers: Create, Read, Update, Delete services and their connections.
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from . import models


def list_services(db: Session) -> List[models.Service]:
    return db.query(models.Service).order_by(models.Service.id).all()


def get_service(db: Session, service_id: int) -> Optional[models.Service]:
    return db.query(models.Service).filter(models.Service.id == service_id).first()


def get_service_by_name(db: Session, name: str) -> Optional[models.Service]:
    return db.query(models.Service).filter(models.Service.name == name).first()


def connects_to_names(db: Session, service: models.Service) -> List[str]:
    names = []
    for edge in service.outgoing:
        target = get_service(db, edge.to_id)
        if target:
            names.append(target.name)
    return names


def set_connections(db: Session, service: models.Service, connects_to: List[str]) -> None:
    """Replace this service's outgoing connections using target service names."""
    db.query(models.ServiceDependency).filter(
        models.ServiceDependency.from_id == service.id
    ).delete()

    for target_name in connects_to:
        target_name = (target_name or "").strip()
        if not target_name:
            continue
        if target_name == service.name:
            # A service cannot depend on itself
            continue
        target = get_service_by_name(db, target_name)
        if not target:
            raise ValueError(f"Unknown service to connect to: {target_name}")
        db.add(models.ServiceDependency(from_id=service.id, to_id=target.id))


def create_service(
    db: Session,
    name: str,
    service_type: str,
    description: str,
    connects_to: List[str],
) -> models.Service:
    if get_service_by_name(db, name):
        raise ValueError(f"A service named '{name}' already exists")

    service = models.Service(
        name=name.strip(),
        service_type=service_type.strip().lower(),
        description=(description or "").strip(),
    )
    db.add(service)
    db.flush()  # get the new id before adding edges
    set_connections(db, service, connects_to)
    db.commit()
    db.refresh(service)
    return service


def update_service(
    db: Session,
    service: models.Service,
    name: Optional[str],
    service_type: Optional[str],
    description: Optional[str],
    connects_to: Optional[List[str]],
) -> models.Service:
    if name is not None:
        other = get_service_by_name(db, name)
        if other and other.id != service.id:
            raise ValueError(f"A service named '{name}' already exists")
        service.name = name.strip()
    if service_type is not None:
        service.service_type = service_type.strip().lower()
    if description is not None:
        service.description = description.strip()
    if connects_to is not None:
        set_connections(db, service, connects_to)
    db.commit()
    db.refresh(service)
    return service


def delete_service(db: Session, service: models.Service) -> None:
    db.delete(service)
    db.commit()
