from __future__ import annotations

import argparse
import gc
import json
import re
import time
from math import ceil
from pathlib import Path

import pypdfium2 as pdfium
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from pypdf import PdfReader, PdfWriter


BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = BASE_DIR / "data" / "input"
OUTPUT_DIR = BASE_DIR / "data" / "processed"

# Deliberately conservative for an 8 GB RAM development machine.
CHUNK_SIZE = 10


def normalized_stem(path: Path) -> str:
    """Create a filesystem-safe, stable output stem."""
    return re.sub(r"[^A-Za-z0-9]+", "_", path.stem).strip("_")


def get_page_count(input_file: Path) -> int:
    """Read only PDF metadata needed to determine the page count."""
    pdf = pdfium.PdfDocument(str(input_file))
    try:
        return len(pdf)
    finally:
        del pdf


def valid_chunk_output(markdown_file: Path, metadata_file: Path) -> bool:
    """Return True only when both final chunk artifacts are valid."""
    if not markdown_file.exists() or not metadata_file.exists():
        return False

    if not markdown_file.read_text(encoding="utf-8").strip():
        return False

    try:
        metadata = json.loads(
            metadata_file.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError):
        return False

    required = {
        "department",
        "source_file",
        "file_type",
        "source_path",
        "page_start",
        "page_end",
        "chunk_index",
        "total_chunks",
    }

    return required.issubset(metadata)


def parse_large_pdf(input_file: Path) -> int:
    """Parse a large PDF in bounded, resumable Docling page ranges."""
    input_file = input_file.resolve()

    if not input_file.exists():
        raise FileNotFoundError(f"Input PDF not found: {input_file}")

    if input_file.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a PDF input: {input_file}")

    try:
        relative = input_file.relative_to(INPUT_DIR)
    except ValueError as exc:
        raise ValueError(
            f"Input must be inside {INPUT_DIR}: {input_file}"
        ) from exc

    if not relative.parts:
        raise ValueError(f"Could not determine department: {input_file}")

    department = relative.parts[0]
    output_dir = OUTPUT_DIR / department
    output_dir.mkdir(parents=True, exist_ok=True)

    total_pages = get_page_count(input_file)
    total_chunks = ceil(total_pages / CHUNK_SIZE)
    output_stem = normalized_stem(input_file)

    print()
    print("=" * 72)
    print("LARGE PDF MEMORY-SAFE PARSER")
    print("=" * 72)
    print(f"Input        : {input_file}")
    print(f"Department   : {department}")
    print(f"Total pages  : {total_pages}")
    print(f"Chunk size   : {CHUNK_SIZE} pages")
    print(f"Total chunks : {total_chunks}")
    print(f"Output dir   : {output_dir}")
    print("=" * 72)

    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = False

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options
            )
        }
    )

    successful = 0
    skipped = 0
    failed = 0

    for chunk_index in range(1, total_chunks + 1):
        page_start = ((chunk_index - 1) * CHUNK_SIZE) + 1
        page_end = min(chunk_index * CHUNK_SIZE, total_pages)

        markdown_file = (
            output_dir
            / f"{output_stem}_part_{chunk_index:03d}.md"
        )
        metadata_file = (
            output_dir
            / f"{output_stem}_part_{chunk_index:03d}.json"
        )

        if valid_chunk_output(markdown_file, metadata_file):
            skipped += 1
            print(
                f"[{chunk_index:02d}/{total_chunks:02d}] "
                f"Pages {page_start}-{page_end} SKIP "
                f"(already complete)"
            )
            continue

        # Remove stale temporary artifacts from an interrupted previous attempt.
        markdown_tmp = markdown_file.with_name(
            markdown_file.name + ".tmp"
        )
        metadata_tmp = metadata_file.with_name(
            metadata_file.name + ".tmp"
        )

        markdown_tmp.unlink(missing_ok=True)
        metadata_tmp.unlink(missing_ok=True)

        started = time.monotonic()
        result = None
        markdown = None

        temp_pdf = (
            Path("/tmp")
            / f"{output_stem}_part_{chunk_index:03d}.pdf"
        )
        temp_pdf.unlink(missing_ok=True)

        print(
            f"[{chunk_index:02d}/{total_chunks:02d}] "
            f"Pages {page_start}-{page_end} PROCESSING"
        )

        try:
            with input_file.open("rb") as source_handle:
                reader = PdfReader(source_handle)
                writer = PdfWriter()

                for page_number in range(page_start - 1, page_end):
                    writer.add_page(reader.pages[page_number])

                with temp_pdf.open("wb") as chunk_handle:
                    writer.write(chunk_handle)

            reader = None
            writer = None
            gc.collect()

            result = converter.convert(
                temp_pdf,
                raises_on_error=True,
            )

            markdown = result.document.export_to_markdown()

            if not markdown or not markdown.strip():
                raise ValueError(
                    f"Docling produced empty Markdown for pages "
                    f"{page_start}-{page_end}"
                )

            metadata = {
                "department": department,
                "source_file": input_file.name,
                "file_type": "pdf",
                "source_path": str(input_file.relative_to(BASE_DIR)),
                "page_start": page_start,
                "page_end": page_end,
                "chunk_index": chunk_index,
                "total_chunks": total_chunks,
                "total_pdf_pages": total_pages,
            }

            # Write temporary files first. Final files only appear when the
            # complete chunk has been successfully written.
            markdown_tmp.write_text(
                markdown,
                encoding="utf-8",
            )
            metadata_tmp.write_text(
                json.dumps(
                    metadata,
                    indent=2,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            markdown_tmp.replace(markdown_file)
            metadata_tmp.replace(metadata_file)

            elapsed = time.monotonic() - started
            successful += 1

            print(
                f"  ✓ Pages {page_start}-{page_end} "
                f"-> {markdown_file.name} "
                f"({elapsed:.1f}s)"
            )

        except Exception as exc:
            failed += 1
            elapsed = time.monotonic() - started
            print(
                f"  ✗ Pages {page_start}-{page_end} "
                f"FAILED after {elapsed:.1f}s: {exc}"
            )
            print(
                "  Stop here. Re-running this command will resume from "
                "the failed/incomplete chunk."
            )
            return 1

        finally:
            # Release per-chunk objects and remove the temporary PDF.
            result = None
            markdown = None
            temp_pdf.unlink(missing_ok=True)
            gc.collect()

    print()
    print("=" * 72)
    print("PARSING SUMMARY")
    print("=" * 72)
    print(f"Total chunks : {total_chunks}")
    print(f"Processed    : {successful}")
    print(f"Skipped      : {skipped}")
    print(f"Failed       : {failed}")
    print("=" * 72)

    return 0 if failed == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Memory-safe, resumable Docling parser for large PDFs."
    )
    parser.add_argument(
        "input_pdf",
        type=Path,
        help="Path to the large PDF inside data/input/<department>/",
    )
    args = parser.parse_args()

    return parse_large_pdf(args.input_pdf)


if __name__ == "__main__":
    raise SystemExit(main())
