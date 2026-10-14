from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable, Sequence

import psycopg
from sqlglot import exp, parse

from schema_anonymized import schema_dict


ROOT = Path(__file__).resolve().parent
PROHIBITED_NODES = (
    exp.Alter,
    exp.Command,
    exp.Create,
    exp.Delete,
    exp.Drop,
    exp.Insert,
    exp.Merge,
    exp.Transaction,
    exp.Update,
)
PROHIBITED_FUNCTIONS = {
    "dblink",
    "lo_export",
    "lo_import",
    "pg_ls_dir",
    "pg_read_binary_file",
    "pg_read_file",
    "pg_sleep",
}


@dataclass(frozen=True)
class ExecutionResult:
    columns: tuple[str, ...]
    rows: tuple[tuple[Any, ...], ...]


def load_examples(path: Path = ROOT / "evaluation_data_anonymized.json") -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as file:
        examples = json.load(file)
    if not isinstance(examples, list):
        raise ValueError("evaluation data must be a JSON array")
    return examples


def select_examples(
    examples: list[dict[str, Any]], limit: int | None
) -> list[dict[str, Any]]:
    if limit is None:
        return examples
    if limit < 1:
        raise ValueError("limit must be at least 1")
    if limit > len(examples):
        raise ValueError("limit must not exceed example count")
    return examples[:limit]


def parse_single_query(sql: str) -> exp.Query:
    statements = parse(sql, read="postgres")
    if len(statements) != 1 or not isinstance(statements[0], exp.Query):
        raise ValueError("exactly one read-only query is required")
    query = statements[0]
    if any(query.find(node_type) is not None for node_type in PROHIBITED_NODES):
        raise ValueError("data definition and modification statements are prohibited")
    for function in query.find_all(exp.Func):
        function_name = (
            function.name if isinstance(function, exp.Anonymous) else function.sql_name()
        )
        if function_name.lower() in PROHIBITED_FUNCTIONS:
            raise ValueError(f"prohibited function: {function_name}")
    return query


def referenced_tables(query: exp.Query) -> set[str]:
    cte_names = {cte.alias_or_name for cte in query.find_all(exp.CTE)}
    public_by_base = {name.rsplit(".", 1)[-1]: name for name in schema_dict}
    tables = set()
    for table in query.find_all(exp.Table):
        if table.name in cte_names:
            continue
        if table.db:
            name = f"{table.db}.{table.name}"
        else:
            name = public_by_base.get(table.name, table.name)
        tables.add(name)
    return tables


def validate_example(example: dict[str, Any]) -> exp.Query:
    query = parse_single_query(example["sql"])
    actual = referenced_tables(query)
    expected = set(example["table_names"])
    if actual != expected:
        raise ValueError(
            f"table metadata mismatch: expected {sorted(expected)}, got {sorted(actual)}"
        )
    missing_schema = expected - schema_dict.keys()
    if missing_schema:
        raise ValueError(f"missing schema context: {sorted(missing_schema)}")
    return query


def gold_context(example: dict[str, Any]) -> str:
    validate_example(example)
    return "\n\n".join(schema_dict[name] for name in example["table_names"])


def freeze_time(sql: str, snapshot_as_of: datetime) -> str:
    query = parse_single_query(sql)

    def replace_time(node: exp.Expression) -> exp.Expression:
        if isinstance(node, exp.CurrentDate):
            return exp.Cast(
                this=exp.Literal.string(snapshot_as_of.date().isoformat()),
                to=exp.DataType.build("date"),
            )
        if isinstance(node, exp.CurrentTimestamp):
            return exp.Cast(
                this=exp.Literal.string(snapshot_as_of.isoformat()),
                to=exp.DataType.build("timestamptz", dialect="postgres"),
            )
        return node

    return query.transform(replace_time).sql(dialect="postgres")


