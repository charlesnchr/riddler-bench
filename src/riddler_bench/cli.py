from __future__ import annotations

import csv
import os
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import typer
from rich import print
from rich.table import Table

from .config import load_providers_config, resolve_model_specs
from .dataset import QAItem, load_dataset
from .evaluate import append_jsonl, ensure_dir, grade_answer, summarize_results
from .models import ask_question, build_chat_model
from .parallel_evaluate import create_parallel_evaluator

app = typer.Typer(add_completion=False, no_args_is_help=True)


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


@app.command()
def eval(
    dataset: str = typer.Option(..., help="Path to JSONL dataset"),
    config: str = typer.Option(..., help="Path to models YAML config"),
    models: Optional[str] = typer.Option(
        None, help="CSV of provider:model_id (defaults to all in config)"
    ),
    out: str = typer.Option(
        None, help="Output directory for results (default results/<timestamp>)"
    ),
    fuzzy_threshold: int = typer.Option(85, help="Fuzzy match threshold 0-100"),
    temperature: float = typer.Option(0.0, help="Model sampling temperature"),
):
    cfg = load_providers_config(config)
    specs = resolve_model_specs(cfg, models)
    items = load_dataset(dataset)

    out_dir = out or f"results/{_timestamp()}"
    ensure_dir(out_dir)

    print(f"[bold]Models:[/bold] {[s.display_name for s in specs]}")
    print(f"[bold]Dataset:[/bold] {dataset} ({len(items)} items)")
    print(f"[bold]Writing to:[/bold] {out_dir}")

    summary_rows: List[dict] = []

    for spec in specs:
        llm = build_chat_model(spec, temperature=temperature)
        model_key = spec.display_name
        out_path = Path(out_dir) / f"{model_key.replace('/', '_').replace(':', '_')}.jsonl"

        rows: List[dict] = []
        start_time = time.time()
        for item in items:
            t0 = time.time()
            try:
                answer = ask_question(llm, item.question)
            except Exception as e:
                answer = f"<error: {e}>"
            latency_ms = int((time.time() - t0) * 1000)

            g = grade_answer(item, answer, fuzzy_threshold=fuzzy_threshold)
            row = {
                "id": item.id,
                "question": item.question,
                "answer_ref": item.answer,
                "aliases": item.aliases or [],
                "model": model_key,
                "answer": answer,
                "latency_ms": latency_ms,
                "is_exact": g.is_exact,
                "is_alias": g.is_alias,
                "fuzzy": g.fuzzy,
                "is_correct": g.is_correct,
            }
            rows.append(row)
            append_jsonl(out_path, row)

        elapsed = int(time.time() - start_time)
        stats = summarize_results(rows)
        stats.update({"model": model_key, "elapsed_s": elapsed})
        summary_rows.append(stats)

    # Write summary CSV
    summary_csv = Path(out_dir) / "summary.csv"
    with open(summary_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["model", "total", "correct", "accuracy", "exact", "alias", "avg_fuzzy", "elapsed_s"]
        )
        writer.writeheader()
        writer.writerows(summary_rows)

    # Pretty print
    table = Table(title="Results Summary")
    for col in ["model", "total", "correct", "accuracy", "exact", "alias", "avg_fuzzy", "elapsed_s"]:
        table.add_column(col)
    for r in summary_rows:
        table.add_row(
            str(r["model"]),
            str(r["total"]),
            str(r["correct"]),
            f"{r['accuracy']:.3f}",
            str(r["exact"]),
            str(r["alias"]),
            str(r["avg_fuzzy"]),
            str(r["elapsed_s"]),
        )
    print(table)


@app.command()
def score(
    results: str = typer.Option(..., help="Path to a results folder with *.jsonl"),
):
    from pathlib import Path
    import json

    rows_by_model: dict[str, list[dict]] = {}

    for p in Path(results).glob("*.jsonl"):
        model_key = p.stem.replace("_", "/")
        rows: list[dict] = []
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                rows.append(json.loads(line))
        rows_by_model[model_key] = rows

    table = Table(title=f"Scored: {results}")
    for col in ["model", "total", "correct", "accuracy", "exact", "alias", "avg_fuzzy"]:
        table.add_column(col)

    for model_key, rows in rows_by_model.items():
        stats = summarize_results(rows)
        table.add_row(
            model_key,
            str(stats["total"]),
            str(stats["correct"]),
            f"{stats['accuracy']:.3f}",
            str(stats["exact"]),
            str(stats["alias"]),
            str(stats["avg_fuzzy"]),
        )

    print(table)


@app.command()
def eval_parallel(
    dataset: str = typer.Option(..., help="Path to JSONL dataset"),
    config: str = typer.Option(..., help="Path to models YAML config"),
    models: Optional[str] = typer.Option(
        None, help="CSV of provider:model_id (defaults to all in config)"
    ),
    out: str = typer.Option(
        None, help="Output directory for results (default results/<timestamp>)"
    ),
    fuzzy_threshold: int = typer.Option(85, help="Fuzzy match threshold 0-100"),
    temperature: float = typer.Option(0.0, help="Model sampling temperature"),
    azure_workers: int = typer.Option(20, help="Parallel workers for Azure models"),
    groq_workers: int = typer.Option(2, help="Parallel workers for Groq models"),
    openrouter_workers: int = typer.Option(5, help="Parallel workers for OpenRouter models"),
):
    """Run evaluation with parallel processing for faster execution."""
    cfg = load_providers_config(config)
    specs = resolve_model_specs(cfg, models)
    items = load_dataset(dataset)

    out_dir = out or f"results/{_timestamp()}"
    ensure_dir(out_dir)

    print(f"[bold]Models:[/bold] {[s.display_name for s in specs]}")
    print(f"[bold]Dataset:[/bold] {dataset} ({len(items)} items)")
    print(f"[bold]Writing to:[/bold] {out_dir}")
    print(f"[bold]Concurrency:[/bold] Azure: {azure_workers}, Groq: {groq_workers}, OpenRouter: {openrouter_workers}")

    # Configure parallel evaluator
    provider_concurrency = {
        "azure_openai": azure_workers,
        "groq": groq_workers,
        "openrouter": openrouter_workers,
    }
    
    evaluator = create_parallel_evaluator()
    evaluator.provider_concurrency = provider_concurrency

    # Run parallel evaluation
    summary_rows = evaluator.evaluate_all_models(
        specs, items, out_dir, fuzzy_threshold, temperature
    )

    # Write summary CSV
    summary_csv = Path(out_dir) / "summary.csv"
    with open(summary_csv, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["model", "total", "correct", "accuracy", "exact", "alias", "avg_fuzzy", "elapsed_s"]
        if any("error" in row for row in summary_rows):
            fieldnames.append("error")
            
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary_rows)

    # Pretty print results
    table = Table(title="Parallel Evaluation Results")
    for col in ["model", "total", "correct", "accuracy", "exact", "alias", "avg_fuzzy", "elapsed_s"]:
        table.add_column(col)
    
    for r in summary_rows:
        if "error" not in r:
            table.add_row(
                str(r["model"]),
                str(r["total"]),
                str(r["correct"]),
                f"{r['accuracy']:.3f}",
                str(r["exact"]),
                str(r["alias"]),
                str(r["avg_fuzzy"]),
                str(r["elapsed_s"]),
            )
        else:
            table.add_row(
                str(r["model"]),
                str(r["total"]),
                "ERROR",
                "0.000",
                "0",
                "0", 
                "0.0",
                "0",
            )
    print(table) 