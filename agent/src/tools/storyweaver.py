"""StoryWeaverAgent tool - creates narratives, scenes, and stories."""

from livekit.agents import llm
from typing import Annotated, Literal
import openai

from ..prompts.specialists import STORYWEAVER_AGENT_PROMPT


@llm.function_tool
async def storyweaver_style(
    prompt: Annotated[str, "High-level idea or situation to narrativize"],
    story_goal: Annotated[
        Literal["funny_anecdote", "short_fable", "tiny_scene", "character_intro"],
        "The type of story to create"
    ] = "tiny_scene",
) -> str:
    """Turn ideas into short stories, scenes, or narrative snippets in a chosen style."""

    client = openai.AsyncOpenAI()

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": STORYWEAVER_AGENT_PROMPT},
            {
                "role": "user",
                "content": f"""prompt: {prompt}

story_goal: {story_goal}

Create a short story or scene that fulfills this goal.""",
            },
        ],
        temperature=0.9,
        max_tokens=800,
    )

    return response.choices[0].message.content or "Once upon a time..."
