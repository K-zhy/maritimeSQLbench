from __future__ import annotations

import unittest
from pathlib import Path


class ReleaseMetadataTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parent.parent

    def test_license_files_exist(self) -> None:
        for name in ("LICENSE", "LICENSE-CODE", "LICENSE-DATA"):
            self.assertTrue((self.root / name).is_file(), name)

    def test_root_license_references_split_license_files(self) -> None:
        content = (self.root / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("LICENSE-CODE", content)
        self.assertIn("LICENSE-DATA", content)
        self.assertIn("No single license applies", content)

    def test_code_license_contains_mit_notice(self) -> None:
        content = (self.root / "LICENSE-CODE").read_text(encoding="utf-8")
        self.assertIn("MIT License", content)
        self.assertIn("Copyright (c) 2026 Haoyu Zhang and contributors", content)

    def test_data_license_contains_cc_by_identifiers(self) -> None:
        content = (self.root / "LICENSE-DATA").read_text(encoding="utf-8")
        self.assertIn("Creative Commons Attribution 4.0 International Public License", content)
        self.assertIn("Attribution 4.0 International", content)

    def test_citation_file_contains_required_fields(self) -> None:
        content = (self.root / "CITATION.cff").read_text(encoding="utf-8")
        self.assertIn("cff-version: 1.2.0", content)
        self.assertIn("title: MaritimeSQLBench", content)
        self.assertIn("version: 1.0.0", content)
        self.assertIn("repository-code: https://github.com/K-zhy/maritimeSQLbench", content)
        for name in (
            "given-names: Haoyu",
            "family-names: Zhang",
            "given-names: Yingqi",
            "family-names: Zou",
            "given-names: Xiangyu",
            "given-names: Shaohan",
            "given-names: Zijian",
        ):
            self.assertIn(name, content)
        self.assertNotIn("doi:", content)
        self.assertNotIn("date-released:", content)


if __name__ == "__main__":
    unittest.main()
