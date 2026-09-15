from pathlib import Path
import logging

from docling.document_converter import DocumentConverter


# Project directories
BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = BASE_DIR / "data" / "input"
OUTPUT_DIR = BASE_DIR / "data" / "processed"
LOG_DIR = BASE_DIR / "logs"

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".xlsx"}

# Logging configuration
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=LOG_DIR / "parser.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


def convert_document(converter, input_file: Path, output_file: Path) -> bool:
    """Convert one document to Markdown using Docling."""
    try:
        logger.info("Processing: %s", input_file)

        result = converter.convert(input_file)
        markdown = result.document.export_to_markdown()

        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")

        logger.info("Successfully converted: %s", input_file)
        return True

    except Exception as exc:
        logger.exception("Failed to convert %s: %s", input_file, exc)
        return False


def process_documents() -> None:
    """Scan department folders and convert supported documents."""
    if not INPUT_DIR.exists():
        print(f"Input directory not found: {INPUT_DIR}")
        return

    converter = DocumentConverter()

    total = 0
    successful = 0
    failed = 0

    for input_file in INPUT_DIR.rglob("*"):
        if not input_file.is_file():
            continue

        if input_file.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        # Department is the folder directly under data/input
        try:
            department = input_file.relative_to(INPUT_DIR).parts[0]
        except IndexError:
            logger.warning("Could not determine department: %s", input_file)
            continue

        relative_path = input_file.relative_to(INPUT_DIR / department)
        output_file = OUTPUT_DIR / department / relative_path.with_suffix(".md")

        total += 1

        print(f"Processing [{department}]: {input_file.name}")

        if convert_document(converter, input_file, output_file):
            successful += 1
            print(f"  ✓ Created: {output_file}")
        else:
            failed += 1
            print(f"  ✗ Failed: {input_file.name}")

    print("\n========== PARSING SUMMARY ==========")
    print(f"Total documents : {total}")
    print(f"Successful      : {successful}")
    print(f"Failed          : {failed}")
    print("=====================================")


if __name__ == "__main__":
    process_documents()
