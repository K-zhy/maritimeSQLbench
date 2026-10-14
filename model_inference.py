from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from benchmark import ROOT, gold_context, load_examples, parse_single_query, select_examples


DEFAULT_BASE_URL = "https://api.openai.com/v1"
PROMPT_PREFIX = """你是一名严谨的 PostgreSQL Text-to-SQL 生成器，擅长航运与调度类数据库的查询编写。
你将收到 Database Schema 与 用户问题。你的唯一任务：基于 Schema 生成一条可直接执行、语法与类型均正确的 PostgreSQL 查询语句，用于回答该问题。

【绝对规则（必须遵守）】
1. 只输出 SQL
- 输出中不得包含解释、推理过程、注释、JSON、Markdown 代码块符号（如 ```），或除 SQL 以外的任何字符。

2. Schema 约束
- 只使用 Database Schema 中存在的表与字段；字段名与表名必须精确匹配（注意大小写 与下划线）。

3. 字段类型匹配（避免 "operator does not exist: varchar = integer" 等错误）
- 严格遵守 Schema 中列出的字段类型，避免类型不匹配导致的运行时错误。

4. 文本匹配策略（仅在文本列上使用）
- 模糊匹配：LIKE '%keyword%' 或不区分大小写：ILIKE '%keyword%'。

【你在内部遵循但不要输出的生成流程】
- 读取 Database Schema → 仅选用存在的表/列
- 明确每个被用到的列的数据类型

【输入格式】
- Database Schema：包含表名、列名、列类型、主外键关系与必要索引信息。
- 用户自然语言问题。

【输出格式（唯一允许）】
- 仅输出一条可执行的 PostgreSQL 查询语句（不含注释/解释/JSON/Markdown）。
"""


def build_messages(example: dict[str, Any]) -> list[dict[str, str]]:
    user = (
        f"Database Schema：\n{gold_context(example)}\n\n"
        f"用户自然语言问题：\n{example['query']}"
    )
    return [
        {"role": "system", "content": PROMPT_PREFIX},
        {"role": "user", "content": user},
    ]


def extract_sql(content: str) -> str:
    fenced = re.search(r"```(?:sql)?\s*(.*?)```", content, flags=re.IGNORECASE | re.DOTALL)
    sql = fenced.group(1) if fenced else content
    sql = sql.strip()
    if sql.lower().startswith("sql:"):
        sql = sql[4:].strip()
    return sql


def call_chat_completions(
    *,
    base_url: str,
    api_key: str,
    model: str,
    messages: list[dict[str, str]],
    temperature: float,
    timeout: float,
) -> str:
    payload = json.dumps(
        {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"model API returned HTTP {error.code}: {detail}") from error
    return extract_sql(result["choices"][0]["message"]["content"])


def load_existing(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError("existing predictions must be a JSON array")
    return {
        item["question_id"]: item
        for item in value
        if isinstance(item, dict) and isinstance(item.get("question_id"), str)
    }


def write_predictions(path: Path, predictions: dict[str, dict[str, Any]]) -> None:
    ordered = sorted(predictions.values(), key=lambda item: item["question_id"])
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(ordered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def generate_prediction(
    example: dict[str, Any],
    *,
    base_url: str,
    api_key: str,
    model: str,
    temperature: float,
    timeout: float,
) -> dict[str, Any]:
    question_id = example["question_id"]
    try:
        sql = call_chat_completions(
            base_url=base_url,
            api_key=api_key,
            model=model,
            messages=build_messages(example),
            temperature=temperature,
            timeout=timeout,
        )
        parse_single_query(sql)
        return {"question_id": question_id, "sql": sql}
    except Exception as error:
        return {
            "question_id": question_id,
            "sql": "",
            "generation_error": f"{type(error).__name__}: {error}",
        }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate MaritimeSQLBench predictions with an OpenAI-compatible API."
    )
    parser.add_argument("--model", default=os.environ.get("MODEL_NAME"))
    parser.add_argument(
        "--base-url", default=os.environ.get("MODEL_BASE_URL", DEFAULT_BASE_URL)
    )
    parser.add_argument("--api-key-env", default="MODEL_API_KEY")
    parser.add_argument(
        "--evaluation-data",
        type=Path,
        default=ROOT / "evaluation_data_anonymized.json",
    )
    parser.add_argument("--output", type=Path, default=ROOT / "predictions.json")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument(
        "--workers",
        type=int,
        default=int(os.environ.get("MODEL_WORKERS", "1")),
        help="Number of concurrent model requests (default: 1).",
    )
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "--overwrite", action="store_true", help="Regenerate existing question IDs."
    )
    args = parser.parse_args()

    if not args.model:
        parser.error("--model or MODEL_NAME is required")
    if args.workers < 1:
        parser.error("--workers must be at least 1")
    api_key = os.environ.get(args.api_key_env)
    if not api_key:
        parser.error(f"environment variable {args.api_key_env} is required")

    try:
        examples = select_examples(load_examples(args.evaluation_data), args.limit)
    except ValueError as error:
        parser.error(str(error))
    predictions = load_existing(args.output)
    selected_ids = {example["question_id"] for example in examples}
    pending = [
        example
        for example in examples
        if args.overwrite
        or not predictions.get(example["question_id"], {}).get("sql")
    ]
    completed = len(examples) - len(pending)
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(
                generate_prediction,
                example,
                base_url=args.base_url,
                api_key=api_key,
                model=args.model,
                temperature=args.temperature,
                timeout=args.timeout,
            ): example["question_id"]
            for example in pending
        }
        for future in as_completed(futures):
            prediction = future.result()
            question_id = prediction["question_id"]
            predictions[question_id] = prediction
            completed += 1
            write_predictions(args.output, predictions)
            print(f"[{completed}/{len(examples)}] {question_id}", file=sys.stderr)

    write_predictions(args.output, predictions)
    failures = sum(
        question_id in selected_ids and not item.get("sql")
        for question_id, item in predictions.items()
    )
    print(
        json.dumps(
            {
                "model": args.model,
                "prediction_count": sum(
                    question_id in selected_ids for question_id in predictions
                ),
                "generation_failure_count": failures,
                "workers": args.workers,
                "output": str(args.output),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())