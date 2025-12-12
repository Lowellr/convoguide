"use client";

import { useCallback, useState, useEffect } from "react";
import {
  LiveKitRoom,
  RoomAudioRenderer,
  useVoiceAssistant,
  BarVisualizer,
  VoiceAssistantControlBar,
  useRoomContext,
  useConnectionState,
  useDataChannel,
} from "@livekit/components-react";
import "@livekit/components-styles";
import { ConnectionState } from "livekit-client";
import { ChatInterface } from "./ChatInterface";

interface VoiceAgentProps {
  token: string;
  serverUrl: string;
  onDisconnect?: () => void;
}

function AgentRoom({ onDisconnect }: { onDisconnect?: () => void }) {
  const room = useRoomContext();
  const connectionState = useConnectionState();
  const voiceAssistant = useVoiceAssistant();
  const [currentMode, setCurrentMode] = useState<string>("casual");
  const [modeChanged, setModeChanged] = useState(false);

  // Listen for mode updates from the agent via data channel
  useDataChannel("mode-update", (msg) => {
    try {
      const decoded = new TextDecoder().decode(msg.payload);
      console.log("Raw mode update received:", decoded);
      const data = JSON.parse(decoded);
      console.log("Parsed mode data:", data);
      if (data.mode) {
        console.log("Setting mode to:", data.mode);
        setCurrentMode(data.mode);
      }
    } catch (e) {
      console.error("Error parsing mode update:", e);
    }
  });

  const handleDisconnect = useCallback(() => {
    room.disconnect();
    onDisconnect?.();
  }, [room, onDisconnect]);

  return (
    <div className="flex flex-col h-full">
      {/* Header with mode indicator */}
      <div className="flex items-center justify-between p-4 border-b border-gray-800">
        <div className="flex items-center gap-3">
          <div className="w-3 h-3 rounded-full bg-green-500 animate-pulse" />
          <span className="text-sm text-gray-400">
            {connectionState === ConnectionState.Connected
              ? "Connected to ConvoGuide"
              : "Connecting..."}
          </span>
        </div>
        <ModeIndicator mode={currentMode} />
      </div>

      {/* Main content area */}
      <div className="flex-1 flex flex-col items-center justify-center p-8">
        {/* Voice visualizer */}
        <div className="mb-8">
          {voiceAssistant.state === "listening" ||
          voiceAssistant.state === "speaking" ? (
            <div className="w-64 h-32">
              <BarVisualizer
                state={voiceAssistant.state}
                trackRef={voiceAssistant.audioTrack}
                barCount={5}
                options={{
                  minHeight: 20,
                }}
              />
            </div>
          ) : (
            <div className="w-32 h-32 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
              <span className="text-4xl">🎙️</span>
            </div>
          )}
        </div>

        {/* Status text */}
        <div className="text-center mb-8">
          <h2 className="text-xl font-semibold mb-2">
            {voiceAssistant.state === "listening"
              ? "Listening..."
              : voiceAssistant.state === "speaking"
              ? "Speaking..."
              : voiceAssistant.state === "thinking"
              ? "Thinking..."
              : "Ready to chat"}
          </h2>
          <p className="text-gray-400 text-sm">
            Speak naturally — I adapt to your mood and style
          </p>
        </div>

        {/* Control bar */}
        <VoiceAssistantControlBar />
      </div>

      {/* Chat interface */}
      <ChatInterface currentMode={currentMode} />

      {/* Disconnect button */}
      <div className="p-4 border-t border-gray-800">
        <button
          onClick={handleDisconnect}
          className="w-full py-2 px-4 bg-red-600 hover:bg-red-700 rounded-lg text-sm transition-colors"
        >
          End Conversation
        </button>
      </div>

      {/* Audio renderer (required for hearing the agent) */}
      <RoomAudioRenderer />
    </div>
  );
}

function ModeIndicator({ mode }: { mode: string }) {
  const modeConfig: Record<string, { color: string; label: string; emoji: string }> = {
    casual: { color: "bg-gray-500", label: "Casual", emoji: "💬" },
    humor: { color: "bg-yellow-500", label: "Playful", emoji: "😄" },
    serious: { color: "bg-blue-500", label: "Serious", emoji: "🎯" },
    empathetic: { color: "bg-pink-500", label: "Empathetic", emoji: "💗" },
    creative: { color: "bg-purple-500", label: "Creative", emoji: "✨" },
    debate: { color: "bg-orange-500", label: "Debate", emoji: "⚔️" },
  };

  const config = modeConfig[mode] || modeConfig.casual;

  return (
    <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-800 rounded-full">
      <div className={`w-2 h-2 rounded-full ${config.color}`} />
      <span className="text-xs text-gray-300">
        {config.emoji} {config.label}
      </span>
    </div>
  );
}

export function VoiceAgent({ token, serverUrl, onDisconnect }: VoiceAgentProps) {
  return (
    <LiveKitRoom
      token={token}
      serverUrl={serverUrl}
      connect={true}
      audio={true}
      video={false}
      className="h-full"
    >
      <AgentRoom onDisconnect={onDisconnect} />
    </LiveKitRoom>
  );
}
