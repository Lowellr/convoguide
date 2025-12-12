# ConvoGuide Architecture - Mode Detection System

This document describes how ConvoGuide's real-time conversational mode detection and UI indicator system works.

## Overview

ConvoGuide presents a single unified AI persona to users while dynamically adapting its conversational style through specialist agents. The mode indicator provides real-time visual feedback showing which conversational style is currently active.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Mode Indicator                                          │  │
│  │  💬 Casual | 😄 Playful | 🎯 Serious | 💗 Empathetic   │  │
│  │  ✨ Creative | ⚔️ Debate                                 │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Frontend (Next.js + React)                                     │
│  - VoiceAgent.tsx: Mode state & data channel listener          │
│  - ChatInterface.tsx: Conversation transcript                   │
└────────────────────┬────────────────────────────────────────────┘
                     │ LiveKit WebRTC + Data Channels
                     │
┌────────────────────┴────────────────────────────────────────────┐
│                    LiveKit Room (Cloud)                         │
│  - Audio/Video streams (WebRTC)                                 │
│  - Data channels: "mode-update", "lk-chat-topic"                │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────────────┐
│              Python Agent Worker (Backend)                      │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  AgentSession (livekit-agents)                         │    │
│  │  - STT: Deepgram (speech-to-text)                      │    │
│  │  - LLM: OpenAI GPT-4o-mini (conversation logic)        │    │
│  │  - TTS: Cartesia (text-to-speech)                      │    │
│  │  - VAD: Silero (voice activity detection)              │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Event Handlers                                        │    │
│  │  - user_input_transcribed → Mode detection & chat      │    │
│  │  - speech_created → Publish to chat                    │    │
│  │  - function_tools_executed → Future: Tool-based modes  │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  ModeTracker                                           │    │
│  │  - send_mode_update(mode) → Data channel              │    │
│  │  - publish_to_chat(text) → Chat messages              │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Session State                                         │    │
│  │  - infer_mode_from_text() → Keyword-based detection    │    │
│  │  - infer_mood_from_text() → Emotional state tracking   │    │
│  │  - SessionState: mode, topic, mood_history             │    │
│  └────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

## Data Flow: User Speech to Mode Update

### Step-by-Step Process

1. **User Speaks**
   ```
   User: "Tell me a joke"
   ```

2. **Speech-to-Text (Deepgram STT)**
   - Audio is streamed to Deepgram via WebSocket
   - Deepgram returns real-time transcription
   - Transcript: `"Tell me a joke"`

3. **Event: `user_input_transcribed`**
   ```python
   @session.on("user_input_transcribed")
   def on_user_input_transcribed_for_mode(event):
       text = event.transcript  # "Tell me a joke"

       # Detect mode from keywords
       detected_mode = infer_mode_from_text(text)
       # Returns: ConversationMode.HUMOR
   ```

4. **Mode Detection Logic**
   ```python
   def infer_mode_from_text(text: str) -> Optional[ConversationMode]:
       text_lower = text.lower()

       # Check for humor signals
       if "joke" in text_lower or "funny" in text_lower:
           return ConversationMode.HUMOR  # ✓ Match found!
   ```

5. **Update Session State**
   ```python
   session_state.update_mode(detected_mode)
   # mode changes from CASUAL → HUMOR
   ```

6. **Broadcast to Frontend**
   ```python
   await mode_tracker.send_mode_update("humor")
   # Publishes JSON: {"mode": "humor"} to data channel "mode-update"
   ```

7. **Frontend Receives Update**
   ```typescript
   useDataChannel("mode-update", (msg) => {
     const data = JSON.parse(msg.payload);
     // data = {mode: "humor"}
     setCurrentMode(data.mode);  // "humor"
   });
   ```

8. **UI Updates**
   ```tsx
   <ModeIndicator mode={currentMode} />
   // Renders: 😄 Playful (yellow pill)
   ```

## Mode Detection Keywords

