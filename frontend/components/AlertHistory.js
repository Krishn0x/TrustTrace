import { useAlerts } from "./AlertsProvider";
import { AlertTriangle, Info, ShieldAlert, Clock } from "lucide-react";

export default function AlertHistory() {
  const { alerts } = useAlerts() || { alerts: [] };
  
  if (alerts.length === 0) return null;

  return (
    <div className="rounded-2xl border border-line bg-panel p-5 mt-6">
      <h2 className="text-lg font-semibold text-white flex items-center gap-2 mb-4">
        <Clock className="h-5 w-5 text-cyan-400" />
        Alert History
      </h2>
      <div className="space-y-3">
        {alerts.slice(0, 10).map(alert => (
          <div key={alert.id} className="flex items-start gap-3 p-3 rounded-xl border border-line bg-ink">
            {alert.severity === "red" && <ShieldAlert className="h-5 w-5 text-red-500 mt-0.5 shrink-0" />}
            {alert.severity === "orange" && <AlertTriangle className="h-5 w-5 text-orange-500 mt-0.5 shrink-0" />}
            {alert.severity === "green" && <Info className="h-5 w-5 text-green-500 mt-0.5 shrink-0" />}
            
            <div className="flex-1">
              <p className="text-sm font-medium text-white">{alert.message}</p>
              <div className="flex items-center gap-3 mt-1">
                <span className="text-[10px] text-slate-400 uppercase tracking-wide bg-white/5 px-2 py-0.5 rounded">
                  {alert.type.replace("_", " ")}
                </span>
                <span className="text-xs text-slate-500">
                  {new Date(alert.timestamp).toLocaleString()}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
