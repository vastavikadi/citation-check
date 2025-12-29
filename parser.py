import re
from typing import Dict

def normalize_text_spacing(text: str) -> str:
    text = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', text)

    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)

    text = re.sub(r'\.(?=[A-Za-z])', '. ', text)

    text = re.sub(r'\s+', ' ', text)

    return text.strip()

def smart_parse_citation(raw: str) -> dict:
    """
    Attempts to extract structured metadata from a noisy citation string.
    """
    refined_raw = normalize_text_spacing(raw)

    result = {
        "raw": refined_raw,
        "authors": None,
        "title": None,
        "year": None,
        "confidence": 0.0
    }

    text = refined_raw.strip()

    year_match = re.search(r"(19|20)\d{2}", text)
    if year_match:
        result["year"] = year_match.group()
        result["confidence"] += 0.2

    quote_match = re.search(r'"([^"]{5,})"', text)
    if quote_match:
        result["title"] = quote_match.group(1).strip()
        result["confidence"] += 0.4
    else:
        parts = re.split(r"\b(19|20)\d{2}\b", text)
        if len(parts) > 1:
            left = parts[0]
            chunks = left.split(",")
            if len(chunks) > 1:
                candidate = chunks[-1].strip()
                if len(candidate.split()) >= 3:
                    result["title"] = candidate
                    result["confidence"] += 0.25

    author_match = re.match(r"^([^.,]+(?:, [^.,]+)*)", text)
    if author_match:
        authors = author_match.group(1)
        if len(authors.split()) <= 12:
            result["authors"] = authors.strip()
            result["confidence"] += 0.2

    result["confidence"] = round(min(result["confidence"], 1.0), 2)

    return result
