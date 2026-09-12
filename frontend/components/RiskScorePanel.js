"use client";

import { useMemo } from "react";

export default function RiskScorePanel({ simulation, totalServices }) {
  const { score, percentage, color } = useMemo(() => {
    if (!simulation) return { score: 0, percentage: 0, color: "text-green-500" };

    let total = 0;
    const { critical = 0, high = 0, medium = 0 } = simulation.severity_counts;
    total += critical * 40;
    total += high * 20;
    total += medium * 10;
    
    if (total > 100) total = 100;

    let col = "text-green-500";
    if (total > 70) col = "text-red-500";
    else if (total >= 40) col = "text-orange-500";

    const perc = totalServices > 0 ? Math.round((simulation.affected_count / totalServices) * 100) : 0;

    return { score: total, percentage: perc, color: col };
  }, [simulation, totalServices]);

  if (!simulation) return null;

  const radius = 40;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  const { critical = 0, high = 0, medium = 0 } = simulation.severity_counts;

  return (
    <div className="rounded-2xl border border-line bg-panel p-5 xl:w-64 flex-shrink-0 animate-in fade-in slide-in-from-right-4">
      <h2 className="text-lg font-semibold text-white mb-4 text-center">Risk Score</h2>
      
      <div className="flex justify-center mb-6">
        <div className="relative w-32 h-32">
          <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
            {/* Background circle */}
            <circle
              cx="50"
              cy="50"
              r={radius}
              className="stroke-slate-700"
              strokeWidth="8"
              fill="none"
            />
            {/* Progress circle */}
            <circle
              cx="50"
              cy="50"
              r={radius}
              className={`${color} transition-all duration-1000 ease-out`}
              strokeWidth="8"
              strokeLinecap="round"
              fill="none"
              stroke="currentColor"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center flex-col">
            <span className="text-3xl font-bold text-white">{score}</span>
            <span className="text-xs text-slate-400">/ 100</span>
          </div>
        </div>
      </div>

      <div className="space-y-2 mb-4">
        <div className="flex justify-between items-center text-sm">
          <span className="flex items-center gap-2 text-slate-300">
            <span className="w-2 h-2 rounded-full bg-red-500"></span> Critical
          </span>
          <span className="font-medium text-white">{critical}</span>
        </div>
        <div className="flex justify-between items-center text-sm">
          <span className="flex items-center gap-2 text-slate-300">
            <span className="w-2 h-2 rounded-full bg-orange-500"></span> High
          </span>
          <span className="font-medium text-white">{high}</span>
        </div>
        <div className="flex justify-between items-center text-sm">
          <span className="flex items-center gap-2 text-slate-300">
            <span className="w-2 h-2 rounded-full bg-yellow-500"></span> Medium
          </span>
          <span className="font-medium text-white">{medium}</span>
        </div>
      </div>

      <div className="text-center text-xs text-slate-400 pt-4 border-t border-line">
        Compromising <span className="font-semibold text-slate-200">{simulation.compromised_service.name}</span> puts {percentage}% of infrastructure at risk
      </div>
    </div>
  );
}