def normalize_value(value: Any) -> Any:
    if value is None:
        return ("null",)
    if isinstance(value, Decimal):
        return ("decimal", value.normalize().as_tuple())
    if isinstance(value, float):
        if math.isnan(value):
            return ("float", "nan")
        return ("float", round(value, 9))
    if isinstance(value, (datetime, date, time)):
        return (type(value).__name__, value.isoformat())
    if isinstance(value, (dict, list)):
        return ("json", json.dumps(value, ensure_ascii=False, sort_keys=True))
    if isinstance(value, memoryview):
        return ("bytes", bytes(value))
    return (type(value).__name__, value)


def normalize_rows(rows: Iterable[Sequence[Any]]) -> Counter[tuple[Any, ...]]:
    return Counter(tuple(normalize_value(value) for value in row) for row in rows)


def results_equal(
    expected: ExecutionResult, actual: ExecutionResult, ordered: bool = False
) -> bool:
    if len(expected.columns) != len(actual.columns):
        return False
    if ordered:
        return tuple(normalize_rows_ordered(expected.rows)) == tuple(
            normalize_rows_ordered(actual.rows)
        )
    return normalize_rows(expected.rows) == normalize_rows(actual.rows)


def normalize_rows_ordered(
    rows: Iterable[Sequence[Any]],
) -> Iterable[tuple[Any, ...]]:
    return (tuple(normalize_value(value) for value in row) for row in rows)


def execute_query(
    connection: psycopg.Connection[Any],
    sql: str,
    timeout_ms: int,
    snapshot_as_of: datetime,
) -> ExecutionResult:
    frozen_sql = freeze_time(sql, snapshot_as_of)
    with connection.transaction():
        with connection.cursor() as cursor:
            cursor.execute("SET TRANSACTION READ ONLY")
            cursor.execute("SELECT set_config('TimeZone', 'Asia/Shanghai', true)")
            cursor.execute(
                "SELECT set_config('statement_timeout', %s, true)",
                (str(timeout_ms),),
            )
            cursor.execute(frozen_sql)
            columns = tuple(column.name for column in cursor.description or ())
            rows = tuple(cursor.fetchall())
    return ExecutionResult(columns=columns, rows=rows)


def validate_dataset(examples: list[dict[str, Any]]) -> dict[str, Any]:
    failures = []
    contexts = []
    for index, example in enumerate(examples):
        try:
            validate_example(example)
            contexts.append(gold_context(example))
        except Exception as error:
            failures.append({"index": index, "error": str(error)})
    return {
        "example_count": len(examples),
        "valid_count": len(examples) - len(failures),
        "failure_count": len(failures),
        "failures": failures,
        "unique_context_count": len(set(contexts)),
    }


def audit_gold(
    examples: list[dict[str, Any]],
    database_url: str,
    timeout_ms: int,
    snapshot_as_of: datetime,
) -> dict[str, Any]:
    outcomes = Counter()
    failures = []
    items = []
    with psycopg.connect(database_url) as connection:
        for index, example in enumerate(examples):
            try:
                validate_example(example)
                result = execute_query(
                    connection, example["sql"], timeout_ms, snapshot_as_of
                )
                if not result.rows:
                    outcome = "empty"
                elif all(all(value is None for value in row) for row in result.rows):
                    outcome = "all_null"
                elif len(result.rows) == 1 and result.rows[0] == (0,):
                    outcome = "single_zero"
                else:
                    outcome = "nonempty"
                outcomes[outcome] += 1
                items.append(
                    {
                        "index": index,
                        "outcome": outcome,
                        "difficulty": example["difficulty"],
                        "table_names": example["table_names"],
                        "row_count": len(result.rows),
                    }
                )
            except Exception as error:
                outcomes["error"] += 1
                failures.append(
                    {
                        "index": index,
                        "error_type": type(error).__name__,
                        "error": str(error),
                    }
                )
                items.append(
                    {
                        "index": index,
                        "outcome": "error",
                        "difficulty": example["difficulty"],
                        "table_names": example["table_names"],
                    }
                )
                connection.rollback()
    return {
        "example_count": len(examples),
        "outcomes": dict(sorted(outcomes.items())),
        "items": items,
        "failures": failures,
    }


