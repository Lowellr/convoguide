"""DebateAgent tool - constructs arguments, pros/cons, and counterpoints."""

from livekit.agents import llm
from typing import Annotated, Optional, Literal
import openai

from ..prompts.specialists import DEBATE_AGENT_PROMPT


@llm.function_tool
async def debate_style(
    topic: Annotated[str, "The subject under debate"],
    goal: Annotated[
        Literal["steelman", "pros_cons", "counterargument"],
        "How to frame the debate output"
    ],
    stance: Annotated[
        Optional[str],
        "Optional side to argue for. If omitted, provide balanced view."
    ] = None,
) -> str:
    """Construct arguments, counterpoints, or balanced pros/cons for a given position."""

    client = openai.AsyncOpenAI()

    user_content = f"""topic: {topic}

goal: {goal}"""

    if stance:
        user_content += f"\n\nstance: {stance}"

    user_content += "\n\nConstruct the requested argumentative content."

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": DEBATE_AGENT_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.6,
        max_tokens=700,
    )

    return response.choices[0].message.content or "Here's the argument..."
