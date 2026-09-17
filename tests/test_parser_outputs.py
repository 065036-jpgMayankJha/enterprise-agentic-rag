import json
import unittest
from pathlib import Path


PROCESSED_DIR = Path("data/processed")
REQUIRED_FIELDS = {
    "department",
    "source_file",
    "file_type",
    "source_path",
}


class TestParserOutputs(unittest.TestCase):
    def test_metadata_and_markdown_outputs(self):
        json_files = sorted(PROCESSED_DIR.rglob("*.json"))

        self.assertTrue(json_files, "No metadata JSON files found")

        for json_file in json_files:
            with self.subTest(file=str(json_file)):
                metadata = json.loads(
                    json_file.read_text(encoding="utf-8")
                )

                self.assertTrue(REQUIRED_FIELDS.issubset(metadata))
                self.assertTrue(json_file.with_suffix(".md").exists())
                self.assertTrue(
                    json_file.with_suffix(".md")
                    .read_text(encoding="utf-8")
                    .strip()
                )


if __name__ == "__main__":
    unittest.main()
