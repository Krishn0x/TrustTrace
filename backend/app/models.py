"""
Database tables.

Service: one row per service the user adds (Payment, Auth, Database, ...).
ServiceDependency: one row per connection. "from_id depends on to_id"
  Example: Payment Service -> Auth Service
"""

from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.orm import relationship
import datetime

from .database import Base


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    # Examples: auth, payment, database, api, cache
    service_type = Column(String, nullable=False, default="api")
    description = Column(String, nullable=True, default="")

    # Connections this service makes TO other services
    outgoing = relationship(
        "ServiceDependency",
        foreign_keys="ServiceDependency.from_id",
        back_populates="from_service",
        cascade="all, delete-orphan",
    )
    # Connections other services make TO this service
    incoming = relationship(
        "ServiceDependency",
        foreign_keys="ServiceDependency.to_id",
        back_populates="to_service",
        cascade="all, delete-orphan",
    )


class ServiceDependency(Base):
    __tablename__ = "service_dependencies"

    id = Column(Integer, primary_key=True, index=True)
    from_id = Column(Integer, ForeignKey("services.id", ondelete="CASCADE"), nullable=False)
    to_id = Column(Integer, ForeignKey("services.id", ondelete="CASCADE"), nullable=False)

    from_service = relationship("Service", foreign_keys=[from_id], back_populates="outgoing")
    to_service = relationship("Service", foreign_keys=[to_id], back_populates="incoming")

    __table_args__ = (
        UniqueConstraint("from_id", "to_id", name="unique_edge"),
    )

class GraphSnapshot(Base):
    __tablename__ = "graph_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    nodes_json = Column(String, nullable=False)
    edges_json = Column(String, nullable=False)

class SimulationRecord(Base):
    __tablename__ = "simulations"

    id = Column(String, primary_key=True, index=True) # UUID
    service_id = Column(Integer, ForeignKey("services.id", ondelete="CASCADE"), nullable=False)
    started_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    status = Column(String, nullable=False, default="running") # running, completed, failed
    final_risk_score = Column(Integer, nullable=True)
    
    steps = relationship("SimulationStep", back_populates="simulation", cascade="all, delete-orphan", order_by="SimulationStep.step_index")

class SimulationStep(Base):
    __tablename__ = "simulation_steps"

    id = Column(Integer, primary_key=True, index=True)
    simulation_id = Column(String, ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False)
    step_index = Column(Integer, nullable=False)
    service_id = Column(Integer, ForeignKey("services.id", ondelete="CASCADE"), nullable=False)
    risk_score = Column(Integer, nullable=False)
    step_data_json = Column(String, nullable=False) # JSON dump of the step payload
    
    simulation = relationship("SimulationRecord", back_populates="steps")

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False) # e.g. "risk_threshold", "dependency_added", "simulation_completed", "threat_intel"
    message = Column(String, nullable=False)
    severity = Column(String, nullable=False) # "red", "orange", "green"
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    metadata_json = Column(String, nullable=True)
