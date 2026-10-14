from __future__ import annotations

import argparse
import ast
import re
from pathlib import Path


COLUMN_PATTERN = re.compile(r'^\s*"([^"]+)"\s+(.+?)(?:,)?\s*(?:--.*)?$', re.MULTILINE)
TYPE_PATTERN = re.compile(
    r"^(timestamp with time zone|timestamp without time zone|timestamptz|"
    r"double precision|bigserial|serial|"
    r"character varying(?:\(\d+\))?|public\.geography(?:\([^)]*\))?|"
    r"numeric(?:\(\d+\s*,\s*\d+\))?|varchar(?:\(\d+\))?|"
    r"bigint|smallint|integer|int8|int4|int2|jsonb|text|date|uuid)\b",
    re.IGNORECASE,
)
SAFE_NAME = re.compile(r"^[a-z_][a-z0-9_]*$")


def load_schema(path: Path) -> dict[str, str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "schema_dict"
            for target in node.targets
        ):
            value = ast.literal_eval(node.value)
            if isinstance(value, dict):
                return value
    raise ValueError(f"schema_dict was not found in {path}")


def extract_columns(description: str) -> list[tuple[str, str]]:
    columns = []
    for name, declaration in COLUMN_PATTERN.findall(description):
        type_match = TYPE_PATTERN.match(declaration)
        if type_match:
            data_type = type_match.group(1)
            if data_type.lower().startswith("public.geography"):
                data_type = "text"
            columns.append((name, data_type))
    if not columns:
        raise ValueError("no columns found in schema description")
    return columns


def render_schema(schema: dict[str, str]) -> str:
    statements = [
        "-- Generated from schema_anonymized.py; do not edit by hand.",
        "-- Geography columns are stored as text because this release has no spatial SQL.",
        "CREATE SCHEMA IF NOT EXISTS maritime;",
        "SET TIME ZONE 'UTC';",
        "SET DateStyle = 'ISO, DMY';",
        "",
    ]
    for qualified_name, description in schema.items():
        namespace, table = qualified_name.split(".", 1)
        if namespace != "maritime" or not SAFE_NAME.fullmatch(table):
            raise ValueError(f"unsafe table name: {qualified_name}")
        columns = extract_columns(description)
        rendered_columns = ",\n".join(
            f'    "{name}" {data_type}' for name, data_type in columns
        )
        statements.extend(
            [
                f'CREATE TABLE "maritime"."{table}" (',
                rendered_columns,
                ");",
                "",
            ]
        )
    return "\n".join(statements)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate executable PostgreSQL DDL.")
    parser.add_argument(
        "--schema-source",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "schema_anonymized.py",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent / "schema.sql",
    )
    args = parser.parse_args()
    schema = load_schema(args.schema_source.resolve())
    rendered = render_schema(schema)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"generated {len(schema)} tables at {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())