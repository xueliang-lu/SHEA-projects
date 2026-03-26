"""Transcript extraction utilities for text-based PDFs.

Tries pdfplumber first, then falls back to PyMuPDF (fitz).
Returns structured extraction results and never raises on expected parse failures.
Author: Sunil Paudel
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class ExtractionResult:
    success: bool
    text: str
    page_count: int
    method: str
    warnings: List[str]
    error: Optional[str] = None


def _extract_with_pdfplumber(path: Path) -> ExtractionResult:
    warnings: List[str] = []
    try:
        import pdfplumber  # type: ignore
    except Exception as exc:  # pragma: no cover
        return ExtractionResult(False, "", 0, "pdfplumber", warnings, f"pdfplumber unavailable: {exc}")

    try:
        pages_text: List[str] = []
        with pdfplumber.open(str(path)) as pdf:
            for idx, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text() or ""
                if not page_text.strip():
                    warnings.append(f"Page {idx} contains no extractable text (possible scan/image).")
                pages_text.append(page_text)
        all_text = "\n\n".join(pages_text).strip()
        return ExtractionResult(
            success=bool(all_text),
            text=all_text,
            page_count=len(pages_text),
            method="pdfplumber",
            warnings=warnings,
            error=None if all_text else "No text could be extracted by pdfplumber.",
        )
    except Exception as exc:
        return ExtractionResult(False, "", 0, "pdfplumber", warnings, str(exc))


def _extract_with_pymupdf(path: Path) -> ExtractionResult:
    warnings: List[str] = []
    try:
        import fitz  # type: ignore
    except Exception as exc:  # pragma: no cover
        return ExtractionResult(False, "", 0, "pymupdf", warnings, f"PyMuPDF unavailable: {exc}")

    try:
        doc = fitz.open(str(path))
        pages_text: List[str] = []
        for idx, page in enumerate(doc, start=1):
            page_text = page.get_text("text") or ""
            if not page_text.strip():
                warnings.append(f"Page {idx} contains no extractable text (possible scan/image).")
            pages_text.append(page_text)
        doc.close()

        all_text = "\n\n".join(pages_text).strip()
        return ExtractionResult(
            success=bool(all_text),
            text=all_text,
            page_count=len(pages_text),
            method="pymupdf",
            warnings=warnings,
            error=None if all_text else "No text could be extracted by PyMuPDF.",
        )
    except Exception as exc:
        return ExtractionResult(False, "", 0, "pymupdf", warnings, str(exc))


def _extract_with_ocr(path: Path) -> ExtractionResult:
    warnings: List[str] = []
    try:
        import fitz  # type: ignore
        import pytesseract  # type: ignore
        from PIL import Image  # type: ignore
    except Exception as exc:  # pragma: no cover
        return ExtractionResult(False, "", 0, "ocr", warnings, f"OCR unavailable: {exc}")

    try:
        doc = fitz.open(str(path))
        pages_text: List[str] = []
        for idx, page in enumerate(doc, start=1):
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            text = pytesseract.image_to_string(img) or ""
            if not text.strip():
                warnings.append(f"Page {idx}: OCR found little/no text.")
            pages_text.append(text)
        doc.close()
        all_text = "\n\n".join(pages_text).strip()
        return ExtractionResult(
            success=bool(all_text),
            text=all_text,
            page_count=len(pages_text),
            method="ocr",
            warnings=warnings,
            error=None if all_text else "OCR could not extract text.",
        )
    except Exception as exc:
        return ExtractionResult(False, "", 0, "ocr", warnings, str(exc))


def extract_header_text_via_ocr(path: str | Path) -> str:
    """OCR only first-page header area, useful for logo/header institution text."""
    pdf_path = Path(path)
    try:
        import fitz  # type: ignore
        import pytesseract  # type: ignore
        from PIL import Image  # type: ignore
    except Exception:
        return ""

    try:
        doc = fitz.open(str(pdf_path))
        if len(doc) == 0:
            return ""
        page = doc[0]
        rect = page.rect
        header = fitz.Rect(rect.x0, rect.y0, rect.x1, rect.y0 + rect.height * 0.28)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), clip=header)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        text = pytesseract.image_to_string(img) or ""
        doc.close()
        return text.strip()
    except Exception:
        return ""


def extract_transcript_text(path: str | Path) -> ExtractionResult:
    """Extract text from transcript PDF with graceful fallback behavior."""
    pdf_path = Path(path)
    if not pdf_path.exists():
        return ExtractionResult(False, "", 0, "none", [], f"File not found: {pdf_path}")
    if pdf_path.suffix.lower() != ".pdf":
        return ExtractionResult(False, "", 0, "none", [], "Only PDF files are supported.")

    result = _extract_with_pdfplumber(pdf_path)
    if result.success:
        return result

    fallback = _extract_with_pymupdf(pdf_path)
    warnings = result.warnings + fallback.warnings
    if fallback.success:
        fallback.warnings = warnings
        return fallback

    ocr = _extract_with_ocr(pdf_path)
    warnings += ocr.warnings
    if ocr.success:
        ocr.warnings = warnings
        return ocr

    return ExtractionResult(
        success=False,
        text="",
        page_count=max(result.page_count, fallback.page_count, ocr.page_count),
        method="none",
        warnings=warnings,
        error=f"pdfplumber failed: {result.error}; PyMuPDF failed: {fallback.error}; OCR failed: {ocr.error}",
    )
