from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from rapidfuzz import fuzz

from .dataset import QAItem, normalize_text


@dataclass
class Grade:
    is_exact: bool
    is_alias: bool
    fuzzy: int
    is_correct: bool


def grade_answer(
    item: QAItem, prediction: str, fuzzy_threshold: int = 85
) -> Grade:
    gold = normalize_text(item.answer)
    pred = normalize_text(prediction)

    is_exact = pred == gold and len(pred) > 0

    aliases = item.aliases or []
    alias_norms = {normalize_text(a) for a in aliases}

    is_alias = pred in alias_norms

    # Fuzzy against answer and aliases
    fuzzy_scores = [
        fuzz.token_set_ratio(pred, gold),
        *[fuzz.token_set_ratio(pred, a) for a in alias_norms],
    ]
    fuzzy_score = max(fuzzy_scores) if fuzzy_scores else 0

    is_correct = bool(is_exact or is_alias or fuzzy_score >= fuzzy_threshold)

    return Grade(
        is_exact=is_exact,
        is_alias=is_alias,
        fuzzy=int(fuzzy_score),
        is_correct=is_correct,
    )


def ensure_dir(path: str | Path) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


def write_jsonl(path: str | Path, rows: Iterable[Dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def append_jsonl(path: str | Path, row: Dict) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def summarize_results(rows: List[Dict]) -> Dict:
    total = len(rows)
    correct = sum(1 for r in rows if r.get("is_correct"))
    exact = sum(1 for r in rows if r.get("is_exact"))
    alias = sum(1 for r in rows if r.get("is_alias"))
    avg_fuzzy = round(sum(int(r.get("fuzzy", 0)) for r in rows) / max(total, 1), 1)
    return {
        "total": total,
        "correct": correct,
        "accuracy": round(correct / total, 3) if total else 0.0,
        "exact": exact,
        "alias": alias,
        "avg_fuzzy": avg_fuzzy,
    } 