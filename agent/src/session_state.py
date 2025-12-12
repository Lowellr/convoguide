"""Session state management for ConvoGuide conversations."""

from dataclasses import dataclass, field
from typing import Literal, Optional
from enum import Enum


class ConversationMode(str, Enum):
    """Possible conversational modes."""
    CASUAL = "casual"
    HUMOR = "humor"
    SERIOUS = "serious"
    EMPATHETIC = "empathetic"
    CREATIVE = "creative"
    DEBATE = "debate"


@dataclass
class SessionState:
    """Tracks the current state of a conversation session."""

    mode: ConversationMode = ConversationMode.CASUAL
    topic: Optional[str] = None
    mood_history: list[str] = field(default_factory=list)

    def update_mode(self, new_mode: ConversationMode) -> None:
        """Update the conversation mode."""
        self.mode = new_mode

    def set_topic(self, topic: Optional[str]) -> None:
        """Update the current topic."""
        self.topic = topic

    def log_mood(self, mood: str) -> None:
        """Add a mood observation to history (keep last 10)."""
        self.mood_history.append(mood)
        if len(self.mood_history) > 10:
            self.mood_history = self.mood_history[-10:]

    def to_context_string(self) -> str:
        """Format state as context for the LLM."""
        mood_str = ", ".join(self.mood_history[-3:]) if self.mood_history else "none observed"
        return f"Current mode: {self.mode.value}. Topic: {self.topic or 'general'}. Recent moods: {mood_str}."


def infer_mode_from_text(text: str) -> Optional[ConversationMode]:
    """
    Simple heuristic to detect what mode the user might be requesting.
    Returns None if no clear signal is detected.
    """
    text_lower = text.lower()

    # Humor signals
    humor_signals = ["roast", "joke", "funny", "make me laugh", "tell me something funny", "be silly", "goofy"]
    if any(signal in text_lower for signal in humor_signals):
        return ConversationMode.HUMOR

    # Serious signals
    serious_signals = ["serious", "honest answer", "no jokes", "be real", "straight answer", "honestly"]
    if any(signal in text_lower for signal in serious_signals):
        return ConversationMode.SERIOUS

    # Empathetic signals
    empathy_signals = ["i'm stressed", "i feel", "overwhelmed", "anxious", "sad", "frustrated",
                       "i'm struggling", "hard time", "i'm upset", "feeling down"]
    if any(signal in text_lower for signal in empathy_signals):
        return ConversationMode.EMPATHETIC

    # Creative signals
    creative_signals = ["tell me a story", "story about", "imagine", "what if", "invent",
                        "creative", "brainstorm", "wild ideas", "give me ideas"]
    if any(signal in text_lower for signal in creative_signals):
        return ConversationMode.CREATIVE

    # Debate signals
    debate_signals = ["convince me", "argue", "devil's advocate", "debate", "pros and cons",
                      "other side", "counterargument", "challenge"]
    if any(signal in text_lower for signal in debate_signals):
        return ConversationMode.DEBATE

    return None


def infer_mood_from_text(text: str) -> Optional[str]:
    """
    Simple heuristic to detect the user's emotional state.
    Returns a short mood descriptor or None.
    """
    text_lower = text.lower()

    if any(w in text_lower for w in ["anxious", "worried", "nervous", "stressed"]):
        return "anxious"
    if any(w in text_lower for w in ["sad", "down", "depressed", "blue"]):
        return "sad"
    if any(w in text_lower for w in ["frustrated", "annoyed", "irritated", "angry"]):
        return "frustrated"
    if any(w in text_lower for w in ["excited", "happy", "great", "amazing"]):
        return "excited"
    if any(w in text_lower for w in ["confused", "lost", "don't understand"]):
        return "confused"
    if any(w in text_lower for w in ["tired", "exhausted", "burnt out"]):
        return "tired"
    if any(w in text_lower for w in ["playful", "joking", "haha", "lol", "lmao"]):
        return "playful"

    return None


# In-memory storage for session states (keyed by room_id)
_session_states: dict[str, SessionState] = {}


def get_session_state(room_id: str) -> SessionState:
    """Get or create a session state for a room."""
    if room_id not in _session_states:
        _session_states[room_id] = SessionState()
    return _session_states[room_id]


def clear_session_state(room_id: str) -> None:
    """Clear session state for a room."""
    if room_id in _session_states:
        del _session_states[room_id]
