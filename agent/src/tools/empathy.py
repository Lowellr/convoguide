"""EmpathyAgent tool - adds emotional sensitivity and validation."""

from livekit.agents import llm
from typing import Annotated, Optional
import openai

from ..prompts.specialists import EMPATHY_AGENT_PROMPT


@llm.function_tool
async def empathy_style(
    base_message: Annotated[str, "The factual/helpful reply to transform"],
    conversation_context: Annotated[str, "Recent conversation including user feelings"],
    emotion_hint: Annotated[
        Optional[str],
        "Optional emotion label (e.g., sad, anxious, frustrated, excited)"
    ] = None,
) -> str:
    """Transform a reply to be more emotionally attuned and validating while staying honest."""

    client = openai.AsyncOpenAI()

    user_content = f"""base_message: {base_message}

conversation_context: {conversation_context}"""

    if emotion_hint:
        user_content += f"\n\nemotion_hint: {emotion_hint}"

    user_content += "\n\nTransform the base_message to be more emotionally sensitive and validating."

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": EMPATHY_AGENT_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.7,
        max_tokens=500,
    )

    return response.choices[0].message.content or base_message
