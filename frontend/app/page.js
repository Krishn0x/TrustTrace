"use client";

// This is the main dashboard. It talks to the FastAPI backend and
// passes data into the smaller UI components.

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import BlastPanel from "../components/BlastPanel";
import GraphView from "../components/GraphView";
import Header from "../components/Header";
import ServiceForm from "../components/ServiceForm";
import ServiceList from "../components/ServiceList";
import StatsBar from "../components/StatsBar";
import RiskScorePanel from "../components/RiskScorePanel";
import LiveThreatFeed from "../components/LiveThreatFeed";
import HistoricalReplay from "../components/HistoricalReplay";
import AlertHistory from "../components/AlertHistory";

// Backend address. Change this if you run FastAPI on another port.
const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

import { WebSocketProvider } from "../components/WebSocketProvider";
import { AlertsProvider } from "../components/AlertsProvider";

export default function HomePage() {
  const [services, setServices] = useState([]);
  const [graph, setGraph] = useState({ nodes: [], edges: [] });
  const [simulation, setSimulation] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadAll = useCallback(async () => {
    try {
      setError("");
      const [servicesRes, graphRes] = await Promise.all([
        fetch(`${API}/services`),
        fetch(`${API}/graph`),
      ]);
      if (!servicesRes.ok || !graphRes.ok) {
        throw new Error("Could not load data from the API. Is the backend running?");
      }
      setServices(await servicesRes.json());
      setGraph(await graphRes.json());
    } catch (err) {
      setError(err.message || "Failed to load");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  const [isSimulating, setIsSimulating] = useState(false);
  const [lastWsEvent, setLastWsEvent] = useState(null);
  const [lastScannedAt, setLastScannedAt] = useState(null);
  const [secondsSinceScan, setSecondsSinceScan] = useState(null);
  const [isReplaying, setIsReplaying] = useState(false);
  const [graphDiff, setGraphDiff] = useState({ added: [], removed: [] });

  useEffect(() => {
    if (!lastScannedAt) return;
    const interval = setInterval(() => {
      setSecondsSinceScan(Math.floor((Date.now() - new Date(lastScannedAt).getTime()) / 1000));
    }, 1000);
    return () => clearInterval(interval);
  }, [lastScannedAt]);

  useEffect(() => {
    const handleTrigger = (e) => {
      if (e.detail) {
        // Find the block simulate function in the component scope
        if (!isSimulating && !isReplaying) {
          simulate(e.detail);
        }
      }
    };
    window.addEventListener('trigger-simulation', handleTrigger);
    return () => window.removeEventListener('trigger-simulation', handleTrigger);
  }, [isSimulating, isReplaying]);

  const handleWebSocketMessage = useCallback((event) => {
    setLastWsEvent(event);
    if (event.type === "graph_updated") {
      if (event.data.graph) {
        // Do not update live graph if we are watching a replay!
        if (!isReplaying) {
          setGraph(event.data.graph);
          setGraphDiff({
            added: event.data.new_dependencies || [],
            removed: event.data.removed_dependencies || []
          });
          
          fetch(`${API}/services`)
            .then(res => res.json())
            .then(data => setServices(data))
            .catch(err => console.error(err));
            
          // Clear diff highlight after 3 seconds
          setTimeout(() => setGraphDiff({ added: [], removed: [] }), 3000);
        }
      }
      if (event.data.last_scanned_at) {
        setLastScannedAt(event.data.last_scanned_at);
        setSecondsSinceScan(0);
      }
    } else if (event.type === "simulation_started") {
      setIsSimulating(true);
      if (!isReplaying) setSimulation(null);
    } else if (event.type === "simulation_step") {
      if (!isReplaying) {
        setSimulation(prev => ({
          ...prev,
          simulation_id: event.data.simulation_id,
          compromised_service: event.data.compromised_service,
          affected_count: event.data.affected_count,
          severity_counts: event.data.severity_counts,
          affected_services: event.data.accumulated_affected,
          summary: `Risk Score: ${event.data.risk_score}`
        }));
      }
    } else if (event.type === "simulation_completed") {
      setIsSimulating(false);
      if (!isReplaying) {
        if (event.data.error) {
          setError(event.data.error);
        } else {
          setSimulation(event.data);
        }
      }
    }
  }, [isReplaying]);

  async function createService(payload) {
    const res = await fetch(`${API}/services`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Could not create service");
    }
    await loadAll();
  }

  async function deleteService(id) {
    const res = await fetch(`${API}/services/${id}`, { method: "DELETE" });
    if (!res.ok) {
      throw new Error("Could not delete service");
    }
    if (selectedId === id) {
      setSelectedId(null);
      setSimulation(null);
    }
    await loadAll();
  }

  async function simulate(id) {
    if (isSimulating) return; // Prevent duplicate while running
    setSelectedId(id);
    const res = await fetch(`${API}/simulate/${id}`, { method: "POST" });
    const data = await res.json();
    if (!res.ok) {
      setError(data.detail || "Simulation failed");
      setIsSimulating(false);
      return;
    }
    // State will be updated by WebSocket events
  }

  const stats = useMemo(() => {
    const types = new Set(services.map((s) => s.service_type));
    return {
      services: services.length,
      connections: graph.edges?.length || 0,
      types: types.size,
      affected: simulation ? simulation.affected_count : 0,
    };
  }, [services, graph, simulation]);

  return (
    <WebSocketProvider onMessage={handleWebSocketMessage}>
      <AlertsProvider webSocketEvent={lastWsEvent}>
        <main className="mx-auto max-w-7xl px-4 py-6 relative pb-32">
          <Header />

          <div className="my-4 flex items-center justify-between">
            <div className="text-sm font-medium flex items-center gap-4">
              <span className="text-green-400 bg-green-500/10 px-3 py-1 rounded-full border border-green-500/20">
                AUTO-DISCOVERY ACTIVE
              </span>
              {secondsSinceScan !== null && (
                <span className="text-slate-400">
                  Last scanned: {secondsSinceScan} seconds ago
                </span>
              )}
            </div>
            <Link 
              href="/agentic-demo" 
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500 transition-colors"
            >
              View Agentic Demo
            </Link>
          </div>

          {error ? (
            <div className="mt-4 rounded-xl border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-200">
              {error}
            </div>
          ) : null}

          <StatsBar stats={stats} />

          {loading ? (
            <p className="mt-8 text-slate-400">Loading TrustTrace…</p>
          ) : (
            <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-12">
              <section className="space-y-6 lg:col-span-4">
                <ServiceForm services={services} onCreate={createService} />
                <ServiceList
                  services={services}
                  selectedId={selectedId}
                  onSimulate={simulate}
                  onDelete={deleteService}
                  isSimulating={isSimulating}
                />
                
                <HistoricalReplay 
                  setSimulation={setSimulation} 
                  isReplaying={isReplaying} 
                  setIsReplaying={setIsReplaying} 
                />
                
                <AlertHistory />
              </section>

              <section className="space-y-6 lg:col-span-8">
                <div className="flex flex-col xl:flex-row gap-6">
                  <div className="flex-1 relative">
                    {isReplaying && (
                      <div className="absolute top-4 left-4 z-10 bg-orange-500/90 text-white px-3 py-1 rounded-full text-xs font-bold tracking-wider shadow-lg animate-pulse border border-orange-400">
                        REPLAY MODE
                      </div>
                    )}
                    <GraphView
                      graph={graph}
                      selectedId={selectedId}
                      simulation={simulation}
                      graphDiff={graphDiff}
                      onSelect={isReplaying ? () => {} : simulate}
                    />
                  </div>
                  <RiskScorePanel simulation={simulation} totalServices={services.length} />
                </div>
                
                <BlastPanel simulation={simulation} />
              </section>
            </div>
          )}
          
          <LiveThreatFeed />
        </main>
      </AlertsProvider>
    </WebSocketProvider>
  );
}
