from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any


SAFE_NAME = re.compile(r"^[a-z_][a-z0-9_]*$")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(data_dir: Path) -> dict[str, Any]:
    path = data_dir / "manifest.json"
    with path.open(encoding="utf-8") as file:
        manifest = json.load(file)
    if manifest.get("table_count") != len(manifest.get("tables", [])):
        raise ValueError("manifest table_count does not match tables")
    return manifest


def validate_table(data_dir: Path, table: dict[str, Any]) -> tuple[str, list[str], Path]:
    qualified_name = table["table"]
    namespace, name = qualified_name.split(".", 1)
    if namespace != "maritime" or not SAFE_NAME.fullmatch(name):
        raise ValueError(f"unsafe table name: {qualified_name}")

    path = (data_dir / table["file"]).resolve()
    if path.parent != data_dir.resolve():
        raise ValueError(f"data file escapes data directory: {table['file']}")
    if sha256(path) != table["sha256"]:
        raise ValueError(f"checksum mismatch: {table['file']}")
    with path.open(encoding="utf-8", newline="") as file:
        reader = csv.reader(file)
        columns = next(reader)
        row_count = sum(1 for _ in reader)
    if not columns or not all(SAFE_NAME.fullmatch(column) for column in columns):
        raise ValueError(f"unsafe or empty CSV header: {table['file']}")
    if len(columns) != table["column_count"]:
        raise ValueError(f"column count mismatch: {table['file']}")
    if row_count != table["row_count"]:
        raise ValueError(f"row count mismatch: {table['file']}")
    return qualified_name, columns, path


def run_psql(psql: str, database_url: str, arguments: list[str]) -> None:
    subprocess.run(
        [psql, database_url, "--set", "ON_ERROR_STOP=1", *arguments],
        check=True,
    )


def build_copy_command(qualified_name: str, columns: list[str], path: Path) -> str:
    quoted_columns = ", ".join(f'"{column}"' for column in columns)
    escaped_path = str(path).replace("'", "''")
    return (
        f"\\copy {qualified_name} ({quoted_columns}) FROM '{escaped_path}' "
        "WITH (FORMAT csv, HEADER true, ENCODING 'UTF8', NULL '', "
        f"FORCE_NULL ({quoted_columns}))"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Load MaritimeSQLBench into PostgreSQL.")
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--data-dir", required=True, type=Path)
    parser.add_argument("--psql", default="psql")
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path(__file__).resolve().parent / "schema.sql",
    )
    args = parser.parse_args()

    data_dir = args.data_dir.resolve()
    manifest = load_manifest(data_dir)
    validated = [validate_table(data_dir, table) for table in manifest["tables"]]

    run_psql(args.psql, args.database_url, ["--file", str(args.schema.resolve())])
    for qualified_name, columns, path in validated:
        copy_command = build_copy_command(qualified_name, columns, path)
        run_psql(
            args.psql,
            args.database_url,
            [
                "--command",
                "SET TIME ZONE 'UTC'; SET DateStyle = 'ISO, DMY';",
                "--command",
                copy_command,
            ],
        )

    print(f"loaded {len(validated)} tables from {data_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())