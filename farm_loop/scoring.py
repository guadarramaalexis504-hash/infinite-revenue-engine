from __future__ import annotations

from html import unescape
from re import sub
from typing import Iterable


RELEVANT_TAGS = {
    "python",
    "fastapi",
    "supabase",
    "openai-api",
    "github-actions",
    "requests",
    "postgresql",
    "rest",
}


def _plain_text(value: str | None) -> str:
    if not value:
        return ""
    without_code_tags = sub(r"</?(pre|code)[^>]*>", " ", value, flags=2)
    without_tags = sub(r"<[^>]+>", " ", without_code_tags)
    return " ".join(unescape(without_tags).split())


def _has_code(value: str | None) -> bool:
    if not value:
        return False
    lower = value.lower()
    return "<code" in lower or "```" in lower or "traceback" in lower


def score_question(question: dict) -> int:
    score = 0

    answer_count = int(question.get("answer_count") or 0)
    if answer_count == 0:
        score += 25
    elif answer_count == 1:
        score += 8

    if not question.get("is_answered") and not question.get("accepted_answer_id"):
        score += 15

    views = int(question.get("view_count") or 0)
    if views >= 150:
        score += 15
    elif views >= 50:
        score += 10
    elif views >= 15:
        score += 5

    tags = {str(tag).lower() for tag in question.get("tags") or []}
    score += min(24, 8 * len(tags & RELEVANT_TAGS))

    title = _plain_text(str(question.get("title") or ""))
    body = _plain_text(str(question.get("body") or question.get("body_markdown") or ""))
    if 35 <= len(title) <= 140:
        score += 8
    if len(body) >= 80:
        score += 10
    if _has_code(question.get("body") or question.get("body_markdown")):
        score += 8

    platform_score = int(question.get("score") or 0)
    score += max(-10, min(10, platform_score * 2))

    return max(0, min(100, score))


def rank_questions(
    questions: Iterable[dict],
    *,
    max_items: int = 3,
    min_score: int = 50,
    seen_external_ids: set[str] | None = None,
) -> list[dict]:
    seen = set(seen_external_ids or set())
    unique: list[tuple[int, int, dict]] = []

    for index, question in enumerate(questions):
        external_id = str(question.get("question_id") or "")
        if not external_id or external_id in seen:
            continue
        seen.add(external_id)
        question_score = score_question(question)
        if question_score < min_score:
            continue
        enriched = dict(question)
        enriched["farm_score"] = question_score
        unique.append((question_score, -index, enriched))

    unique.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [item[2] for item in unique[:max_items]]


def to_opportunity_payload(question: dict, score: int | None = None) -> dict:
    question_score = score if score is not None else score_question(question)
    return {
        "source": "stackexchange",
        "external_id": str(question["question_id"]),
        "title": str(question.get("title") or ""),
        "url": str(question.get("link") or question.get("share_link") or ""),
        "tags": list(question.get("tags") or []),
        "score": int(question_score),
        "status": "new",
    }
