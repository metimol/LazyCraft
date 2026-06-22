import json
import logging

from ai.config import model


async def generate_optimized_queries(user_query: str) -> list[str]:
    """
    Generates 1 to 5 highly optimized search queries for Kleinanzeigen based on user input.
    Returns a JSON list of strings.
    """

    # TODO: Make better search phrases
    sys_prompt = (
        "You are an expert at searching Kleinanzeigen (a German classifieds site). "
        "Based on the user's input, generate 1 to 5 short, highly optimized search queries "
        "that would yield the best results on the platform. "
        "Output ONLY a raw JSON array of strings. Do not use markdown code blocks or any other text. "
        'Example: ["iphone 13 pro", "apple iphone 13", "iphone 13"]'
    )

    response = await model.ainvoke(
        [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_query},
        ]
    )

    content = response.content

    # TODO: Remove logging after first release
    logging.info(content)

    if isinstance(content, list):
        content = "".join(
            [str(p.get("text", "")) for p in content if p.get("type") == "text"]
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
            return queries[:5]
    except Exception:
        pass

    return [user_query]


async def filter_best_items(items_list: list[dict], original_query: str) -> list[str]:
    """
    Takes a list of stripped down items and returns a JSON array of the best matching item IDs.
    """
    if not items_list:
        return []

    items_json = json.dumps(items_list, ensure_ascii=False)
    sys_prompt = (
        "You are an expert filter for Kleinanzeigen. "
        f"The user originally searched for: '{original_query}'. "
        "Review the following JSON list of items. Pick the best matching items (up to 10) "
        "that match the user's intent. "
        "Output ONLY a raw JSON array of the string IDs of the chosen items. Do not use markdown code blocks."
        'Example: ["1234567", "89101112"]'
    )

    # Chunking might be needed if items_json is too large, but model supports 8k+ tokens
    response = await model.ainvoke(
        [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": items_json},
        ]
    )

    content = response.content
    if isinstance(content, list):
        content = "".join(
            [str(p.get("text", "")) for p in content if p.get("type") == "text"]
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
    except Exception:
        pass

    return [str(i["id"]) for i in items_list[:10]]
