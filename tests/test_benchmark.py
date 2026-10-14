from __future__ import annotations

import unittest
from datetime import datetime, timezone
from decimal import Decimal

import benchmark


class SqlValidationTests(unittest.TestCase):
    def test_all_released_examples_validate(self) -> None:
        report = benchmark.validate_dataset(benchmark.load_examples())
        self.assertEqual(585, report["valid_count"])
        self.assertEqual([], report["failures"])

    def test_rejects_multiple_statements(self) -> None:
        with self.assertRaisesRegex(ValueError, "exactly one"):
            benchmark.parse_single_query("SELECT 1; SELECT 2")

    def test_rejects_data_modification(self) -> None:
        with self.assertRaisesRegex(ValueError, "read-only"):
            benchmark.parse_single_query("DELETE FROM maritime.vessel_reference")

    def test_rejects_prohibited_function(self) -> None:
        with self.assertRaisesRegex(ValueError, "prohibited function"):
            benchmark.parse_single_query("SELECT pg_sleep(1)")

    def test_gold_context_contains_only_required_tables(self) -> None:
        example = benchmark.load_examples()[0]
        context = benchmark.gold_context(example)
        self.assertIn("maritime.vessel_reference", context)
        self.assertNotIn("maritime.vessel_event_log", context)

    def test_freeze_time_replaces_clock_expressions(self) -> None:
        frozen = benchmark.freeze_time(
            "SELECT NOW(), CURRENT_DATE, CURRENT_TIMESTAMP",
            datetime(2025, 3, 4, 12, 30, tzinfo=timezone.utc),
        )
        query = benchmark.parse_single_query(frozen)
        self.assertIsNone(query.find(benchmark.exp.CurrentDate))
        self.assertIsNone(query.find(benchmark.exp.CurrentTimestamp))
        self.assertIn("2025-03-04", frozen)

    def test_select_examples_returns_all_when_limit_is_none(self) -> None:
        examples = [{"question_id": "msb_0001"}, {"question_id": "msb_0002"}]
        self.assertIs(examples, benchmark.select_examples(examples, None))

    def test_select_examples_rejects_zero_limit(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least 1"):
            benchmark.select_examples([{"question_id": "msb_0001"}], 0)

    def test_select_examples_rejects_negative_limit(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least 1"):
            benchmark.select_examples([{"question_id": "msb_0001"}], -1)

    def test_select_examples_rejects_limit_above_dataset_size(self) -> None:
        with self.assertRaisesRegex(ValueError, "must not exceed"):
            benchmark.select_examples([{"question_id": "msb_0001"}], 2)

    def test_select_examples_returns_requested_prefix(self) -> None:
        examples = [
            {"question_id": "msb_0001"},
            {"question_id": "msb_0002"},
            {"question_id": "msb_0003"},
        ]
        self.assertEqual(examples[:2], benchmark.select_examples(examples, 2))


class ResultComparisonTests(unittest.TestCase):
    def test_unordered_multiset_keeps_duplicates(self) -> None:
        expected = benchmark.ExecutionResult(("value",), ((1,), (1,), (2,)))
        reordered = benchmark.ExecutionResult(("other",), ((2,), (1,), (1,)))
        missing_duplicate = benchmark.ExecutionResult(("value",), ((1,), (2,)))
        self.assertTrue(benchmark.results_equal(expected, reordered))
        self.assertFalse(benchmark.results_equal(expected, missing_duplicate))

    def test_ordered_results_preserve_row_order(self) -> None:
        expected = benchmark.ExecutionResult(("value",), ((1,), (2,)))
        reversed_rows = benchmark.ExecutionResult(("value",), ((2,), (1,)))
        self.assertFalse(benchmark.results_equal(expected, reversed_rows, ordered=True))

    def test_decimal_normalization_is_exact(self) -> None:
        left = benchmark.ExecutionResult(("value",), ((Decimal("1.00"),),))
        right = benchmark.ExecutionResult(("value",), ((Decimal("1.0"),),))
        self.assertTrue(benchmark.results_equal(left, right))

    def test_load_predictions_rejects_duplicate_ids(self) -> None:
        import json
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "predictions.json"
            path.write_text(
                json.dumps(
                    [
                        {"question_id": "msb_0001", "sql": "SELECT 1"},
                        {"question_id": "msb_0001", "sql": "SELECT 2"},
                    ]
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "duplicate"):
                benchmark.load_predictions(path)

    def test_evaluate_prediction_count_ignores_predictions_outside_selected_examples(self) -> None:
        examples = [
            {
                "question_id": "msb_0001",
                "difficulty": "简单",
                "sql": "SELECT 1",
            },
            {
                "question_id": "msb_0002",
                "difficulty": "中等",
                "sql": "SELECT 2",
            },
        ]
        class FakeConnection:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def rollback(self) -> None:
                return None

        original_connect = benchmark.psycopg.connect
        original_execute_query = benchmark.execute_query
        original_parse_single_query = benchmark.parse_single_query
        try:
            benchmark.psycopg.connect = lambda _database_url: FakeConnection()
            benchmark.execute_query = lambda *_args, **_kwargs: benchmark.ExecutionResult(
                ("value",), ((1,),)
            )
            benchmark.parse_single_query = lambda _sql: benchmark.parse("SELECT 1", read="postgres")[0]
            report = benchmark.evaluate_predictions(
                examples,
                {
                    "msb_0001": "SELECT 1",
                    "msb_9999": "SELECT 9999",
                },
                database_url="postgresql://unused",
                timeout_ms=1000,
                snapshot_as_of=datetime(2026, 10, 13, tzinfo=timezone.utc),
            )
        finally:
            benchmark.psycopg.connect = original_connect
            benchmark.execute_query = original_execute_query
            benchmark.parse_single_query = original_parse_single_query

        self.assertEqual(1, report["prediction_count"])


class EvaluatePredictionScopeTests(unittest.TestCase):
    def test_evaluate_prediction_count_ignores_outside_ids_without_opening_database(self) -> None:
        examples = [{"question_id": "msb_0001", "difficulty": "简单", "sql": "SELECT 1"}]
        predictions = {"msb_0001": "SELECT 1", "msb_9999": "SELECT 9999"}

        class FakeConnection:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def rollback(self) -> None:
                return None

        original_connect = benchmark.psycopg.connect
        original_execute_query = benchmark.execute_query
        original_parse_single_query = benchmark.parse_single_query
        try:
            benchmark.psycopg.connect = lambda _database_url: FakeConnection()
            benchmark.execute_query = lambda *_args, **_kwargs: benchmark.ExecutionResult(
                ("value",), ((1,),)
            )
            benchmark.parse_single_query = lambda _sql: benchmark.parse("SELECT 1", read="postgres")[0]
            report = benchmark.evaluate_predictions(
                examples,
                predictions,
                database_url="postgresql://unused",
                timeout_ms=1000,
                snapshot_as_of=datetime(2026, 10, 13, tzinfo=timezone.utc),
            )
        finally:
            benchmark.psycopg.connect = original_connect
            benchmark.execute_query = original_execute_query
            benchmark.parse_single_query = original_parse_single_query

        self.assertEqual(1, report["prediction_count"])
        self.assertEqual(1, report["correct_count"])
        self.assertEqual({"correct": 1}, report["outcomes"])


if __name__ == "__main__":
    unittest.main()