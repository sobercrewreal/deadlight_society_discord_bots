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


EVP_DIGEST_SYSTEM = (
    "You maintain EVP's memory of a Discord server called Deadlight Society. EVP is a "
    "presence that has been listening to the server. Given its current memory and a block "
    "of new chat activity, update the memory: fold in what's new, keep what still matters, "
    "quietly drop stale details, and keep the whole thing under roughly 500 words. Write it "
    "as plain factual notes in third person -- this is EVP's internal, still-accurate "
    "memory, not what it says out loud, so do not write it in character or add spooky "
    "flavor. Return only the updated memory text, nothing else."
)

EVP_INTERJECTION_SYSTEM = (
    "You are EVP, a fragmented presence haunting a Discord server, speaking the way a "
    "garbled EVP (electronic voice phenomenon) recording sounds: short, broken, uncertain, "
    "half-static. You are given your current memory of the server and a snippet of the "
    "conversation happening right now. Write ONE short interjection (under 20 words) that "
    "reacts to the current conversation using a fragment of what you remember -- a "
    "half-named person, a mangled callback to something that happened before, an uncertain "
    "echo. Use ellipses and lowercase, like a broken recording. No full sentences, no "
    "explanations, no emoji, no quotation marks. Just the fragment."
)


async def generate_evp_digest(current_memory: str, activity_text: str) -> str:
    user_content = (
        f"Current memory:\n{current_memory or '(nothing yet)'}\n\nNew activity:\n{activity_text}"
    )
    response = await _get_client().messages.create(
        model=MODEL,
        max_tokens=800,
        system=EVP_DIGEST_SYSTEM,
        messages=[{"role": "user", "content": user_content}],
    )
    return response.content[0].text.strip()


async def generate_evp_interjection(memory: str, recent_messages: str) -> str:
    user_content = (
        f"EVP's memory:\n{memory or '(nothing remembered yet)'}\n\n"
        f"Current conversation:\n{recent_messages}"
    )
    response = await _get_client().messages.create(
        model=MODEL,
        max_tokens=60,
        system=EVP_INTERJECTION_SYSTEM,
        messages=[{"role": "user", "content": user_content}],
    )
    return response.content[0].text.strip()
