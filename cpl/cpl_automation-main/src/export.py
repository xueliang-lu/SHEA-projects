"""Export helpers (CSV, Excel, PDF).
Author: Sunil Paudel
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, Mapping

import pandas as pd


def export_rows_to_csv(rows: Iterable[Mapping], output_path: str | Path) -> Path:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows)
    if not rows:
        out.write_text("", encoding="utf-8")
        return out

    fieldnames = list(rows[0].keys())
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return out


def export_rows_to_excel(rows: Iterable[Mapping], output_path: str | Path) -> Path:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(list(rows))
    df.to_excel(out, index=False)
    return out


def export_rows_to_pdf(rows: Iterable[Mapping], output_path: str | Path, title: str = "CPL Suggestions Report") -> Path:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    rows_list = list(rows)

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except Exception as exc:
        raise RuntimeError("PDF export requires reportlab. Install with: pip install reportlab") from exc

    c = canvas.Canvas(str(out), pagesize=A4)
    width, height = A4
    y = height - 40
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, title)
    y -= 24

    c.setFont("Helvetica", 9)
    if not rows_list:
        c.drawString(40, y, "No rows available")
    else:
        keys = list(rows_list[0].keys())
        for row in rows_list:
            line = " | ".join(f"{k}: {str(row.get(k, ''))[:35]}" for k in keys[:6])
            c.drawString(40, y, line)
            y -= 14
            if y < 40:
                c.showPage()
                y = height - 40
                c.setFont("Helvetica", 9)

    c.save()
    return out
