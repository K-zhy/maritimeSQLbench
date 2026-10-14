from __future__ import annotations

import csv
import decimal
import hashlib
import importlib.util
import json
import re
import tempfile
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


generate_schema = load_module("generate_schema", ROOT / "database" / "generate_schema.py")
load_data = load_module("load_data", ROOT / "database" / "load_data.py")

PUBLIC_REFERENCE_COORDINATE_COLUMNS = {
    "port_reference.csv": {"lon", "lat"},
    "country_reference.csv": {"lon", "lat"},
    "route_node_reference.csv": {
        "lon",
        "lat",
        "start_lon",
        "start_lat",
        "end_lon",
        "end_lat",
    },
    "special_region_reference.csv": {
        "center_lon",
        "center_lat",
        "top_lon",
        "top_lat",
        "bottom_lon",
        "bottom_lat",
        "title_lon",
        "title_lat",
    },
    "sea_area_reference.csv": {
        "center_lon",
        "center_lat",
        "max_lon",
        "max_lat",
        "min_lon",
        "min_lat",
    },
}

CLEARED_COMPOSITE_COLUMNS = {
    "port_reference.csv": {"position", "extra_lon_lat"},
    "country_reference.csv": {"position", "data_shape"},
    "route_node_reference.csv": {"segment"},
    "special_region_reference.csv": {"data_shape"},
    "sea_area_reference.csv": {"data_shape"},
    "berth_reference.csv": {
        "berth_line",
        "berth_line_geo",
        "berth_line_start_point",
        "berth_line_end_point",
    },
}


def is_one_decimal(value: str) -> bool:
    if not re.fullmatch(r"-?\d+\.\d", value):
        return False
    quantized = decimal.Decimal(value).quantize(decimal.Decimal("0.1"))
    return format(quantized, "f") == value


class GenerateSchemaTests(unittest.TestCase):
    def test_static_schema_matches_generator(self) -> None:
        schema = generate_schema.load_schema(ROOT / "schema_anonymized.py")
        rendered = generate_schema.render_schema(schema)
        self.assertEqual(16, len(schema))
        self.assertEqual(rendered, (ROOT / "database" / "schema.sql").read_text())
        self.assertEqual(16, rendered.count('CREATE TABLE "maritime".'))