| Mode | Enum Value | Trigger Keywords | UI Display |
|------|-----------|------------------|------------|
| Casual | `casual` | (default) | 💬 Casual (gray) |
| Humor | `humor` | joke, funny, roast, laugh, silly | 😄 Playful (yellow) |
| Serious | `serious` | serious, honest, no jokes, be real | 🎯 Serious (blue) |
| Empathetic | `empathetic` | stressed, sad, overwhelmed, anxious | 💗 Empathetic (pink) |
| Creative | `creative` | story, imagine, brainstorm, ideas | ✨ Creative (purple) |
| Debate | `debate` | convince me, argue, pros and cons | ⚔️ Debate (orange) |

### Implementation

```python
# /agent/src/session_state.py
def infer_mode_from_text(text: str) -> Optional[ConversationMode]:
    text_lower = text.lower()

    # Humor signals
    humor_signals = ["roast", "joke", "funny", "make me laugh",
                     "tell me something funny", "be silly", "goofy"]
    if any(signal in text_lower for signal in humor_signals):
        return ConversationMode.HUMOR

    # Serious signals
    serious_signals = ["serious", "honest answer", "no jokes",
                       "be real", "straight answer", "honestly"]
    if any(signal in text_lower for signal in serious_signals):
        return ConversationMode.SERIOUS

    # ... similar for other modes

    return None  # No mode detected, keep current mode
```

## Communication Channels

### 1. Data Channel: `mode-update`

**Purpose**: Broadcast conversational mode changes from backend to frontend

**Message Format**:
```json
{
  "mode": "humor"
}
```

**Backend (Python)**:
```python
await room.local_participant.publish_data(
    payload=json.dumps({"mode": mode}).encode(),
    topic="mode-update"
)
```

**Frontend (React)**:
```typescript
useDataChannel("mode-update", (msg) => {
  const data = JSON.parse(new TextDecoder().decode(msg.payload));
  setCurrentMode(data.mode);
});
```

### 2. Data Channel: `lk-chat-topic`

**Purpose**: Display conversation transcript in chat interface

**Message Format**:
```json
{
  "message": "Tell me a joke",
  "timestamp": 1734043200000
}
```

**Backend (Python)**:
```python
message_data = {
    "message": text,
    "timestamp": int(time.time() * 1000)  # milliseconds
}
await room.local_participant.publish_data(
    payload=json.dumps(message_data).encode("utf-8"),
    topic="lk-chat-topic"
)
```

**Frontend (React)**:
```typescript
const { chatMessages } = useChat();
// Automatically subscribes to "lk-chat-topic"
```

## Event Handlers

### `user_input_transcribed`

**Triggered**: When user speech is transcribed by STT

**Purpose**:
- Detect conversational mode from user intent
- Detect emotional mood
- Publish user transcript to chat

```python
@session.on("user_input_transcribed")
def on_user_input_transcribed_for_mode(event):
    text = event.transcript

    # Mode detection
    detected_mode = infer_mode_from_text(text)
    if detected_mode:
        session_state.update_mode(detected_mode)
        asyncio.create_task(mode_tracker.send_mode_update(detected_mode.value))

    # Mood detection
    detected_mood = infer_mood_from_text(text)
    if detected_mood:
        session_state.log_mood(detected_mood)

    # Publish to chat
    asyncio.create_task(mode_tracker.publish_to_chat(event.transcript))
```

### `speech_created`

**Triggered**: When agent begins speaking (TTS output ready)

**Purpose**: Publish agent's response to chat interface

```python
@session.on("speech_created")
def on_speech_created(event):
    text = event.text if hasattr(event, 'text') else str(event)
    asyncio.create_task(mode_tracker.publish_to_chat(text))
```

### `function_tools_executed` (Future Enhancement)

**Triggered**: When LLM calls specialist style tools

**Purpose**: Update mode based on which specialist agent was invoked