def load_predictions(path: Path) -> dict[str, str]:
    value = load_examples(path)
    predictions: dict[str, str] = {}
    for item in value:
        question_id = item.get("question_id")
        sql = item.get("sql")
        if not isinstance(question_id, str) or not isinstance(sql, str):
            raise ValueError("each prediction requires string question_id and sql fields")
        if question_id in predictions:
            raise ValueError(f"duplicate prediction question_id: {question_id}")
        predictions[question_id] = sql
    return predictions


def evaluate_predictions(
    examples: list[dict[str, Any]],
    predictions: dict[str, str],
    database_url: str,
    timeout_ms: int,
    snapshot_as_of: datetime,
) -> dict[str, Any]:
    totals = Counter(example["difficulty"] for example in examples)
    selected_ids = {example["question_id"] for example in examples}
    correct = Counter()
    outcomes = Counter()
    items = []
    with psycopg.connect(database_url) as connection:
        for example in examples:
            question_id = example["question_id"]
            predicted_sql = predictions.get(question_id)
            if predicted_sql is None:
                outcome = "missing"
                is_correct = False
            else:
                try:
                    expected = execute_query(
                        connection, example["sql"], timeout_ms, snapshot_as_of
                    )
                    actual = execute_query(
                        connection, predicted_sql, timeout_ms, snapshot_as_of
                    )
                    gold_query = parse_single_query(example["sql"])
                    is_correct = results_equal(
                        expected,
                        actual,
                        ordered=gold_query.args.get("order") is not None,
                    )
                    outcome = "correct" if is_correct else "mismatch"
                except Exception as error:
                    connection.rollback()
                    is_correct = False
                    outcome = "error"
                    error_type = type(error).__name__
            outcomes[outcome] += 1
            if is_correct:
                correct[example["difficulty"]] += 1
            item = {
                "question_id": question_id,
                "difficulty": example["difficulty"],
                "outcome": outcome,
            }
            if outcome == "error":
                item["error_type"] = error_type
            items.append(item)

    total_correct = outcomes["correct"]
    return {
        "example_count": len(examples),
        "prediction_count": sum(question_id in selected_ids for question_id in predictions),
        "correct_count": total_correct,
        "execution_accuracy": total_correct / len(examples),
        "outcomes": dict(sorted(outcomes.items())),
        "by_difficulty": {
            difficulty: {
                "correct": correct[difficulty],
                "total": totals[difficulty],
                "execution_accuracy": correct[difficulty] / totals[difficulty],
            }
            for difficulty in sorted(totals)
        },
        "items": items,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and audit MaritimeSQLBench.")
    parser.add_argument("command", choices=("validate", "audit-gold", "evaluate"))
    parser.add_argument(
        "--evaluation-data",
        type=Path,
        default=ROOT / "evaluation_data_anonymized.json",
    )
    parser.add_argument("--database-url")
    parser.add_argument("--predictions", type=Path)
    parser.add_argument("--timeout-ms", type=int, default=15_000)
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "--snapshot-as-of",
        type=datetime.fromisoformat,
        help="Required ISO-8601 timestamp used to replace SQL clock expressions.",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        examples = select_examples(load_examples(args.evaluation_data), args.limit)
    except ValueError as error:
        parser.error(str(error))
    if args.command == "validate":
        report = validate_dataset(examples)
    elif args.command == "audit-gold":
        if not args.database_url:
            parser.error("audit-gold requires --database-url")
        if not args.snapshot_as_of:
            parser.error("audit-gold requires --snapshot-as-of")
        report = audit_gold(
            examples, args.database_url, args.timeout_ms, args.snapshot_as_of
        )
    else:
        if not args.database_url or not args.predictions or not args.snapshot_as_of:
            parser.error(
                "evaluate requires --database-url, --predictions, and --snapshot-as-of"
            )
        report = evaluate_predictions(
            examples,
            load_predictions(args.predictions),
            args.database_url,
            args.timeout_ms,
            args.snapshot_as_of,
        )

    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 0 if not report.get("failure_count") and not report.get("failures") else 1


if __name__ == "__main__":
    raise SystemExit(main())