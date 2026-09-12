"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { ArrowLeft, Bot, CreditCard, CheckCircle, Unlock } from "lucide-react";
import BlastPanel from "./BlastPanel";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function AgenticDemo() {
  const [running, setRunning] = useState(false);
  const [steps, setSteps] = useState([]);
  const [visibleSteps, setVisibleSteps] = useState([]);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [error, setError] = useState("");

  const runAgent = async () => {
    setRunning(true);
    setSteps([]);
    setVisibleSteps([]);
    setAnalysisResult(null);
    setError("");

    try {
      // For demo, just use service_id = 1 (Auth Service usually)
      const res = await fetch(`${API}/x402/demo-agent/1`);
      if (!res.ok) {
        throw new Error("Failed to run demo agent");
      }
      const data = await res.json();
      setSteps(data.steps);
    } catch (err) {
      setError(err.message);
      setRunning(false);
    }
  };

  useEffect(() => {
    if (steps.length === 0) return;

    let currentStep = 0;
    const interval = setInterval(() => {
      if (currentStep < steps.length) {
        setVisibleSteps((prev) => [...prev, steps[currentStep]]);
        
        // If it's the last step, set the analysis result
        if (currentStep === steps.length - 1 && steps[currentStep].result) {
          // The BlastPanel component expects `simulation` format from original API
          setAnalysisResult(steps[currentStep].result);
          setRunning(false);
        }
        currentStep++;
      } else {
        clearInterval(interval);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [steps]);

  const stepConfig = {
    1: { icon: Bot, color: "text-blue-400", bg: "bg-blue-400/10", border: "border-blue-400/20", label: "Payment Required" },
    2: { icon: CreditCard, color: "text-orange-400", bg: "bg-orange-400/10", border: "border-orange-400/20", label: "Payment Submitted" },
    3: { icon: CheckCircle, color: "text-green-400", bg: "bg-green-400/10", border: "border-green-400/20", label: "Payment Verified" },
    4: { icon: Unlock, color: "text-cyan-400", bg: "bg-cyan-400/10", border: "border-cyan-400/20", label: "Analysis Unlocked" },
  };

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <Link href="/" className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-white mb-6">
        <ArrowLeft size={16} />
        Back to Dashboard
      </Link>
      
      <div className="rounded-2xl border border-line bg-panel p-6 shadow-xl">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-white flex items-center gap-2">
              <Bot className="text-blue-400" /> Agentic Payment Demo
            </h1>
            <p className="text-slate-400 mt-1">
              Watch an AI agent seamlessly negotiate and pay for an API request using the x402 protocol.
            </p>
          </div>
          <button
            onClick={runAgent}
            disabled={running}
            className={`rounded-lg px-5 py-2.5 font-medium transition-colors ${
              running
                ? "bg-slate-700 text-slate-400 cursor-not-allowed"
                : "bg-blue-600 text-white hover:bg-blue-500"
            }`}
          >
            {running ? "Agent Running..." : "Run AI Agent"}
          </button>
        </div>

        {error && (
          <div className="mb-6 rounded-xl border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-200">
            {error}
          </div>
        )}

        <div className="space-y-4">
          {visibleSteps.map((step, idx) => {
            const config = stepConfig[step.step];
            const Icon = config.icon;
            return (
              <div
                key={idx}
                className={`flex items-start gap-4 rounded-xl border ${config.border} ${config.bg} p-4 animate-in fade-in slide-in-from-bottom-4`}
              >
                <div className={`mt-1 rounded-full p-2 bg-panel shadow-sm`}>
                  <Icon className={config.color} size={24} />
                </div>
                <div className="flex-1">
                  <h3 className={`font-semibold ${config.color}`}>{config.label}</h3>
                  <p className="text-sm text-slate-300 mt-1">{step.action}</p>
                  
                  {step.step === 1 && step.response && (
                    <pre className="mt-3 overflow-x-auto rounded-lg bg-black/40 p-3 text-xs text-slate-300">
                      {JSON.stringify(step.response, null, 2)}
                    </pre>
                  )}
                  {step.step === 2 && step.token && (
                    <div className="mt-3 rounded-lg bg-black/40 p-3 text-xs font-mono text-orange-200">
                      Token: {step.token}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {analysisResult && (
          <div className="mt-8 pt-8 border-t border-line animate-in fade-in">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Unlock className="text-cyan-400" size={20} /> Analysis Result Received
            </h3>
            <BlastPanel simulation={analysisResult} />
          </div>
        )}
      </div>
    </div>
  );
}
