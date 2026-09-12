"use client";

import { AlertTriangle, Server, Database, Lock, CreditCard, Box, Clock } from "lucide-react";

const BADGE = {
  critical: "bg-red-500/20 text-red-400 border-red-500/40",
  high: "bg-orange-500/20 text-orange-400 border-orange-500/40",
  medium: "bg-yellow-500/20 text-yellow-400 border-yellow-500/40",
  low: "bg-sky-500/20 text-sky-400 border-sky-500/40",
};

const RECOVERY_TIME = {
  critical: "4-8 hours",
  high: "1-4 hours",
  medium: "30 mins",
  low: "15 mins"
};

const ICONS = {
  auth: Lock,
  payment: CreditCard,
  database: Database,
  api: Server,
  cache: Box
};

export default function BlastPanel({ simulation }) {
  if (!simulation) {
    return (
      <div className="rounded-2xl border border-dashed border-line bg-panel p-8 text-center text-slate-400">
        Select a service and click <span className="text-cyan-300">Simulate compromise</span> to
        see blast radius, severity, and mitigations.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-red-500/40 bg-red-500/10 p-3 flex items-center justify-center gap-2 animate-in fade-in slide-in-from-top-4">
        <AlertTriangle className="text-red-400" size={20} />
        <span className="font-bold text-red-200">
          ACTIVE SIMULATION — {simulation.affected_count} services at risk
        </span>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {simulation.affected_services.map((item, index) => {
          const ServiceIcon = ICONS[(item.service_type || "").toLowerCase()] || Server;
          const recoveryTime = RECOVERY_TIME[item.severity] || "Unknown";
          
          return (
            <div 
              key={item.id} 
              className="rounded-xl border border-line bg-panel p-5 animate-in fade-in slide-in-from-bottom-4"
            >
              <div className="flex flex-wrap items-start justify-between gap-4 border-b border-line pb-4 mb-4">
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-slate-800 p-2">
                    <ServiceIcon className="text-slate-300" size={24} />
                  </div>
                  <div>
                    <h3 className="font-bold text-white text-lg">{item.name}</h3>
                    <p className="text-sm text-slate-400">{item.reason}</p>
                  </div>
                </div>
                
                <div className="flex flex-col items-end gap-2">
                  <span className={`rounded-full border px-3 py-1 text-xs font-bold uppercase ${BADGE[item.severity]}`}>
                    {item.severity}
                  </span>
                  <div className="flex items-center gap-1 text-xs text-slate-400">
                    <Clock size={12} />
                    Recovery: {recoveryTime}
                  </div>
                </div>
              </div>
              
              <div>
                <h4 className="text-sm font-semibold text-slate-300 mb-3 uppercase tracking-wider">Mitigation Steps</h4>
                <ul className="space-y-2">
                  {item.mitigations.slice(0, 3).map((tip, i) => (
                    <li key={i} className="flex items-start gap-3 text-sm text-slate-300">
                      <input 
                        type="checkbox" 
                        className="mt-1 h-4 w-4 rounded border-slate-600 bg-slate-800 text-cyan-500 focus:ring-cyan-500 focus:ring-offset-slate-900" 
                      />
                      <span className="flex-1">{tip}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
