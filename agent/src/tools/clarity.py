"""ClarityAgent tool - simplifies and reframes content for clarity."""

from livekit.agents import llm
from typing import Annotated, Literal
import openai

from ..prompts.specialists import CLARITY_AGENT_PROMPT


@llm.function_tool
async def clarity_style(
    base_message: Annotated[str, "The content that needs to be clearer"],
    target_level: Annotated[
        Literal["child", "teen", "adult", "expert"],
        "Rough audience level to adapt to"
    ] = "adult",
) -> str:
    """Simplify or reframe content to be clearer and easier to understand."""

    client = openai.AsyncOpenAI()

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": CLARITY_AGENT_PROMPT},
            {
                "role": "user",
                "content": f"""base_message: {base_message}

target_level: {target_level}

Rewrite the message for clarity at this comprehension level.""",
            },
        ],
        temperature=0.5,
        max_tokens=500,
    )

    return response.choices[0].message.content or base_message
