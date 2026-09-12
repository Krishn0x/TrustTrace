"use client";

// Form for adding a service by hand: name, type, and checkboxes for connections.

import { useState } from "react";

const TYPES = ["auth", "payment", "database", "api", "cache", "other"];

export default function ServiceForm({ services, onCreate }) {
  const [name, setName] = useState("");
  const [serviceType, setServiceType] = useState("api");
  const [description, setDescription] = useState("");
  const [connectsTo, setConnectsTo] = useState([]);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  function toggleConnection(serviceName) {
    setConnectsTo((current) =>
      current.includes(serviceName)
        ? current.filter((item) => item !== serviceName)
        : [...current, serviceName]
    );
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    try {
      await onCreate({
        name,
        service_type: serviceType,
        description,
        connects_to: connectsTo,
      });
      setName("");
      setDescription("");
      setConnectsTo([]);
      setServiceType("api");
      setMessage("Service added.");
    } catch (err) {
      setMessage(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-2xl border border-line bg-panel p-5"
    >
      <h2 className="text-lg font-semibold text-white">Add a service</h2>
      <p className="mt-1 text-sm text-slate-400">
        Name it, pick a type, then tick what it connects to.
      </p>

      <label className="mt-4 block text-sm text-slate-300">
        Name
        <input
          required
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Notification Service"
          className="mt-1 w-full rounded-lg border border-line bg-ink px-3 py-2 text-white outline-none focus:border-cyan-400"
        />
      </label>

      <label className="mt-3 block text-sm text-slate-300">
        Type
        <select
          value={serviceType}
          onChange={(e) => setServiceType(e.target.value)}
          className="mt-1 w-full rounded-lg border border-line bg-ink px-3 py-2 text-white outline-none focus:border-cyan-400"
        >
          {TYPES.map((type) => (
            <option key={type} value={type}>
              {type}
            </option>
          ))}
        </select>
      </label>

      <label className="mt-3 block text-sm text-slate-300">
        What it does (optional)
        <input
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Short description"
          className="mt-1 w-full rounded-lg border border-line bg-ink px-3 py-2 text-white outline-none focus:border-cyan-400"
        />
      </label>

      <fieldset className="mt-3">
        <legend className="text-sm text-slate-300">Connects to</legend>
        {services.length === 0 ? (
          <p className="mt-2 text-xs text-slate-500">No other services yet.</p>
        ) : (
          <div className="mt-2 space-y-2">
            {services.map((service) => (
              <label key={service.id} className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={connectsTo.includes(service.name)}
                  onChange={() => toggleConnection(service.name)}
                />
                <span>
                  {service.name}{" "}
                  <span className="text-slate-500">({service.service_type})</span>
                </span>
              </label>
            ))}
          </div>
        )}
      </fieldset>

      <button
        type="submit"
        disabled={busy}
        className="mt-4 w-full rounded-lg bg-cyan-500 px-4 py-2 font-medium text-ink hover:bg-cyan-400 disabled:opacity-60"
      >
        {busy ? "Saving…" : "Add service"}
      </button>
      {message ? <p className="mt-2 text-sm text-slate-300">{message}</p> : null}
    </form>
  );
}
