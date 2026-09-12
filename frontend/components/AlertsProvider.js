"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { AlertTriangle, Info, ShieldAlert, X } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const AlertsContext = createContext(null);

export function AlertsProvider({ children, webSocketEvent }) {
  const [alerts, setAlerts] = useState([]);
  const [toasts, setToasts] = useState([]);

  // Load initial alerts from backend
  useEffect(() => {
    fetch(`${API}/alerts`)
      .then(res => res.json())
      .then(data => setAlerts(data))
      .catch(err => console.error("Failed to load alerts", err));
  }, []);

  // Handle new alerts from websocket
  useEffect(() => {
    if (webSocketEvent && webSocketEvent.type === "alert_created") {
      const newAlert = webSocketEvent.data;
      setAlerts(prev => [newAlert, ...prev].slice(0, 50)); // Keep last 50
      
      // Show toast
      const toastId = Date.now().toString();
      setToasts(prev => [...prev, { ...newAlert, toastId }]);
      
      // Auto dismiss toast after 5s
      setTimeout(() => {
        setToasts(prev => prev.filter(t => t.toastId !== toastId));
      }, 5000);
    }
  }, [webSocketEvent]);

  const dismissToast = useCallback((toastId) => {
    setToasts(prev => prev.filter(t => t.toastId !== toastId));
  }, []);

  return (
    <AlertsContext.Provider value={{ alerts }}>
      {children}
      {/* Toast Container - Top Right */}
      <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 w-full max-w-sm">
        {toasts.map(toast => (
          <div 
            key={toast.toastId} 
            className="flex items-start gap-3 rounded-lg border border-line bg-panel p-4 shadow-lg animate-in slide-in-from-right fade-in duration-300"
          >
            {toast.severity === "red" && <ShieldAlert className="h-5 w-5 text-red-500 mt-0.5 shrink-0" />}
            {toast.severity === "orange" && <AlertTriangle className="h-5 w-5 text-orange-500 mt-0.5 shrink-0" />}
            {toast.severity === "green" && <Info className="h-5 w-5 text-green-500 mt-0.5 shrink-0" />}
            
            <div className="flex-1">
              <p className="text-sm font-medium text-white">{toast.message}</p>
              <p className="text-xs text-slate-400 mt-1 capitalize tracking-wide">{toast.type.replace("_", " ")}</p>
            </div>
            
            <button 
              onClick={() => dismissToast(toast.toastId)}
              className="text-slate-500 hover:text-white transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        ))}
      </div>
    </AlertsContext.Provider>
  );
}

export function useAlerts() {
  return useContext(AlertsContext);
}
