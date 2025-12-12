# ConvoGuide - Adaptive Conversational Agent

A real-time voice/chat application with a single front-facing AI persona that dynamically routes to specialist "style agents" behind the scenes—all while appearing seamless to the user.

## Architecture

```
User speaks → LiveKit Room → STT (Deepgram) → Transcription
    ↓
Agent Worker (Python - livekit-agents)
    ↓
ConvoGuide Agent (OpenAI GPT-4o-mini with function calling)
    ↓ (optional tool calls)
Style Specialists:
  - humor_style      → HumorAgent
  - empathy_style    → EmpathyAgent
  - serious_style    → SeriousModeAgent
  - storyweaver_style → StoryWeaverAgent
  - creativity_style  → CreativityAgent
  - debate_style     → DebateAgent
  - clarity_style    → ClarityAgent
    ↓
Final response → TTS (Cartesia) → Audio back to user
```

## Features

- **Seamless mode-switching**: User goes from jokes → vulnerability → planning, and the agent adapts naturally
- **Persistent session state**: Tracks mode, topic, mood history across the conversation
- **Tool-based architecture**: Specialists are OpenAI-style function calls, easy to extend
- **Real-time voice**: Full-duplex audio with LiveKit
- **Text fallback**: Chat interface for text input when preferred

## Prerequisites

- Python 3.11+
- Node.js 18+
- [uv](https://github.com/astral-sh/uv) package manager
- LiveKit Cloud account (or self-hosted LiveKit server)
- API keys for: OpenAI, Deepgram, Cartesia

## Setup

### 1. Clone and configure environment

```bash
# Copy environment templates
cp .env.example .env
cp agent/.env.example agent/.env.local
cp frontend/.env.example frontend/.env.local

# Edit with your API keys
```

### 2. Start the Python agent

```bash
cd agent

# Install dependencies with uv
uv sync

# Run in development mode
uv run python -m src.main dev
```

### 3. Start the frontend

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### 4. Open in browser

Navigate to `http://localhost:3000`, enter your name, and start talking!

## Project Structure

```
personalityAgent/
├── frontend/                    # React/Next.js app
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx        # Main voice interface
│   │   │   └── api/token/      # Token generation endpoint
│   │   └── components/
│   │       ├── VoiceAgent.tsx  # LiveKit room + audio viz
│   │       └── ChatInterface.tsx
│   └── package.json
│
├── agent/                       # Python LiveKit agent
│   ├── src/
│   │   ├── main.py             # Entry point + AgentSession
│   │   ├── session_state.py    # Session state management
│   │   ├── tools/              # Style specialist tools
│   │   │   ├── humor.py
│   │   │   ├── empathy.py
│   │   │   ├── serious.py
│   │   │   ├── storyweaver.py
│   │   │   ├── creativity.py
│   │   │   ├── debate.py
│   │   │   └── clarity.py
│   │   └── prompts/
│   │       ├── convoguide.py   # Main agent prompt
│   │       └── specialists.py  # Specialist prompts
│   └── pyproject.toml
│
└── .env.example
```

## Conversational Modes

| Mode | Triggered By | Specialist |
|------|--------------|------------|
| Casual | Default | None |
| Humor | "roast me", "tell me a joke" | HumorAgent |
| Serious | "be honest", "no jokes please" | SeriousModeAgent |
| Empathetic | "I'm stressed", "I feel sad" | EmpathyAgent |
| Creative | "tell me a story", "give me ideas" | StoryWeaverAgent/CreativityAgent |
| Debate | "convince me", "argue with me" | DebateAgent |

## API Keys

| Service | Purpose | Get it at |
|---------|---------|-----------|
| LiveKit | Real-time audio/video | [livekit.io](https://livekit.io) |
| OpenAI | LLM (GPT-4o-mini) | [platform.openai.com](https://platform.openai.com) |
| Deepgram | Speech-to-text | [deepgram.com](https://deepgram.com) |
| Cartesia | Text-to-speech | [cartesia.ai](https://cartesia.ai) |

## Development

### Adding a new specialist

1. Create a new tool in `agent/src/tools/newspecialist.py`
2. Add the system prompt in `agent/src/prompts/specialists.py`
3. Export from `agent/src/tools/__init__.py`
4. Add to the tools list in `agent/src/main.py`

### Customizing the voice

Edit `agent/src/main.py` and change the Cartesia TTS configuration:

```python
tts=cartesia.TTS(voice="your-voice-id")
```

## License

MIT
# convoguide