```python
@session.on("function_tools_executed")
def on_function_tools_executed(event):
    # Map tool names to modes
    TOOL_TO_MODE = {
        "humor_style": "humor",
        "empathy_style": "empathetic",
        "serious_style": "serious",
        # ...
    }

    for call in event.function_calls:
        tool_name = call.name
        if tool_name in TOOL_TO_MODE:
            mode = TOOL_TO_MODE[tool_name]
            asyncio.create_task(mode_tracker.send_mode_update(mode))
```

## Session State Management

### SessionState Class

Tracks conversation context across the session:

```python
@dataclass
class SessionState:
    mode: ConversationMode = ConversationMode.CASUAL
    topic: Optional[str] = None
    mood_history: list[str] = field(default_factory=list)

    def update_mode(self, new_mode: ConversationMode) -> None:
        self.mode = new_mode

    def log_mood(self, mood: str) -> None:
        self.mood_history.append(mood)
        if len(self.mood_history) > 10:
            self.mood_history = self.mood_history[-10:]
```

**Storage**: In-memory dictionary keyed by `room_id`

```python
_session_states: dict[str, SessionState] = {}

def get_session_state(room_id: str) -> SessionState:
    if room_id not in _session_states:
        _session_states[room_id] = SessionState()
    return _session_states[room_id]
```

## Specialist Agents (Tools)

While mode detection is currently based on user intent, the system is designed to support tool-based specialist agents:

```python
class ConvoGuideAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=CONVOGUIDE_PROMPT,
            tools=[
                humor_style,        # Add humor to responses
                empathy_style,      # Add emotional validation
                serious_style,      # Make responses analytical
                storyweaver_style,  # Transform into narrative
                creativity_style,   # Generate creative ideas
                debate_style,       # Construct arguments
                clarity_style,      # Simplify complex topics
            ],
        )
```

Each tool is a Python function decorated with `@llm.function_tool`:

```python
@llm.function_tool(
    name="humor_style",
    description="Add light humor or playful tone to a message"
)
async def humor_style(
    base_message: Annotated[str, "The base message to add humor to"],
    humor_level: Annotated[str, "Level of humor: subtle, moderate, playful"],
    conversation_context: Annotated[str, "Recent conversation context"]
) -> str:
    # LLM-powered humor injection
    ...
```

## Frontend Components

### VoiceAgent.tsx

Main component managing:
- LiveKit room connection
- Voice assistant state
- Mode indicator display
- Data channel subscriptions

```typescript
function AgentRoom({ onDisconnect }: { onDisconnect?: () => void }) {
  const [currentMode, setCurrentMode] = useState<string>("casual");

  // Subscribe to mode updates
  useDataChannel("mode-update", (msg) => {
    const data = JSON.parse(new TextDecoder().decode(msg.payload));
    if (data.mode) {
      setCurrentMode(data.mode);
    }
  });

  return (
    <>
      <ModeIndicator mode={currentMode} />
      <ChatInterface currentMode={currentMode} />
      <RoomAudioRenderer />
    </>
  );
}
```

### ModeIndicator Component

Visual pill showing current mode:

```typescript
function ModeIndicator({ mode }: { mode: string }) {
  const modeConfig = {
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
```

### ChatInterface Component

Displays conversation transcript using LiveKit's `useChat` hook:

```typescript
export function ChatInterface({ currentMode }: { currentMode: string }) {
  const { chatMessages } = useChat();

  return (
    <div className="chat-container">
      {chatMessages.map((msg) => (
        <div key={msg.id} className="message">
          <span className="timestamp">{formatTime(msg.timestamp)}</span>
          <p>{msg.message}</p>
        </div>
      ))}
    </div>
  );
}
```

## Key Design Decisions

### 1. User-Intent Detection vs Tool-Based Detection

**Current Approach**: Keyword-based intent detection

**Rationale**:
- ✅ Instant feedback (no LLM latency)
- ✅ Reliable (not dependent on tool execution)
- ✅ Simple implementation

**Future Enhancement**: Hybrid approach
- Use intent detection for instant UI feedback
- Use tool execution to confirm and refine mode selection

### 2. Data Channels vs Custom WebSocket

**Current Approach**: LiveKit data channels

