"use client";

import React, { createContext, useContext, useEffect, useState, useRef } from "react";

const WebSocketContext = createContext(null);

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws";

export function WebSocketProvider({ children, onMessage }) {
  const [status, setStatus] = useState("OFFLINE");
  const ws = useRef(null);

  useEffect(() => {
    let reconnectTimeout = null;

    const connect = () => {
      setStatus("RECONNECTING");
      ws.current = new WebSocket(WS_URL);

      ws.current.onopen = () => {
        setStatus("LIVE");
      };

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (onMessage) {
            onMessage(data);
          }
        } catch (e) {
          console.error("Failed to parse WS message", e);
        }
      };

      ws.current.onclose = () => {
        setStatus("OFFLINE");
        // Reconnect after 3 seconds
        reconnectTimeout = setTimeout(connect, 3000);
      };

      ws.current.onerror = () => {
        if (ws.current) {
          ws.current.close();
        }
      };
    };

    connect();

    return () => {
      clearTimeout(reconnectTimeout);
      if (ws.current) {
        ws.current.onclose = null;
        ws.current.close();
      }
    };
  }, [onMessage]);

  return (
    <WebSocketContext.Provider value={{ status }}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocketStatus() {
  return useContext(WebSocketContext);
}
