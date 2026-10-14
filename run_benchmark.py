from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_DATABASE_URL = (
    "postgresql://benchmark_admin:benchmark_local_only@localhost:54320/"
    "maritime_benchmark"
)
SNAPSHOT_AS_OF = "2026-10-13T14:00:00+08:00"


def run(arguments: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    print("+ " + " ".join(arguments), file=sys.stderr)
    return subprocess.run(arguments, cwd=ROOT, check=check, text=True)


def ensure_python_dependencies() -> None:
    check = subprocess.run(
        [sys.executable, "-c", "import psycopg, sqlglot"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if check.returncode:
        run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run MaritimeSQLBench database setup, inference, and EX evaluation."
    )
    parser.add_argument("--model", default=os.environ.get("MODEL_NAME"))
    parser.add_argument(
        "--base-url", default=os.environ.get("MODEL_BASE_URL", "https://api.openai.com/v1")
    )
    parser.add_argument("--api-key-env", default="MODEL_API_KEY")
    parser.add_argument(
        "--predictions", type=Path, default=ROOT / "predictions.json"
    )
    parser.add_argument(
        "--report", type=Path, default=ROOT / "evaluation_report.json"
    )
    parser.add_argument("--database-url", default=DEFAULT_DATABASE_URL)
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "--workers",
        type=int,
        default=int(os.environ.get("MODEL_WORKERS", "1")),
        help="Number of concurrent model requests.",
    )
    parser.add_argument(
        "--resume", action="store_true", help="Reuse existing model predictions."
    )
    parser.add_argument(
        "--reuse-database",
        action="store_true",
        help="Do not recreate the benchmark Docker volume or reload CSV data.",
    )
    parser.add_argument(
        "--no-docker",
        action="store_true",
        help="Use --database-url without managing Docker.",
    )
    parser.add_argument(
        "--stop", action="store_true", help="Stop Docker after evaluation."
    )
    args = parser.parse_args()

    ensure_python_dependencies()
    python = sys.executable
    if not args.no_docker:
        run(["docker", "compose", "config", "--quiet"])
        if not args.reuse_database:
            run(["docker", "compose", "down", "-v", "--remove-orphans"])
        run(["docker", "compose", "up", "-d", "--wait"])
        if not args.reuse_database:
            run(
                [
                    python,
                    "database/load_data.py",
                    "--database-url",
                    args.database_url,
                    "--data-dir",
                    "data",
                ]
            )

    audit_path = args.report.with_name(args.report.stem + ".gold-audit.json")
    run(
        [
            python,
            "benchmark.py",
            "audit-gold",
            "--database-url",
            args.database_url,
            "--snapshot-as-of",
            SNAPSHOT_AS_OF,
            "--output",
            str(audit_path),
        ]
        + (["--limit", str(args.limit)] if args.limit is not None else [])
    )

    if args.model:
        inference_command = [
            python,
            "model_inference.py",
            "--model",
            args.model,
            "--base-url",
            args.base_url,
            "--api-key-env",
            args.api_key_env,
            "--workers",
            str(args.workers),
            "--output",
            str(args.predictions),
        ]
        if args.limit is not None:
            inference_command.extend(["--limit", str(args.limit)])
        if not args.resume:
            inference_command.append("--overwrite")
        inference = run(inference_command, check=False)
        if not args.predictions.exists():
            return inference.returncode or 1
    elif not args.predictions.exists():
        parser.error("provide --model or an existing --predictions file")

    run(
        [
            python,
            "benchmark.py",
            "evaluate",
            "--predictions",
            str(args.predictions),
            "--database-url",
            args.database_url,
            "--snapshot-as-of",
            SNAPSHOT_AS_OF,
            "--output",
            str(args.report),
        ]
        + (["--limit", str(args.limit)] if args.limit is not None else [])
    )

    report = json.loads(args.report.read_text(encoding="utf-8"))
    print(
        json.dumps(
            {
                "execution_accuracy": report["execution_accuracy"],
                "correct_count": report["correct_count"],
                "example_count": report["example_count"],
                "outcomes": report["outcomes"],
                "by_difficulty": report["by_difficulty"],
                "predictions": str(args.predictions),
                "report": str(args.report),
            },
            ensure_ascii=False,
            indent=2,
        )
    )

    if args.stop and not args.no_docker:
        run(["docker", "compose", "down"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())