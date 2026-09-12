export default function ServiceList({ services, selectedId, onSimulate, onDelete, isSimulating }) {
  return (
    <div className="rounded-2xl border border-line bg-panel p-5">
      <h2 className="text-lg font-semibold text-white">Your services</h2>
      <p className="mt-1 text-sm text-slate-400">
        Click Simulate to ask: what if this service is compromised?
      </p>

      <ul className="mt-4 space-y-3">
        {services.map((service) => {
          const active = selectedId === service.id;
          return (
            <li
              key={service.id}
              className={`rounded-xl border px-4 py-3 ${
                active ? "border-cyan-400 bg-cyan-400/10" : "border-line bg-ink"
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-medium text-white">{service.name}</p>
                  <p className="text-xs uppercase tracking-wide text-cyan-300">
                    {service.service_type}
                  </p>
                  <p className="mt-1 text-sm text-slate-400">
                    {service.description || "No description"}
                  </p>
                  <p className="mt-1 text-xs text-slate-500">
                    Connects to:{" "}
                    {service.connects_to.length
                      ? service.connects_to.join(", ")
                      : "none"}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => onDelete(service.id)}
                  className="text-xs text-slate-500 hover:text-red-300"
                >
                  Delete
                </button>
              </div>
              <button
                type="button"
                onClick={() => onSimulate(service.id)}
                disabled={isSimulating}
                className={`mt-3 w-full rounded-lg border px-3 py-2 text-sm transition-colors ${
                  isSimulating && active
                    ? "border-orange-500/50 text-orange-400 bg-orange-500/10 animate-pulse"
                    : isSimulating
                    ? "border-slate-700 text-slate-500 cursor-not-allowed"
                    : "border-cyan-500/50 text-cyan-200 hover:bg-cyan-500/10"
                }`}
              >
                {isSimulating && active ? "SIMULATION RUNNING..." : "Simulate compromise"}
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
