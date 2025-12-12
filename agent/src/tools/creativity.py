"""CreativityAgent tool - generates ideas, names, metaphors, and variations."""

from livekit.agents import llm
from typing import Annotated, Literal
import openai

from ..prompts.specialists import CREATIVITY_AGENT_PROMPT


@llm.function_tool
async def creativity_style(
    prompt: Annotated[str, "Description of what the user is working on"],
    output_type: Annotated[
        Literal["ideas", "names", "metaphors", "variations", "twists"],
        "What kind of creative help is needed"
    ],
) -> str:
    """Generate or transform content with extra creativity: ideas, metaphors, names, variations."""

    client = openai.AsyncOpenAI()

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": CREATIVITY_AGENT_PROMPT},
            {
                "role": "user",
                "content": f"""prompt: {prompt}

output_type: {output_type}

Generate creative options for this request.""",
            },
        ],
        temperature=0.95,
        max_tokens=600,
    )

    return response.choices[0].message.content or "Here are some ideas..."
