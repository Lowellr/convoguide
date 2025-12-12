"use client";

import { useState, useRef, useEffect, useCallback, FormEvent } from "react";
import {
  useChat,
  useLocalParticipant,
  useRoomContext,
} from "@livekit/components-react";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

interface ChatInterfaceProps {
  currentMode: string;
}

export function ChatInterface({ currentMode }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isExpanded, setIsExpanded] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const room = useRoomContext();
  const { localParticipant } = useLocalParticipant();

  // Use LiveKit's chat functionality
  const { chatMessages, send } = useChat();

  // Sync LiveKit chat messages to our local state
  useEffect(() => {
    const newMessages: Message[] = chatMessages.map((msg) => ({
      id: msg.id ?? crypto.randomUUID(),
      role: msg.from?.isLocal ? "user" : "assistant",
      content: msg.message,
      timestamp: new Date(msg.timestamp),
    }));
    setMessages(newMessages);
  }, [chatMessages]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = useCallback(
    async (e: FormEvent) => {
      e.preventDefault();
      if (!inputValue.trim()) return;

      // Send message via LiveKit data channel
      await send(inputValue.trim());
      setInputValue("");
    },
    [inputValue, send]
  );

  return (
    <div
      className={`border-t border-gray-800 transition-all duration-300 ${
        isExpanded ? "h-96" : "h-16"
      }`}
    >
      {/* Toggle header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-900 transition-colors"
      >
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">Chat Transcript</span>
          {messages.length > 0 && (
            <span className="px-2 py-0.5 bg-gray-700 rounded-full text-xs">
              {messages.length}
            </span>
          )}
        </div>
        <svg
          className={`w-4 h-4 transition-transform ${
            isExpanded ? "rotate-180" : ""
          }`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M5 15l7-7 7 7"
          />
        </svg>
      </button>

      {/* Expanded chat area */}
      {isExpanded && (
        <div className="flex flex-col h-[calc(100%-48px)]">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 py-2 space-y-3">
            {messages.length === 0 ? (
              <p className="text-center text-gray-500 text-sm py-8">
                Messages will appear here as you speak
              </p>
            ) : (
              messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${
                    msg.role === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  <div
                    className={`max-w-[80%] px-3 py-2 rounded-lg ${
                      msg.role === "user"
                        ? "bg-blue-600 text-white"
                        : "bg-gray-800 text-gray-100"
                    }`}
                  >
                    <p className="text-sm">{msg.content}</p>
                    <p className="text-xs opacity-50 mt-1">
                      {msg.timestamp.toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </p>
                  </div>
                </div>
              ))
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Text input for fallback */}
          <form onSubmit={handleSubmit} className="p-2 border-t border-gray-800">
            <div className="flex gap-2">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Type a message (or just speak)..."
                className="flex-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-blue-500 transition-colors"
              />
              <button
                type="submit"
                disabled={!inputValue.trim()}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed rounded-lg text-sm transition-colors"
              >
                Send
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
