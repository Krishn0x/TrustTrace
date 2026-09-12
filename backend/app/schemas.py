"""
Pydantic schemas: the JSON shapes the API sends and receives.

Keeping these separate from database models makes the API easier to read.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class ServiceCreate(BaseModel):
    name: str = Field(..., min_length=1, examples=["Payment Service"])
    service_type: str = Field(..., min_length=1, examples=["payment"])
    description: Optional[str] = ""
    # Names of services this one connects to / depends on
    connects_to: List[str] = Field(default_factory=list, examples=[["Auth Service"]])


class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    service_type: Optional[str] = None
    description: Optional[str] = None
    connects_to: Optional[List[str]] = None


class ServiceOut(BaseModel):
    id: int
    name: str
    service_type: str
    description: Optional[str] = ""
    connects_to: List[str] = []

    class Config:
        from_attributes = True


class GraphNode(BaseModel):
    id: int
    name: str
    service_type: str


class GraphEdge(BaseModel):
    from_id: int
    to_id: int
    from_name: str
    to_name: str


class GraphOut(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]


class AffectedService(BaseModel):
    id: int
    name: str
    service_type: str
    severity: str  # critical | high | medium | low
    hops: int
    reason: str
    relationship: str  # compromised | dependent | reachable
    mitigations: List[str]


class SimulationResult(BaseModel):
    compromised_service: ServiceOut
    affected_count: int
    severity_counts: dict
    affected_services: List[AffectedService]
    summary: str
