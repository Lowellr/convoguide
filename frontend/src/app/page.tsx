"use client";

import { useState, useCallback } from "react";
import { VoiceAgent } from "@/components/VoiceAgent";

type ConnectionState = "disconnected" | "connecting" | "connected";

export default function Home() {
  const [connectionState, setConnectionState] =
    useState<ConnectionState>("disconnected");
  const [token, setToken] = useState<string>("");
  const [serverUrl, setServerUrl] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [participantName, setParticipantName] = useState<string>("");

  const handleConnect = useCallback(async () => {
    if (!participantName.trim()) {
      setError("Please enter your name");
      return;
    }

    setConnectionState("connecting");
    setError("");

    try {
      // Generate a unique room name
      const roomName = `convoguide-${Date.now()}`;

      // Fetch token from API
      const response = await fetch("/api/token", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          roomName,
          participantName: participantName.trim(),
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || "Failed to get token");
      }

      const data = await response.json();
      setToken(data.token);
      setServerUrl(data.serverUrl);
      setConnectionState("connected");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Connection failed");
      setConnectionState("disconnected");
    }
  }, [participantName]);

  const handleDisconnect = useCallback(() => {
    setConnectionState("disconnected");
    setToken("");
    setServerUrl("");
  }, []);

  // Connected state - show voice agent
  if (connectionState === "connected" && token && serverUrl) {
    return (
      <main className="h-screen bg-background">
        <VoiceAgent
          token={token}
          serverUrl={serverUrl}
          onDisconnect={handleDisconnect}
        />
      </main>
    );
  }

  // Disconnected/connecting state - show landing page
  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-8 bg-background">
      <div className="max-w-md w-full space-y-8">
        {/* Logo/Title */}
        <div className="text-center">
          <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
            <span className="text-4xl">🎙️</span>
          </div>
          <h1 className="text-3xl font-bold mb-2">ConvoGuide</h1>
          <p className="text-gray-400">
            An adaptive AI that responds to your mood and style
          </p>
        </div>

        {/* Mode showcase */}
        <div className="grid grid-cols-3 gap-2 text-center text-xs">
          <ModeChip emoji="😄" label="Humor" color="bg-yellow-500/20" />
          <ModeChip emoji="💗" label="Empathy" color="bg-pink-500/20" />
          <ModeChip emoji="🎯" label="Serious" color="bg-blue-500/20" />
          <ModeChip emoji="✨" label="Creative" color="bg-purple-500/20" />
          <ModeChip emoji="⚔️" label="Debate" color="bg-orange-500/20" />
          <ModeChip emoji="💬" label="Casual" color="bg-gray-500/20" />
        </div>

        {/* Connection form */}
        <div className="space-y-4">
          <div>
            <label
              htmlFor="name"
              className="block text-sm font-medium text-gray-300 mb-2"
            >
              Your name
            </label>
            <input
              id="name"
              type="text"
              value={participantName}
              onChange={(e) => setParticipantName(e.target.value)}
              placeholder="Enter your name"
              className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 transition-colors"
              onKeyDown={(e) => e.key === "Enter" && handleConnect()}
            />
          </div>

          {error && (
            <div className="p-3 bg-red-900/50 border border-red-700 rounded-lg text-red-200 text-sm">
              {error}
            </div>
          )}

          <button
            onClick={handleConnect}
            disabled={connectionState === "connecting"}
            className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 disabled:cursor-not-allowed rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
          >
            {connectionState === "connecting" ? (
              <>
                <LoadingSpinner />
                Connecting...
              </>
            ) : (
              <>
                <span>🎤</span>
                Start Conversation
              </>
            )}
          </button>
        </div>

        {/* Footer info */}
        <p className="text-center text-xs text-gray-500">
          Speak naturally — I'll adapt to jokes, serious questions, emotions,
          and more
        </p>
      </div>
    </main>
  );
}

function ModeChip({
  emoji,
  label,
  color,
}: {
  emoji: string;
  label: string;
  color: string;
}) {
  return (
    <div className={`${color} px-2 py-1.5 rounded-lg`}>
      <span className="mr-1">{emoji}</span>
      {label}
    </div>
  );
}

function LoadingSpinner() {
  return (
    <svg
      className="animate-spin h-5 w-5"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  );
}
