"""
FILE: backend/parser.py
Extracts raw text from uploaded documents: PDF, TXT, CSV.
Uses PyMuPDF for PDF, standard libs for others.
"""

import io
import csv
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF bytes using PyMuPDF (fitz)."""
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(stream=file_bytes, filetype="pdf")
        page_count = len(doc)

        text_parts = []

        for page_num in range(page_count):
            page = doc[page_num]
            text = page.get_text("text")

            if text and text.strip():
                text_parts.append(
                    f"--- Page {page_num + 1} ---\n{text}"
                )

        full_text = "\n\n".join(text_parts)

        logger.info(
            f"Extracted {len(full_text)} characters from PDF ({page_count} pages)"
        )

        doc.close()

        return full_text

    except ImportError:
        logger.error("PyMuPDF not installed. Run: pip install PyMuPDF")
        raise RuntimeError(
            "PyMuPDF (fitz) is required for PDF parsing. Install with: pip install PyMuPDF"
        )

    except Exception as e:
        logger.exception("PDF extraction failed")
        raise RuntimeError(f"Failed to extract text from PDF: {e}")


def extract_text_from_txt(file_bytes: bytes) -> str:
    """Extract text from TXT file bytes."""
    encodings = ["utf-8", "utf-16", "latin-1", "cp1252"]
    for enc in encodings:
        try:
            text = file_bytes.decode(enc)
            logger.info(f"Decoded TXT with encoding: {enc}")
            return text
        except (UnicodeDecodeError, LookupError):
            continue
    raise RuntimeError("Could not decode text file with any supported encoding.")


def extract_text_from_csv(file_bytes: bytes) -> str:
    """
    Extract text from CSV, formatting it as a readable table
    so the AI can parse financial rows/columns.
    """
    try:
        text = file_bytes.decode("utf-8", errors="replace")
        reader = csv.DictReader(io.StringIO(text))
        lines = []

        headers = reader.fieldnames
        if headers:
            lines.append("Financial Data Table:")
            lines.append(" | ".join(str(h) for h in headers))
            lines.append("-" * 80)

        for row in reader:
            line = " | ".join(f"{k}: {v}" for k, v in row.items())
            lines.append(line)

        result = "\n".join(lines)
        logger.info(f"Extracted {len(lines)} rows from CSV")
        return result

    except Exception as e:
        logger.error(f"CSV extraction failed: {e}")
        raise RuntimeError(f"Failed to parse CSV: {e}")


def extract_text_from_file(
    file_bytes: bytes,
    file_extension: str,
    company_name: Optional[str] = None
) -> str:
    """
    Router: dispatches to the correct extractor based on file extension.
    Returns raw text string.
    """
    ext = file_extension.lower().strip(".")

    if ext == "pdf":
        raw_text = extract_text_from_pdf(file_bytes)
    elif ext in ("txt", "text"):
        raw_text = extract_text_from_txt(file_bytes)
    elif ext == "csv":
        raw_text = extract_text_from_csv(file_bytes)
    else:
        # Try PDF first, fallback to TXT
        try:
            raw_text = extract_text_from_pdf(file_bytes)
        except Exception:
            raw_text = extract_text_from_txt(file_bytes)

    # Prepend company name hint for AI context
    if company_name:
        header = f"Company under analysis: {company_name}\n\n"
        raw_text = header + raw_text

    return raw_text
