"use client";

import { useState, useEffect } from "react";
import { AlertTriangle, XCircle, CheckCircle, ShieldAlert } from "lucide-react";

const PREDEFINED_EVENTS = [
  { text: "Auth Service: 3 failed login attempts", type: "warning" },
  { text: "Database: Unusual query volume detected", type: "critical" },
  { text: "Payment Service: Health check passed", type: "success" },
  { text: "API Gateway: Rate limit approaching", type: "warning" },
  { text: "Auth Service: Brute force attempt", type: "critical" },
  { text: "Database: Backup completed", type: "success" },
  { text: "Payment: Latency spike detected", type: "warning" },
  { text: "Firewall: Port scan detected from 192.168.x.x", type: "warning" },
  { text: "User Session: Token revocation failed", type: "critical" },
  { text: "Storage: Disk space at 90%", type: "warning" },
  { text: "Cache Service: Eviction rate high", type: "warning" },
  { text: "Load Balancer: Instance healthy", type: "success" },
  { text: "IAM: New admin role created", type: "critical" },
  { text: "DNS: Propagation successful", type: "success" },
  { text: "Microservice A: Timeout communicating with Auth", type: "warning" }
];

import { useAlerts } from "./AlertsProvider";

export default function LiveThreatFeed() {
  const { alerts } = useAlerts() || { alerts: [] };
  
  // Only show threat_intel alerts
  const threatEvents = alerts.filter(a => a.type === "threat_intel").slice(0, 8).reverse();

  const getEventStyle = (severity) => {
    switch (severity) {
      case "red": return "border-red-500/50 bg-red-500/10 text-red-400 shadow-[0_0_10px_rgba(239,68,68,0.2)]";
      case "orange": return "border-orange-500/50 bg-orange-500/10 text-orange-400";
      case "green": return "border-green-500/50 bg-green-500/10 text-green-400";
      default: return "border-slate-500/50 bg-slate-500/10 text-slate-400";
    }
  };

  const getEventIcon = (severity) => {
    switch (severity) {
      case "red": return <XCircle size={14} className="text-red-500 flex-shrink-0" />;
      case "orange": return <AlertTriangle size={14} className="text-orange-500 flex-shrink-0" />;
      case "green": return <CheckCircle size={14} className="text-green-500 flex-shrink-0" />;
      default: return <ShieldAlert size={14} className="text-slate-500 flex-shrink-0" />;
    }
  };

  return (
    <div className="fixed bottom-4 right-4 w-[350px] rounded-xl border border-line bg-[#0a0a0a]/90 backdrop-blur-md p-4 shadow-2xl z-40 overflow-hidden font-mono text-xs flex flex-col h-[380px]">
      <div className="flex items-center justify-between border-b border-line pb-3 mb-3 shrink-0">
        <div className="flex items-center gap-2">
          <div className="h-2 w-2 rounded-full bg-red-500 animate-pulse shadow-[0_0_8px_rgba(239,68,68,0.8)]"></div>
          <h3 className="font-bold tracking-widest text-slate-300">LIVE THREAT FEED (DEMO)</h3>
        </div>
      </div>
      
      <div className="flex-1 overflow-hidden flex flex-col justify-end space-y-2">
        {threatEvents.length === 0 && (
          <div className="text-slate-500 text-center py-4 italic">Waiting for threat signals...</div>
        )}
        {threatEvents.map((evt) => (
          <div 
            key={evt.id} 
            className={`flex flex-col gap-2 rounded border p-2 animate-in fade-in slide-in-from-bottom-2 ${getEventStyle(evt.severity)}`}
          >
            <div className="flex items-start gap-2">
              <div className="mt-0.5">{getEventIcon(evt.severity)}</div>
              <span className="leading-relaxed">{evt.message}</span>
            </div>
            {evt.metadata && evt.metadata.service_id && (
              <div className="ml-5 flex">
                <button 
                  onClick={() => {
                    // Quick way to simulate via an event dispatch or window global
                    // For a hackathon demo, we can just grab the ID and trigger the existing global simulate if we made it accessible,
                    // but the cleanest React way is to dispatch a custom event.
                    window.dispatchEvent(new CustomEvent('trigger-simulation', { detail: evt.metadata.service_id }));
                  }}
                  className="bg-black/40 hover:bg-black/60 border border-current/30 px-3 py-1 rounded transition-colors text-[10px] uppercase font-bold tracking-wider"
                >
                  Run Simulation
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
