import { useWebSocketStatus } from "./WebSocketProvider";

export default function Header() {
  const { status } = useWebSocketStatus() || { status: "OFFLINE" };

  const getStatusColor = () => {
    switch (status) {
      case "LIVE": return "bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]";
      case "RECONNECTING": return "bg-orange-500 animate-pulse shadow-[0_0_8px_rgba(249,115,22,0.6)]";
      default: return "bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)]";
    }
  };

  return (
    <header className="flex flex-wrap items-center justify-between gap-4">
      <div>
        <div className="flex items-center gap-3">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-400">
            Cybersecurity SaaS
          </p>
          <div className="flex items-center gap-1.5 rounded-full border border-line bg-panel px-2 py-0.5">
            <span className={`h-2 w-2 rounded-full ${getStatusColor()}`}></span>
            <span className="text-[10px] font-bold text-slate-300 tracking-wider">{status}</span>
          </div>
        </div>
        <h1 className="mt-1 text-3xl font-bold text-white">TrustTrace</h1>
        <p className="mt-1 max-w-2xl text-sm text-slate-400">
          Map how your services connect, then simulate what happens if one of them
          is compromised. TrustTrace calculates the blast radius and suggests
          mitigations.
        </p>
      </div>
      <div className="rounded-xl border border-line bg-panel px-4 py-3 text-right">
        <p className="text-xs text-slate-400">Local demo</p>
        <p className="text-sm font-medium text-cyan-300">No cloud setup needed</p>
      </div>
    </header>
  );
}
