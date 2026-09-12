"""
Graph engine built with NetworkX.

We model services as nodes and "connects to / depends on" as directed edges:

    Payment Service  --->  Auth Service  --->  Database Service

If a service is compromised, blast radius includes:
  1. The compromised service itself
  2. Dependents: services that rely on it (walk edges backwards)
  3. Reachable: services an attacker could pivot to (walk edges forwards)
"""

from typing import Dict, List, Tuple

import networkx as nx
from sqlalchemy.orm import Session

from . import models


# Highest to lowest rank so we can keep the worse severity if a service
# is both a dependent and reachable.
SEVERITY_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1}


def mitigations_for(service_type: str, relationship: str) -> List[str]:
    """Simple beginner-friendly recommendations based on type + how it is affected."""
    kind = (service_type or "api").lower()

    shared = [
        "Isolate the service on the network (restrict inbound/outbound traffic).",
        "Review recent access logs and alerts for unusual activity.",
        "Rotate API keys, tokens, and passwords used by this service.",
    ]

    by_type = {
        "auth": [
            "Force password resets and revoke active sessions.",
            "Enable or tighten multi-factor authentication (MFA).",
            "Audit identity providers and OAuth/SSO client secrets.",
        ],
        "payment": [
            "Pause high-risk transactions until the incident is contained.",
            "Rotate payment gateway credentials and webhook secrets.",
            "Notify the payments/compliance owner and review PCI controls.",
        ],
        "database": [
            "Take a snapshot / backup before making recovery changes.",
            "Revoke extra database users and rotate the main credentials.",
            "Check for unexpected queries, dumps, or new admin accounts.",
        ],
        "cache": [
            "Flush potentially poisoned cache entries.",
            "Rotate cache access credentials.",
        ],
        "api": [
            "Rate-limit and temporarily lock unused endpoints.",
            "Rotate service-to-service credentials.",
        ],
    }

    extra = by_type.get(kind, by_type["api"])

    if relationship == "dependent":
        extra = extra + [
            "Fail closed if this dependency is untrusted (do not silently continue).",
            "Use cached/fallback behavior only if it does not skip security checks.",
        ]
    elif relationship == "reachable":
        extra = extra + [
            "Assume an attacker may already have a path here; treat secrets as leaked.",
            "Segment this service so a neighbor compromise cannot freely pivot inward.",
        ]

    return shared + extra


def severity_for(hops: int, relationship: str) -> str:
    """Map graph distance to a severity label."""
    if relationship == "compromised" or hops == 0:
        return "critical"
    if hops == 1:
        return "high"
    if hops == 2:
        return "medium"
    return "low"


def build_graph(db: Session) -> nx.DiGraph:
    """Build a directed NetworkX graph from the current database."""
    graph = nx.DiGraph()
    services = db.query(models.Service).all()
    edges = db.query(models.ServiceDependency).all()

    for service in services:
        graph.add_node(
            service.id,
            name=service.name,
            service_type=service.service_type,
            description=service.description or "",
        )

    for edge in edges:
        # from_id depends on / connects to to_id
        graph.add_edge(edge.from_id, edge.to_id)

    return graph


def _walk(graph: nx.DiGraph, start: int, reverse: bool) -> Dict[int, int]:
    """
    Breadth-first walk. Returns {node_id: hops_from_start} excluding start.

    reverse=True  -> dependents (who relies on the compromised service)
    reverse=False -> reachable  (where an attacker can pivot)
    """
    if start not in graph:
        return {}

    source = graph.reverse(copy=False) if reverse else graph
    distances = nx.single_source_shortest_path_length(source, start)
    distances.pop(start, None)
    return distances


def simulate_compromise(db: Session, service_id: int) -> Tuple[models.Service, List[dict], str]:
    """
    Calculate blast radius for one compromised service.

    Returns the service row, a list of affected-service dicts, and a summary.
    """
    service = db.query(models.Service).filter(models.Service.id == service_id).first()
    if not service:
        raise ValueError("Service not found")

    graph = build_graph(db)
    dependents = _walk(graph, service_id, reverse=True)

    merged: Dict[int, dict] = {}

    def add_hit(node_id: int, hops: int, relationship: str, reason: str):
        node = graph.nodes[node_id]
        severity = severity_for(hops, relationship)
        existing = merged.get(node_id)
        if existing and SEVERITY_RANK[existing["severity"]] >= SEVERITY_RANK[severity]:
            return
        merged[node_id] = {
            "id": node_id,
            "name": node["name"],
            "service_type": node["service_type"],
            "severity": severity,
            "hops": hops,
            "reason": reason,
            "relationship": relationship,
            "mitigations": mitigations_for(node["service_type"], relationship),
        }

    add_hit(
        service_id,
        0,
        "compromised",
        f"{service.name} is the initially compromised service.",
    )

    for node_id, hops in dependents.items():
        name = graph.nodes[node_id]["name"]
        add_hit(
            node_id,
            hops,
            "dependent",
            f"{name} depends on {service.name} ({hops} hop(s) away) so trust/availability is at risk.",
        )

    affected = sorted(
        merged.values(),
        key=lambda item: (-SEVERITY_RANK[item["severity"]], item["hops"], item["name"]),
    )

    others = [item for item in affected if item["relationship"] != "compromised"]
    summary = (
        f"If {service.name} is compromised, {len(others)} other service(s) are in the blast radius "
        f"({len(dependents)} dependent)."
    )
    return service, affected, summary
