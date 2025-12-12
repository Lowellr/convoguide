"""HumorAgent tool - adds wit, jokes, and playful tone."""

from livekit.agents import llm
from typing import Annotated, Literal
import openai

from ..prompts.specialists import HUMOR_AGENT_PROMPT


@llm.function_tool
async def humor_style(
    base_message: Annotated[str, "The straightforward reply before adding humor"],
    conversation_context: Annotated[str, "Recent conversation turns for context"],
    humor_level: Annotated[
        Literal["subtle", "moderate", "goofy"],
        "Intensity of humor. Default: subtle"
    ] = "subtle",
) -> str:
    """Punch up a reply with light, user-appropriate humor, wit, or playful tone."""

    client = openai.AsyncOpenAI()

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": HUMOR_AGENT_PROMPT},
            {
                "role": "user",
                "content": f"""base_message: {base_message}

conversation_context: {conversation_context}

humor_level: {humor_level}

Transform the base_message with the appropriate level of humor.""",
            },
        ],
        temperature=0.8,
        max_tokens=500,
    )

    return response.choices[0].message.content or base_message