**Rationale**:
- ✅ Built into LiveKit SDK
- ✅ Same infrastructure as audio/video
- ✅ Reliable delivery with room lifecycle
- ✅ No additional server infrastructure

### 3. In-Memory Session State

**Current Approach**: Python dictionary keyed by room_id

**Rationale**:
- ✅ Simple for single-worker deployment
- ✅ Fast access
- ✅ Automatic cleanup when room closes

**Limitation**: Not shared across multiple worker instances

**Future Enhancement**: Redis or similar for multi-worker deployments

### 4. Event-Driven Architecture

**Current Approach**: LiveKit AgentSession event handlers

**Rationale**:
- ✅ Reactive to real-time events
- ✅ Clean separation of concerns
- ✅ Easy to add new behaviors
- ✅ Async-friendly with `asyncio.create_task()`

## Performance Considerations

### Latency Budget

```
User speaks → Mode indicator updates
├─ STT latency: ~100-300ms (Deepgram)
├─ Python processing: <10ms (keyword matching)
├─ Data channel publish: <50ms (WebRTC)
└─ Frontend state update: <10ms (React)
────────────────────────────────────────
Total: ~150-400ms (perceived as instant)
```

### Scalability

**Current Setup**: Single LiveKit worker

**Scaling Strategy**:
- LiveKit Cloud auto-scales workers
- Each room gets dedicated worker process
- Session state is room-scoped (no cross-room dependencies)

**Bottlenecks**:
- STT API rate limits (Deepgram)
- LLM API rate limits (OpenAI)
- TTS API rate limits (Cartesia)

## Testing & Debugging

### Enable Debug Logging

```python
# agent/src/main.py
logger.setLevel(logging.DEBUG)

# See mode detection in action
logger.info(f"Checking for mode in text: '{text}'")
logger.info(f"Detected mode: {detected_mode}")
logger.info(f"Mode shifted to: {detected_mode.value}")
logger.info(f"Sent mode update to frontend: {mode}")
```

### Browser Console

```javascript
// frontend/src/components/VoiceAgent.tsx
console.log("Raw mode update received:", decoded);
console.log("Parsed mode data:", data);
console.log("Setting mode to:", data.mode);
```

### Test Mode Transitions

1. Start a session
2. Say trigger phrases:
   - "Tell me a joke" → Should see 😄 Playful
   - "Be serious with me" → Should see 🎯 Serious
   - "I'm feeling stressed" → Should see 💗 Empathetic
3. Watch browser console for data channel messages
4. Check Python logs for mode detection

## Troubleshooting

### Mode Indicator Not Updating

**Check**:
1. Backend logs show "Sent mode update to frontend: {mode}"
2. Frontend console shows "Raw mode update received"
3. React component re-renders (React DevTools)

**Common Issues**:
- Frontend not connected to LiveKit room
- Data channel topic mismatch
- JSON parsing error (check payload format)

### Incorrect Mode Detection

**Check**:
1. Backend logs show detected keywords
2. `infer_mode_from_text()` returns expected mode
3. Keywords in `session_state.py` match user phrases

**Solution**: Add more trigger keywords to detection logic

### Chat Messages Not Appearing

**Check**:
1. Backend publishes to "lk-chat-topic" (exact topic name)
2. Frontend `useChat()` hook is active
3. Message format includes `message` and `timestamp` fields

## Future Enhancements

1. **Hybrid Mode Detection**
   - Combine user-intent keywords with LLM tool execution
   - Intent detection for instant UI feedback
   - Tool execution for confirmation and refinement

2. **Mode Transition Animations**
   - Smooth color transitions on mode change
   - Brief animation on mode pill

3. **Persistent Session History**
   - Store conversation context in database
   - Resume sessions across disconnects

4. **Custom Mode Triggers**
   - User-configurable keywords
   - Per-user mode preferences

5. **Analytics Dashboard**
   - Track mode distribution over time
   - Identify popular conversational styles

---

**Last Updated**: 2025-12-12
**Author**: ConvoGuide Team
**License**: MIT
