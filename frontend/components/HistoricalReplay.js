import { useEffect, useState, useCallback } from "react";
import { Play, Pause, SkipBack, Clock, Activity, X } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function HistoricalReplay({ setSimulation, isReplaying, setIsReplaying }) {
  const [history, setHistory] = useState([]);
  const [activeReplay, setActiveReplay] = useState(null); // The full steps data
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    fetch(`${API}/simulations`)
      .then(res => res.json())
      .then(data => setHistory(data))
      .catch(err => console.error("Failed to load history", err));
  }, [isReplaying]); // Refresh when we exit replay mode

  const loadReplay = async (simId) => {
    try {
      const res = await fetch(`${API}/simulations/${simId}/steps`);
      if (!res.ok) throw new Error("Failed to load replay steps");
      const data = await res.json();
      
      setIsReplaying(true);
      setActiveReplay(data);
      setCurrentStepIndex(0);
      setIsPlaying(false);
      
      // Update global simulation state with step 0 immediately
      updateSimulationState(data, 0);
    } catch (err) {
      console.error(err);
    }
  };

  const updateSimulationState = useCallback((replayData, stepIdx) => {
    if (!replayData || !replayData.steps[stepIdx]) return;
    const step = replayData.steps[stepIdx];
    
    // Simulate what the websocket step payload looked like
    setSimulation({
      simulation_id: replayData.simulation.id,
      compromised_service: step.step_data.compromised_service,
      affected_count: step.step_data.affected_count,
      severity_counts: step.step_data.severity_counts,
      affected_services: step.step_data.accumulated_affected,
      summary: `Risk Score: ${step.step_data.risk_score}`
    });
  }, [setSimulation]);

  const handleSliderChange = (e) => {
    const idx = parseInt(e.target.value, 10);
    setCurrentStepIndex(idx);
    updateSimulationState(activeReplay, idx);
    setIsPlaying(false);
  };

  const exitReplay = () => {
    setIsReplaying(false);
    setActiveReplay(null);
    setSimulation(null);
    setIsPlaying(false);
  };

  // Autoplay functionality
  useEffect(() => {
    let interval;
    if (isPlaying && activeReplay) {
      interval = setInterval(() => {
        setCurrentStepIndex(prev => {
          if (prev >= activeReplay.steps.length - 1) {
            setIsPlaying(false);
            return prev;
          }
          const next = prev + 1;
          updateSimulationState(activeReplay, next);
          return next;
        });
      }, 500);
    }
    return () => clearInterval(interval);
  }, [isPlaying, activeReplay, updateSimulationState]);

  return (
    <div className="rounded-2xl border border-line bg-panel p-5 mt-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
          <Clock className="h-5 w-5 text-cyan-400" />
          Historical Replay
        </h2>
        {isReplaying && (
          <button 
            onClick={exitReplay}
            className="flex items-center gap-1 text-sm bg-red-500/10 text-red-400 border border-red-500/30 px-3 py-1 rounded-full hover:bg-red-500/20 transition-colors"
          >
            <X className="h-4 w-4" /> Exit Replay
          </button>
        )}
      </div>

      {!isReplaying ? (
        <div className="space-y-3">
          {history.length === 0 ? (
            <p className="text-sm text-slate-400">No simulations have been run yet.</p>
          ) : (
            history.map(sim => (
              <div key={sim.id} className="flex items-center justify-between p-3 rounded-xl border border-line bg-ink">
                <div>
                  <p className="text-sm font-medium text-white flex items-center gap-2">
                    <Activity className="h-4 w-4 text-slate-400" />
                    Sim: {sim.id.substring(0, 8)}
                  </p>
                  <p className="text-xs text-slate-500 mt-1">
                    {new Date(sim.started_at).toLocaleString()} • Risk: {sim.final_risk_score || 0}
                  </p>
                </div>
                <button 
                  onClick={() => loadReplay(sim.id)}
                  className="text-xs font-medium text-cyan-300 hover:text-cyan-200 hover:bg-cyan-500/10 px-3 py-1.5 rounded-lg border border-cyan-500/30 transition-colors"
                >
                  Load Replay
                </button>
              </div>
            ))
          )}
        </div>
      ) : (
        <div className="p-4 rounded-xl border border-cyan-500/30 bg-cyan-500/5">
          <div className="flex flex-col gap-4">
            <div className="flex justify-between items-center text-sm text-slate-300">
              <span>Step 1</span>
              <span className="font-medium text-cyan-400">
                Step {currentStepIndex + 1} of {activeReplay?.steps.length}
              </span>
              <span>Step {activeReplay?.steps.length}</span>
            </div>
            
            <input 
              type="range" 
              min="0" 
              max={(activeReplay?.steps.length || 1) - 1} 
              value={currentStepIndex} 
              onChange={handleSliderChange}
              className="w-full accent-cyan-500 h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer"
            />

            <div className="flex justify-center gap-4 mt-2">
              <button 
                onClick={() => {
                  setCurrentStepIndex(0);
                  updateSimulationState(activeReplay, 0);
                  setIsPlaying(false);
                }}
                className="p-2 rounded-full hover:bg-white/10 text-slate-300"
                title="Restart"
              >
                <SkipBack className="h-5 w-5" />
              </button>
              <button 
                onClick={() => setIsPlaying(!isPlaying)}
                className="p-2 rounded-full bg-cyan-500 text-slate-900 hover:bg-cyan-400"
              >
                {isPlaying ? <Pause className="h-5 w-5" /> : <Play className="h-5 w-5 pl-0.5" />}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
