function Card({ label, value }) {
  return (
    <div className="rounded-xl border border-line bg-panel px-4 py-4">
      <p className="text-xs uppercase tracking-wide text-slate-400">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-white">{value}</p>
    </div>
  );
}

export default function StatsBar({ stats }) {
  return (
    <div className="mt-6 grid grid-cols-2 gap-3 md:grid-cols-4">
      <Card label="Services" value={stats.services} />
      <Card label="Connections" value={stats.connections} />
      <Card label="Service types" value={stats.types} />
      <Card label="Last blast radius" value={stats.affected} />
    </div>
  );
}
