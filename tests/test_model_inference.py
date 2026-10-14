from __future__ import annotations

import io
import json
import unittest
from unittest.mock import patch

import model_inference
from benchmark import load_examples


class ModelInferenceTests(unittest.TestCase):
    def test_prompt_excludes_gold_sql(self) -> None:
        example = load_examples()[0]
        messages = model_inference.build_messages(example)
        prompt = "\n".join(message["content"] for message in messages)
        self.assertEqual(model_inference.PROMPT_PREFIX, messages[0]["content"])
        self.assertTrue(messages[1]["content"].startswith("Database Schema：\n"))
        self.assertIn("\n\n用户自然语言问题：\n", messages[1]["content"])
        self.assertIn(example["query"], prompt)
        self.assertNotIn(example["sql"], prompt)

    def test_extract_sql_accepts_fenced_response(self) -> None:
        self.assertEqual(
            "SELECT 1;", model_inference.extract_sql("```sql\nSELECT 1;\n```")
        )

    def test_openai_compatible_response(self) -> None:
        response = io.BytesIO(
            json.dumps(
                {"choices": [{"message": {"content": "SELECT 1;"}}]}
            ).encode("utf-8")
        )
        response.__enter__ = lambda: response  # type: ignore[attr-defined]
        response.__exit__ = lambda *_: None  # type: ignore[attr-defined]
        with patch("urllib.request.urlopen", return_value=response) as urlopen:
            sql = model_inference.call_chat_completions(
                base_url="https://example.invalid/v1",
                api_key="test-key",
                model="test-model",
                messages=[{"role": "user", "content": "question"}],
                temperature=0.0,
                timeout=1.0,
            )
        self.assertEqual("SELECT 1;", sql)
        request = urlopen.call_args.args[0]
        self.assertEqual("Bearer test-key", request.headers["Authorization"])


if __name__ == "__main__":
    unittest.main()