"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import type {
  GenerationState,
  WebSocketMessage,
  ThemeRefinement,
  ArtistDiscoveryData,
  ArtworkDiscoveryData,
} from "@/types/exhibition";
import type { CuratorBrief } from "@/types/curator";

interface UseExhibitionGenerationProps {
  sessionId: string;
  curatorBrief: CuratorBrief;
  automaticMode?: boolean;
  autoStart?: boolean;
}

interface UseExhibitionGenerationReturn {
  state: GenerationState;
  connect: () => void;
  disconnect: () => void;
  isConnected: boolean;
}

export function useExhibitionGeneration({
  sessionId,
  curatorBrief,
  automaticMode = false,
  autoStart = false,
}: UseExhibitionGenerationProps): UseExhibitionGenerationReturn {
  const [state, setState] = useState<GenerationState>(() => {
    // Try to restore state from sessionStorage on mount
    if (typeof window !== "undefined") {
      const stored = sessionStorage.getItem(`exhibition_state_${sessionId}`);
      if (stored) {
        try {
          const parsedState = JSON.parse(stored);
          // If the state was completed, keep it. If it was generating, mark as idle so user can retry
          if (parsedState.status === "completed" || parsedState.status === "error") {
            return parsedState;
          } else {
            // Keep the data but reset connection status
            return {
              ...parsedState,
              status: "idle" as const,
            };
          }
        } catch (e) {
          console.error("Failed to restore state:", e);
        }
      }
    }

    return {
      status: "idle",
      progress: 0,
      currentStage: null,
      theme: null,
      artists: null,
      artworks: null,
      error: null,
      proposalUrl: null,
    };
  });

  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 3;

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setIsConnected(false);
  }, []);

  const connect = useCallback(() => {
    // Don't reconnect if already connected or connecting
    if (wsRef.current?.readyState === WebSocket.OPEN || wsRef.current?.readyState === WebSocket.CONNECTING) {
      console.log("Already connected or connecting, skipping...");
      return;
    }

    if (reconnectAttempts.current >= maxReconnectAttempts) {
      setState((prev) => ({
        ...prev,
        status: "error",
        error: "Failed to connect after multiple attempts. Please refresh the page.",
      }));
      return;
    }

    console.log("Initiating connection to backend...");

    setState((prev) => ({
      ...prev,
      status: "connecting",
      error: null,
    }));

    // Step 1: Submit curator brief to get WebSocket URL
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

    fetch(`${apiBaseUrl}/api/curator/submit`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        curator_brief: curatorBrief,
        config: {
          max_artists: 8,
          max_artworks: 25,
          min_artist_relevance: 0.6,
          min_artwork_relevance: 0.5,
          auto_select: automaticMode,
        },
      }),
    })
      .then(async (response) => {
        if (!response.ok) {
          // Try to get detailed error message from response body
          let errorDetail = response.statusText;
          try {
            const errorData = await response.json();
            errorDetail = errorData.detail || JSON.stringify(errorData);
            console.error("Backend validation error:", errorData);
          } catch (e) {
            // If we can't parse the error, use status text
          }
          throw new Error(`Failed to submit brief: ${errorDetail}`);
        }
        return response.json();
      })
      .then((data) => {
        const wsBaseUrl = process.env.NEXT_PUBLIC_WS_URL?.replace("/ws/generate", "") || "ws://localhost:8000";
        const wsUrl = `${wsBaseUrl}${data.websocket_url}`;

        console.log("Connecting to WebSocket:", wsUrl);

        // Step 2: Connect to WebSocket (with small delay to let backend initialize)
        setTimeout(() => {
          const ws = new WebSocket(wsUrl);
          wsRef.current = ws;

        ws.onopen = () => {
          console.log("WebSocket connected successfully!");
          setIsConnected(true);
          reconnectAttempts.current = 0;
          setState((prev) => ({
            ...prev,
            status: "generating",
            currentStage: "theme_refinement" as any, // Set initial stage so UI shows progress
          }));
        };

        ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            console.log("📨 WebSocket message:", message.type, message);

            switch (message.type) {
              case "connected":
                console.log("✅ WebSocket handshake complete");
                break;

              case "progress":
                console.log(`⏳ Progress: ${message.progress}% - ${message.stage}`);
                setState((prev) => ({
                  ...prev,
                  progress: message.progress || prev.progress,
                  currentStage: (message.stage as any) || prev.currentStage,
                }));
                break;

              case "stage_complete":
                if (message.completed_stage === "theme_refinement") {
                  setState((prev) => ({
                    ...prev,
                    progress: message.progress || 25,
                    theme: message.data as ThemeRefinement,
                  }));
                } else if (message.completed_stage === "artist_discovery") {
                  setState((prev) => ({
                    ...prev,
                    progress: message.progress || 55,
                    artists: message.data as ArtistDiscoveryData,
                  }));
                } else if (message.completed_stage === "artwork_discovery") {
                  setState((prev) => ({
                    ...prev,
                    progress: message.progress || 90,
                    artworks: message.data as ArtworkDiscoveryData,
                  }));
                }
                break;

              case "completed":
                setState((prev) => ({
                  ...prev,
                  status: "completed",
                  progress: 100,
                  proposalUrl: message.proposal_url || null,
                }));
                disconnect();
                break;

              case "error":
                setState((prev) => ({
                  ...prev,
                  status: "error",
                  error: message.error || "An unknown error occurred",
                }));
                disconnect();
                break;
            }
          } catch (error) {
            console.error("Error parsing WebSocket message:", error);
          }
        };

        ws.onerror = (error) => {
          console.error("WebSocket error:", error);
          console.error("WebSocket URL was:", wsUrl);
          setState((prev) => ({
            ...prev,
            status: "error",
            error: "WebSocket connection error. Check that the backend is running on port 8001.",
          }));
        };

          ws.onclose = (event) => {
            setIsConnected(false);
            wsRef.current = null;

            console.log("WebSocket closed:", event.code, event.reason, "Clean:", event.wasClean);

            // Only attempt reconnect if it wasn't a clean close
            if (!event.wasClean) {
              reconnectAttempts.current++;
              if (reconnectAttempts.current < maxReconnectAttempts) {
                console.log(`Attempting reconnect ${reconnectAttempts.current}/${maxReconnectAttempts}...`);
                reconnectTimeoutRef.current = setTimeout(() => {
                  connect();
                }, 2000 * reconnectAttempts.current); // Exponential backoff
              } else {
                setState((prev) => ({
                  ...prev,
                  status: "error",
                  error: "Connection lost. Please refresh the page to try again.",
                }));
              }
            }
          };
        }, 500); // 500ms delay to let backend initialize
      })
      .catch((error) => {
        console.error("Error submitting brief:", error);
        setState((prev) => ({
          ...prev,
          status: "error",
          error: error.message || "Failed to start generation. Please try again.",
        }));
      });
  }, [curatorBrief, automaticMode, disconnect]);

  // Save state to sessionStorage whenever it changes
  useEffect(() => {
    if (state.status !== "idle") {
      sessionStorage.setItem(`exhibition_state_${sessionId}`, JSON.stringify(state));
    }
  }, [state, sessionId]);

  // Auto-start if requested (only once)
  useEffect(() => {
    let mounted = true;

    if (autoStart && mounted) {
      connect();
    }

    // Cleanup on unmount
    return () => {
      mounted = false;
      disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoStart]); // Only depend on autoStart, not connect/disconnect to avoid re-runs

  return {
    state,
    connect,
    disconnect,
    isConnected,
  };
}