class LoadDataTests(unittest.TestCase):
    def test_validate_table_accepts_matching_csv(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data_dir = Path(directory)
            data_file = data_dir / "sample.csv"
            with data_file.open("w", encoding="utf-8", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["id", "value"])
                writer.writerow(["1", "example"])
            table = {
                "table": "maritime.sample",
                "file": data_file.name,
                "column_count": 2,
                "row_count": 1,
                "sha256": hashlib.sha256(data_file.read_bytes()).hexdigest(),
            }
            name, columns, path = load_data.validate_table(data_dir, table)
            self.assertEqual("maritime.sample", name)
            self.assertEqual(["id", "value"], columns)
            self.assertEqual(data_file.resolve(), path)

    def test_validate_table_counts_embedded_newline_as_single_row(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data_dir = Path(directory)
            data_file = data_dir / "sample.csv"
            with data_file.open("w", encoding="utf-8", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["id", "value"])
                writer.writerow(["1", "line 1\nline 2"])
            table = {
                "table": "maritime.sample",
                "file": data_file.name,
                "column_count": 2,
                "row_count": 1,
                "sha256": hashlib.sha256(data_file.read_bytes()).hexdigest(),
            }
            name, columns, path = load_data.validate_table(data_dir, table)
            self.assertEqual("maritime.sample", name)
            self.assertEqual(["id", "value"], columns)
            self.assertEqual(data_file.resolve(), path)

    def test_validate_table_rejects_row_count_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data_dir = Path(directory)
            data_file = data_dir / "sample.csv"
            with data_file.open("w", encoding="utf-8", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["id", "value"])
                writer.writerow(["1", "example"])
            table = {
                "table": "maritime.sample",
                "file": data_file.name,
                "column_count": 2,
                "row_count": 2,
                "sha256": hashlib.sha256(data_file.read_bytes()).hexdigest(),
            }
            with self.assertRaisesRegex(ValueError, "row count mismatch"):
                load_data.validate_table(data_dir, table)

    def test_load_manifest_rejects_count_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(
                json.dumps({"table_count": 2, "tables": []}), encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "table_count"):
                load_data.load_manifest(path.parent)

    def test_copy_treats_quoted_empty_values_as_null(self) -> None:
        command = load_data.build_copy_command(
            "maritime.sample", ["id", "value"], Path("/tmp/sample.csv")
        )
        self.assertIn("NULL ''", command)
        self.assertIn('FORCE_NULL ("id", "value")', command)

    def test_released_package_is_complete(self) -> None:
        data_dir = ROOT / "data"
        manifest = load_data.load_manifest(data_dir)
        validated = [
            load_data.validate_table(data_dir, table) for table in manifest["tables"]
        ]
        examples = json.loads(
            (ROOT / "evaluation_data_anonymized.json").read_text(encoding="utf-8")
        )
        schema = generate_schema.load_schema(ROOT / "schema_anonymized.py")
        self.assertEqual(16, len(validated))
        self.assertEqual(585, len(examples))
        self.assertEqual(585, len({example["question_id"] for example in examples}))
        self.assertEqual(
            Counter({"简单": 212, "中等": 316, "复杂": 57}),
            Counter(example["difficulty"] for example in examples),
        )
        self.assertEqual(
            set(schema),
            {table for example in examples for table in example["table_names"]},
        )
        self.assertEqual(585, manifest["gold_query_audit"]["nonempty_count"])

    def test_public_manifest_shape_hides_private_audit_details(self) -> None:
        manifest = load_data.load_manifest(ROOT / "data")
        self.assertEqual(1, manifest["format_version"])
        self.assertEqual("1.0.0", manifest["version"])
        self.assertEqual("released", manifest["status"])
        self.assertEqual(16, manifest["table_count"])
        self.assertIn("snapshot_as_of", manifest)
        self.assertIn("composition", manifest)
        self.assertIn("gold_query_audit", manifest)
        self.assertIn("evaluation", manifest)
        self.assertIn("sensitive_residual_audit", manifest)
        self.assertNotIn("generated_mapping_counts", manifest)
        self.assertNotIn("violations", manifest["sensitive_residual_audit"])
        self.assertIn("checked_fields", manifest["sensitive_residual_audit"])
        self.assertIn("violation_count", manifest["sensitive_residual_audit"])

    def test_public_reference_coordinates_are_quantized_and_spatial_strings_cleared(self) -> None:
        data_dir = ROOT / "data"
        total_nonempty_coordinate_count = 0
        for file_name, coordinate_columns in PUBLIC_REFERENCE_COORDINATE_COLUMNS.items():
            with (data_dir / file_name).open(encoding="utf-8", newline="") as file:
                reader = csv.DictReader(file)
                rows = list(reader)

            for column in coordinate_columns:
                self.assertIn(column, reader.fieldnames or [], msg=f"missing {column} in {file_name}")
                nonempty_values = [row[column] for row in rows if row[column] != ""]
                total_nonempty_coordinate_count += len(nonempty_values)
                self.assertTrue(
                    all(is_one_decimal(value) for value in nonempty_values),
                    msg=f"found non-quantized values in {file_name}.{column}",
                )
        self.assertGreater(
            total_nonempty_coordinate_count,
            0,
            msg="expected at least one nonempty public reference coordinate value",
        )

        for file_name, cleared_columns in CLEARED_COMPOSITE_COLUMNS.items():
            with (data_dir / file_name).open(encoding="utf-8", newline="") as file:
                reader = csv.DictReader(file)
                rows = list(reader)

            for column in cleared_columns:
                self.assertIn(column, reader.fieldnames or [], msg=f"missing {column} in {file_name}")
                self.assertTrue(
                    all(row[column] == "" for row in rows),
                    msg=f"expected cleared values in {file_name}.{column}",
                )


if __name__ == "__main__":
    unittest.main()