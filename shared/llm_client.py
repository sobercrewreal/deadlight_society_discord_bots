import os

from anthropic import AsyncAnthropic

MODEL = "claude-haiku-4-5-20251001"

REAL_PROMPT = (
    "Write a short, atmospheric retelling (150-220 words) of a real, well-documented "
    "paranormal or \"true ghost story\" case from history (a famous haunting, poltergeist "
    "case, or EVP recording). Base it on an actual documented case and keep the core facts "
    "(names, places, events) accurate to what's publicly known about it. Write in "
    "second-person campfire-story tone, no title, no meta-commentary, no disclaimers, just "
    "the story."
)

FAKE_PROMPT = (
    "Write a short, atmospheric, entirely fictional ghost story (150-220 words) in the same "
    "campfire-story tone as a real documented haunting case, but fully invented -- no real "
    "people, places, or documented events. It should be plausible enough to pass as a real "
    "case to someone unfamiliar with paranormal history. No title, no meta-commentary, no "
    "disclaimers, just the story."
)

_client = None


def _get_client() -> AsyncAnthropic:
    global _client
    if _client is None:
        _client = AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


async def generate_story(is_real: bool) -> str:
    prompt = REAL_PROMPT if is_real else FAKE_PROMPT
    response = await _get_client().messages.create(
        model=MODEL,
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()
