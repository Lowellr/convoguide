"""SeriousModeAgent tool - makes responses grounded, structured, and serious."""

from livekit.agents import llm
from typing import Annotated, Optional, Literal
import openai

from ..prompts.specialists import SERIOUS_AGENT_PROMPT


@llm.function_tool
async def serious_style(
    base_message: Annotated[str, "The draft reply to make more serious"],
    conversation_context: Annotated[str, "Recent conversation for context"],
    focus: Annotated[
        Optional[Literal["analysis", "advice", "step_by_step"]],
        "Optional hint for how to structure the response"
    ] = None,
) -> str:
    """Make a reply more grounded, thoughtful, and serious, focusing on clarity and structure."""

    client = openai.AsyncOpenAI()

    user_content = f"""base_message: {base_message}

conversation_context: {conversation_context}"""

    if focus:
        user_content += f"\n\nfocus: {focus}"

    user_content += "\n\nTransform the base_message to be more serious and structured."

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SERIOUS_AGENT_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.5,
        max_tokens=500,
    )

    return response.choices[0].message.content or base_message
