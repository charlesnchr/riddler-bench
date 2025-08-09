from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class QAItem:
    id: str
    question: str
    answer: str
    aliases: Optional[List[str]] = None
    category: Optional[str] = None


def load_dataset(path: str) -> List[QAItem]:
    items: List[QAItem] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            raw = json.loads(line)
            items.append(
                QAItem(
                    id=str(raw["id"]),
                    question=raw["question"],
                    answer=raw["answer"],
                    aliases=raw.get("aliases"),
                    category=raw.get("category"),
                )
            )
    return items


_ARTICLE_RE = re.compile(r"\b(a|an|the)\b", flags=re.IGNORECASE)
_PUNCT_RE = re.compile(r"[^\w\s]")
_WS_RE = re.compile(r"\s+")


def normalize_text(text: str) -> str:
    t = text.strip().lower()
    t = _ARTICLE_RE.sub(" ", t)
    t = _PUNCT_RE.sub(" ", t)
    t = _WS_RE.sub(" ", t)
    return t.strip() 