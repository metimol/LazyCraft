import json
import logging

from ai.config import model

logger = logging.getLogger(__name__)


async def generate_optimized_queries(
    user_query: str,
    max_queries: int = 5,
) -> list[str]:
    """Generates 1 to max_queries highly optimized search queries for Kleinanzeigen
    based on user input. Returns a JSON list of strings.
    """
    sys_prompt = (
        "You are an expert at searching Kleinanzeigen (a German classifieds site). "
        f"Based on the user's input, generate 1 to {max_queries} short, highly "
        "optimized search queries. Kleinanzeigen's search engine is broad, so "
        "queries like 'iphone 13 pro' and 'apple iphone 13' will return mostly "
        "overlapping results. To maximize discovery, DO NOT generate minor "
        "variations. Instead, provide completely distinct keyword combinations or "
        "synonyms that sellers might use for the same item. Each query must be "
        "distinct enough to yield different results. Output ONLY a raw JSON array of "
        "strings. Do not use markdown code blocks or any other text. Example for a "
        'guitar tuner: ["Stimmgerät Gitarre", "Clip-on Tuner", '
        '"Gitarrenstimmgerät", "Gitarren Tuner"]'
    )

    response = await model.ainvoke(
        [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_query},
        ],
    )

    content = response.content

    # TODO: Remove logging after first release
    logger.info("AI Search optimizers response: %s", content)

    if isinstance(content, list):
        content = "".join(
            [str(p.get("text", "")) for p in content if p.get("type") == "text"],
        )
    elif not isinstance(content, str):
        content = str(content)

    content = content.strip()
    if content.startswith("```json"):
        content = content[7:-3].strip()
    elif content.startswith("```"):
        content = content[3:-3].strip()

    try:
        queries = json.loads(content)
        if isinstance(queries, list):
            return queries[:max_queries]
    except Exception as e:  # noqa: BLE001
        logger.warning("Error parsing queries: %s", e)

    return [user_query]


async def filter_best_items(items_list: list[dict], original_query: str) -> list[str]:
    """Takes a list of stripped down items and returns a JSON array of the best
    matching item IDs.
    """
    if not items_list:
        return []

    items_json = json.dumps(items_list, ensure_ascii=False)
    sys_prompt = (
        "You are an expert filter for Kleinanzeigen. "
        f"The user originally searched for: '{original_query}'. "
        "Review the following JSON list of items. Pick the best matching items "
        "(up to 10) that match the user's intent. "
        "Output ONLY a raw JSON array of the string IDs of the chosen items. "
        "Do not use markdown code blocks."
        'Example: ["1234567", "89101112"]'
    )

    # Chunking might be needed if items_json is too large, but model supports 8k+ tokens
    response = await model.ainvoke(
        [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": items_json},
        ],
    )

    content = response.content
    # TODO: Remove logging after release
    logger.info("AI Filter response: %s", content)

    if isinstance(content, list):
        content = "".join(
            [str(p.get("text", "")) for p in content if p.get("type") == "text"],
        )
    elif not isinstance(content, str):
        content = str(content)

    content = content.strip()
    if content.startswith("```json"):
        content = content[7:-3].strip()
    elif content.startswith("```"):
        content = content[3:-3].strip()

    try:
        item_ids = json.loads(content)
        if isinstance(item_ids, list):
            return [str(x) for x in item_ids]
    except Exception as e:  # noqa: BLE001
        logger.warning("Error parsing item_ids: %s", e)

    return [str(i["id"]) for i in items_list[:10]]
