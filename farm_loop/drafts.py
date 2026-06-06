from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import requests


OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"


@dataclass(frozen=True)
class Draft:
    answer_markdown: str
    code_snippet: str
    raw_response: dict[str, Any]


class DraftGenerator:
    def __init__(
        self,
        api_key: str,
        *,
        model: str = "gpt-4o-mini",
        session: Any | None = None,
        timeout: int = 45,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.session = session or requests.Session()
        self.timeout = timeout

    def generate(self, question: dict, *, tip_url: str) -> Draft:
        payload = {
            "model": self.model,
            "instructions": (
                "Draft a concise, technically correct Stack Overflow style answer. "
                "Do not claim you executed the code. Do not pressure the reader to pay. "
                "Return only JSON with answer_markdown and code_snippet."
            ),
            "input": self._build_input(question, tip_url),
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "technical_answer_draft",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["answer_markdown", "code_snippet"],
                        "properties": {
                            "answer_markdown": {"type": "string"},
                            "code_snippet": {"type": "string"},
                        },
                    },
                }
            },
        }
        response = self.session.post(
            OPENAI_RESPONSES_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self.timeout,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"OpenAI response failed: {response.status_code} {response.text}")
        raw = response.json()
        parsed = self._parse_response_json(raw)
        return Draft(
            answer_markdown=str(parsed.get("answer_markdown") or ""),
            code_snippet=str(parsed.get("code_snippet") or ""),
            raw_response=raw,
        )

    def _build_input(self, question: dict, tip_url: str) -> str:
        return "\n".join(
            [
                f"Question title: {question.get('title', '')}",
                f"Question URL: {question.get('link') or question.get('share_link') or ''}",
                f"Tags: {', '.join(question.get('tags') or [])}",
                "Question body:",
                str(question.get("body") or question.get("body_markdown") or ""),
                "",
                "If appropriate, end with this unobtrusive sentence exactly once:",
                f"If this saved you time, optional support is here: {tip_url}",
            ]
        )

    def _parse_response_json(self, raw: dict[str, Any]) -> dict[str, Any]:
        if raw.get("output_text"):
            return json.loads(raw["output_text"])

        for item in raw.get("output") or []:
            for content in item.get("content") or []:
                text = content.get("text")
                if text:
                    return json.loads(text)
        raise RuntimeError("OpenAI response did not include JSON text output")
