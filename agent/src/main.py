"""
ConvoGuide Agent - Main entry point for LiveKit voice agent.

A single conversational AI persona that dynamically routes to specialist
style agents behind the scenes for adaptive responses.
"""

import asyncio
import json
import logging
import time
from dotenv import load_dotenv

from livekit import rtc
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    WorkerOptions,
    cli,
)
from livekit.plugins import deepgram, openai, cartesia, silero

from .prompts import CONVOGUIDE_PROMPT
from .tools import (
    humor_style,
    empathy_style,
    serious_style,
    storyweaver_style,
    creativity_style,
    debate_style,
    clarity_style,
)
from .session_state import (
    get_session_state,
    infer_mode_from_text,
    infer_mood_from_text,
    ConversationMode,
)

# Map tool names to their corresponding modes
TOOL_TO_MODE = {
    "humor_style": "humor",
    "empathy_style": "empathetic",
    "serious_style": "serious",
    "storyweaver_style": "creative",
    "creativity_style": "creative",
    "debate_style": "debate",
    "clarity_style": "casual",
}

load_dotenv()

logger = logging.getLogger("convoguide")
logger.setLevel(logging.INFO)


class ConvoGuideAgent(Agent):
    """
    The main ConvoGuide agent that handles all user interactions.
    Routes to specialist style agents via tools when needed.
    """

    def __init__(self) -> None:
        super().__init__(
            instructions=CONVOGUIDE_PROMPT,
            tools=[
                humor_style,
                empathy_style,
                serious_style,
                storyweaver_style,
                creativity_style,
                debate_style,
                clarity_style,
            ],
        )


class ModeTracker:
    """Helper class to track and broadcast mode changes."""
    def __init__(self, room):
        self.room = room

    async def send_mode_update(self, mode: str):
        """Send mode update to frontend."""
        try:
            await self.room.local_participant.publish_data(
                payload=json.dumps({"mode": mode}).encode(),
                topic="mode-update"
            )
            logger.info(f"Sent mode update to frontend: {mode}")
        except Exception as e:
            logger.error(f"Failed to send mode update: {e}")

    async def publish_to_chat(self, text: str):
        """Publish text to chat channel in LiveKit chat format."""
        try:
            # Format message as LiveKit expects for useChat() hook
            message_data = {
                "message": text,
                "timestamp": int(time.time() * 1000),  # milliseconds
            }
            await self.room.local_participant.publish_data(
                payload=json.dumps(message_data).encode("utf-8"),
                topic="lk-chat-topic",
            )
            logger.info(f"Published to chat: {text[:50]}...")
        except Exception as e:
            logger.error(f"Failed to publish to chat: {e}")


async def entrypoint(ctx: JobContext):
    """Main entry point for the LiveKit agent worker."""

    logger.info(f"Connecting to room: {ctx.room.name}")
    await ctx.connect()

    # Get or create session state for this room
    session_state = get_session_state(ctx.room.name)
    logger.info(f"Session state initialized: {session_state.to_context_string()}")

    # Create mode tracker
    mode_tracker = ModeTracker(ctx.room)

    # Create the agent session with STT, LLM, TTS, and VAD
    session = AgentSession(
        stt=deepgram.STT(),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=cartesia.TTS(),
        vad=silero.VAD.load(),
    )

    # Create the ConvoGuide agent
    agent = ConvoGuideAgent()

    # Set up event handlers for session state tracking
    @session.on("user_input")
    def on_user_input(text: str):
        """Track user mood and mode from their input."""
        # Detect mode shift
        detected_mode = infer_mode_from_text(text)
        if detected_mode:
            session_state.update_mode(detected_mode)
            logger.info(f"Mode shifted to: {detected_mode.value}")
            # Send mode update asynchronously
            asyncio.create_task(mode_tracker.send_mode_update(detected_mode.value))

        # Detect mood
        detected_mood = infer_mood_from_text(text)
        if detected_mood:
            session_state.log_mood(detected_mood)
            logger.info(f"Mood detected: {detected_mood}")

    @session.on("user_input_transcribed")
    def on_user_input_transcribed(event):
        """Send user transcriptions to chat."""
        logger.info(f"USER INPUT TRANSCRIBED: {event.transcript}")
        asyncio.create_task(mode_tracker.publish_to_chat(event.transcript))

    @session.on("speech_created")
    def on_speech_created(event):
        """Send agent speech to chat."""
        # Get the text from the speech event
        if hasattr(event, 'text'):
            text = event.text
        elif hasattr(event, 'message'):
            text = event.message
        else:
            text = str(event)
        logger.info(f"SPEECH CREATED: {text[:50]}...")
        asyncio.create_task(mode_tracker.publish_to_chat(text))

    @session.on("function_tools_executed")
    def on_function_tools_executed(event):
        """Track when tools are executed and send mode updates."""
        logger.info(f"FUNCTION TOOLS EXECUTED EVENT TRIGGERED")
        logger.info(f"Event type: {type(event)}, Event attributes: {dir(event)}")

        # Try to access tool calls
        if hasattr(event, 'function_calls'):
            logger.info(f"Function calls: {event.function_calls}")
            for call in event.function_calls:
                tool_name = call.name if hasattr(call, 'name') else call.function_info.name
                logger.info(f"Tool executed: {tool_name}")
                if tool_name in TOOL_TO_MODE:
                    mode = TOOL_TO_MODE[tool_name]
                    logger.info(f"Sending mode update: {tool_name} -> {mode}")
                    asyncio.create_task(mode_tracker.send_mode_update(mode))
        elif hasattr(event, 'zipped'):
            for call, output in event.zipped():
                tool_name = call.function_info.name
                logger.info(f"Tool executed: {tool_name}")
                if tool_name in TOOL_TO_MODE:
                    mode = TOOL_TO_MODE[tool_name]
                    logger.info(f"Sending mode update: {tool_name} -> {mode}")
                    asyncio.create_task(mode_tracker.send_mode_update(mode))
        else:
            logger.warning(f"Unable to extract tool calls from event: {event}")

    # Start the agent session
    await session.start(
        agent=agent,
        room=ctx.room,
    )

    logger.info("ConvoGuide agent started and ready for conversation")

    # Send initial mode to frontend
    await mode_tracker.send_mode_update(session_state.mode.value)


def main():
    """CLI entry point."""
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
        )
    )


if __name__ == "__main__":
    main()
