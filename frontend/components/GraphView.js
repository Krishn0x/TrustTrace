"use client";

import { AlertTriangle } from "lucide-react";

// Colors show blast-radius severity after a simulation runs.
function colorFor(node, selectedId, simulation) {
  if (!simulation) {
    return "#3b82f6"; // Default blue
  }
  const hit = simulation.affected_services.find((item) => item.id === node.id);
  if (!hit) return "#22c55e"; // Safe nodes: Green
  if (hit.hops === 0) return "#ef4444"; // Compromised node: Red
  if (hit.hops === 1) return "#f97316"; // Directly affected: Orange
  return "#eab308"; // Indirectly affected: Yellow
}

function layout(nodes) {
  // Place nodes in a circle so arrows stay readable with a handful of services.
  const width = 640;
  const height = 320;
  const cx = width / 2;
  const cy = height / 2;
  const radius = Math.min(width, height) / 2 - 70;
  const count = Math.max(nodes.length, 1);

  return nodes.map((node, index) => {
    const angle = (Math.PI * 2 * index) / count - Math.PI / 2;
    return {
      ...node,
      x: cx + radius * Math.cos(angle),
      y: cy + radius * Math.sin(angle),
    };
  });
}

export default function GraphView({ graph, selectedId, simulation, graphDiff, onSelect }) {
  const positioned = layout(graph.nodes || []);
  const byId = Object.fromEntries(positioned.map((node) => [node.id, node]));

  return (
    <div className="rounded-2xl border border-line bg-panel p-5">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-white">Dependency graph</h2>
          <p className="text-sm text-slate-400">
            Arrows mean “connects to / depends on”. Click a node to simulate.
          </p>
        </div>
      </div>

      <svg viewBox="0 0 640 320" className="mt-4 h-auto w-full overflow-visible">
        <defs>
          <marker
            id="arrow"
            viewBox="0 0 10 10"
            refX="18"
            refY="5"
            markerWidth="6"
            markerHeight="6"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#64748b" />
          </marker>
          <marker
            id="arrow-added"
            viewBox="0 0 10 10"
            refX="18"
            refY="5"
            markerWidth="6"
            markerHeight="6"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#06b6d4" />
          </marker>
        </defs>

        {(graph.edges || []).map((edge) => {
          const from = byId[edge.from_id];
          const to = byId[edge.to_id];
          if (!from || !to) return null;
          
          let edgeColor = "#475569";
          let marker = "url(#arrow)";
          let isAdded = false;
          if (graphDiff && graphDiff.added && graphDiff.added.find(a => a[0] === edge.from_id && a[1] === edge.to_id)) {
            edgeColor = "#06b6d4";
            marker = "url(#arrow-added)";
            isAdded = true;
          }
          
          return (
            <line
              key={`${edge.from_id}-${edge.to_id}`}
              x1={from.x}
              y1={from.y}
              x2={to.x}
              y2={to.y}
              stroke={edgeColor}
              strokeWidth={isAdded ? "3" : "2"}
              markerEnd={marker}
              className={isAdded ? "animate-pulse" : ""}
            />
          );
        })}
        
        {graphDiff && graphDiff.removed && graphDiff.removed.map((edgeArr) => {
          const from = byId[edgeArr[0]];
          const to = byId[edgeArr[1]];
          if (!from || !to) return null;
          return (
            <line
              key={`removed-${edgeArr[0]}-${edgeArr[1]}`}
              x1={from.x}
              y1={from.y}
              x2={to.x}
              y2={to.y}
              stroke="#ef4444"
              strokeWidth="2"
              strokeDasharray="4"
              className="animate-pulse"
            />
          );
        })}

        {positioned.map((node) => {
          const isCompromised = simulation && simulation.affected_services.find(h => h.id === node.id && h.hops === 0);
          const color = colorFor(node, selectedId, simulation);
          
          let isLatest = simulation && simulation.affected_services.length > 0 && 
                           simulation.affected_services[simulation.affected_services.length - 1].id === node.id;
                           
          if (graphDiff && graphDiff.added && graphDiff.added.find(a => a[0] === node.id || a[1] === node.id)) {
            isLatest = true;
          }

          return (
            <g
              key={node.id}
              onClick={() => onSelect(node.id)}
              className="cursor-pointer"
            >
              {isLatest && (
                <circle
                  cx={node.x}
                  cy={node.y}
                  r="28"
                  fill="none"
                  stroke={color}
                  strokeWidth="2"
                  className="animate-ping opacity-75"
                />
              )}
              <circle
                cx={node.x}
                cy={node.y}
                r="22"
                fill={color}
                style={{ transition: "fill 0.5s ease" }}
              />
              {isCompromised ? (
                <g transform={`translate(${node.x - 10}, ${node.y - 10})`}>
                  <AlertTriangle width={20} height={20} color="white" />
                </g>
              ) : null}
              <text
                x={node.x}
                y={node.y + 40}
                textAnchor="middle"
                fill="#e2e8f0"
                fontSize="12"
              >
                {node.name}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
