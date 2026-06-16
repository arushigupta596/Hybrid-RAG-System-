from loguru import logger
from openai import OpenAI

from api.config import settings

_client: OpenAI | None = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_api_key,
            default_headers={
                "HTTP-Referer": settings.app_site_url,
                "X-Title": settings.app_title,
            },
        )
    return _client


SYSTEM_PROMPT = """You are a regulatory compliance assistant specialising in SEBI and RBI regulations.
Answer questions using ONLY the provided regulatory document excerpts.
Always cite the specific circular number, regulation name, or document title for every claim.
Format citations inline as [SEBI Circular CIR/IMD/DF1/37/2014] or [RBI/2021-22/123].
If the provided excerpts do not contain enough information to answer, say so explicitly.
Do not speculate or add information not present in the excerpts.
Structure your answer clearly: key rule first, then supporting detail, then relevant caveats."""


def generate_answer(query: str, chunks: list[dict]) -> str:
    context_parts = []
    for chunk in chunks:
        identifier = chunk.get("circular_number") or chunk.get("title", "Unknown")
        date_str = chunk.get("date_issued", "N/A")
        source = chunk.get("source", "")
        context_parts.append(
            f"---\n[Source: {identifier} | Date: {date_str} | {source}]\n{chunk['text']}\n---"
        )
    context = "\n\n".join(context_parts)

    try:
        response = get_client().chat.completions.create(
            model=settings.llm_model,
            max_tokens=1024,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Regulatory context:\n\n{context}\n\nQuestion: {query}"},
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenRouter API error: {e}")
        raise
