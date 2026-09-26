from pathlib import Path
import json
import logging

from docling.document_converter import DocumentConverter


# =========================
# Project directories
# =========================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_DIR = BASE_DIR / "data" / "input"
OUTPUT_DIR = BASE_DIR / "data" / "processed"
LOG_DIR = BASE_DIR / "logs"


# =========================
# Configuration
# =========================

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".xlsx"}

SUPPORTED_DEPARTMENTS = {
    "HR",
    "Finance",
    "Legal",
    "Legal & Compliance",
    "Customer",
    "IT & Security",
    "Marketing",
    "Operations",
    "Business Development",
    "Procurement",
    "Supply Chain",
    "Sales",
}


# =========================
# Logging
# =========================

LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=LOG_DIR / "parser.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


# =========================
# Document conversion
# =========================

def convert_document(
    converter: DocumentConverter,
    input_file: Path,
    output_file: Path,
    metadata_file: Path,
    department: str,
) -> bool:
    """Convert one document to Markdown and create metadata JSON."""

    try:
        logger.info("Processing: %s", input_file)

        result = converter.convert(input_file)

        markdown = result.document.export_to_markdown()
        if not markdown or not markdown.strip():
            raise ValueError("Document conversion produced empty Markdown")
        # Save Markdown
        output_file.parent.mkdir(parents=True, exist_ok=True)

        output_file.write_text(
            markdown,
            encoding="utf-8",
        )

        # Create metadata
        metadata = {
            "department": department,
            "source_file": input_file.name,
            "file_type": input_file.suffix.lower().lstrip("."),
            "source_path": str(
                input_file.relative_to(BASE_DIR)
            ),
        }

        metadata_file.write_text(
            json.dumps(
                metadata,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        logger.info(
            "Successfully converted: %s",
            input_file,
        )

        return True

    except Exception as exc:

        logger.exception(
            "Failed to convert %s: %s",
            input_file,
            exc,
        )

        return False


# =========================
# Main processing function
# =========================

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

        # Ignore directories
        if not input_file.is_file():
            continue

        # Ignore unsupported files
        if input_file.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        # Determine department
        try:

            relative_parts = input_file.relative_to(
                INPUT_DIR
            ).parts

            department = relative_parts[0]

        except (ValueError, IndexError):

            logger.warning(
                "Could not determine department: %s",
                input_file,
            )

            continue

        # Validate department
        if department not in SUPPORTED_DEPARTMENTS:

            logger.warning(
                "Unsupported department '%s': %s",
                department,
                input_file,
            )

            print(
                f"⚠ Skipping unsupported department: "
                f"{department}/{input_file.name}"
            )

            continue

        # Preserve folder structure below department
        relative_path = input_file.relative_to(
            INPUT_DIR / department
        )

        output_file = (
            OUTPUT_DIR
            / department
            / relative_path.with_suffix(".md")
        )

        metadata_file = (
            OUTPUT_DIR
            / department
            / relative_path.with_suffix(".json")
        )

        total += 1

        print(
            f"Processing [{department}]: "
            f"{input_file.name}"
        )

        success = convert_document(
            converter=converter,
            input_file=input_file,
            output_file=output_file,
            metadata_file=metadata_file,
            department=department,
        )

        if success:

            successful += 1

            print(
                f"  ✓ Markdown: {output_file}"
            )

            print(
                f"  ✓ Metadata: {metadata_file}"
            )

        else:

            failed += 1

            print(
                f"  ✗ Failed: {input_file.name}"
            )

    # =========================
    # Summary
    # =========================

    print("\n========== PARSING SUMMARY ==========")

    print(f"Total documents : {total}")
    print(f"Successful      : {successful}")
    print(f"Failed          : {failed}")

    print("=====================================")


# =========================
# Entry point
# =========================

if __name__ == "__main__":
    process_documents()
