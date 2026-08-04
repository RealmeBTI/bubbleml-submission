#!/usr/bin/env python3
"""Create clean review PDFs from supplied Markdown without changing its claims."""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate, Frame, KeepTogether, ListFlowable, ListItem, PageTemplate, Paragraph, PageBreak, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parents[1]
FONT = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
pdfmetrics.registerFont(TTFont("SubmissionSans", FONT))
pdfmetrics.registerFont(TTFont("SubmissionSans-Bold", FONT_BOLD))


def styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("Title", parent=base["Title"], fontName="SubmissionSans-Bold", fontSize=17, leading=21, spaceAfter=18, textColor=colors.HexColor("#14213d")),
        "h1": ParagraphStyle("H1", parent=base["Heading1"], fontName="SubmissionSans-Bold", fontSize=15, leading=18, spaceBefore=12, spaceAfter=8, textColor=colors.HexColor("#14213d")),
        "h2": ParagraphStyle("H2", parent=base["Heading2"], fontName="SubmissionSans-Bold", fontSize=12, leading=15, spaceBefore=10, spaceAfter=6, textColor=colors.HexColor("#1f4e79")),
        "h3": ParagraphStyle("H3", parent=base["Heading3"], fontName="SubmissionSans-Bold", fontSize=10.5, leading=13, spaceBefore=8, spaceAfter=5),
        "body": ParagraphStyle("Body", parent=base["BodyText"], fontName="SubmissionSans", fontSize=9.4, leading=13, spaceAfter=7, alignment=TA_LEFT),
        "note": ParagraphStyle("Note", parent=base["BodyText"], fontName="SubmissionSans", fontSize=8.4, leading=11.5, spaceAfter=7, textColor=colors.HexColor("#555555")),
        "bullet": ParagraphStyle("Bullet", parent=base["BodyText"], fontName="SubmissionSans", fontSize=9.2, leading=12.5, leftIndent=10),
        "table": ParagraphStyle("Table", parent=base["BodyText"], fontName="SubmissionSans", fontSize=7.4, leading=9.5),
        "table_head": ParagraphStyle("TableHead", parent=base["BodyText"], fontName="SubmissionSans-Bold", fontSize=7.4, leading=9.5, textColor=colors.white),
    }


def inline(text: str) -> str:
    value = html.escape(text, quote=False)
    value = re.sub(r"`([^`]+)`", r"<font name='Courier'>\1</font>", value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", value)
    value = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", value)
    return value


def markdown_flowables(text: str, *, first_title: bool = True):
    style = styles()
    lines = text.splitlines()
    story = []
    index = 0
    title_used = False
    while index < len(lines):
        raw = lines[index].rstrip()
        stripped = raw.strip()
        if not stripped or stripped == "---":
            index += 1
            continue
        if stripped.startswith("|") and index + 1 < len(lines) and re.match(r"^\s*\|?\s*:?-+", lines[index + 1]):
            table_lines = [stripped]
            index += 2
            while index < len(lines) and lines[index].strip().startswith("|"):
                table_lines.append(lines[index].strip())
                index += 1
            rows = [[cell.strip() for cell in line.strip("|").split("|")] for line in table_lines]
            data = [[Paragraph(inline(cell), style["table_head"] if row_index == 0 else style["table"]) for cell in row] for row_index, row in enumerate(rows)]
            available = 7.0 * inch
            count = max(len(row) for row in rows)
            widths = [available / count] * count
            table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#b8c4d1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f7fa")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.extend([table, Spacer(1, 9)])
            continue
        heading = re.match(r"^(#{1,3})\s+(.*)$", stripped)
        if heading:
            level, value = len(heading.group(1)), heading.group(2)
            key = "title" if level == 1 and first_title and not title_used else f"h{level}"
            story.append(Paragraph(inline(value), style[key]))
            title_used = title_used or level == 1
            index += 1
            continue
        if re.match(r"^[-*]\s+", stripped):
            items = []
            while index < len(lines) and re.match(r"^\s*[-*]\s+", lines[index]):
                value = re.sub(r"^\s*[-*]\s+", "", lines[index]).strip()
                items.append(ListItem(Paragraph(inline(value), style["bullet"]), leftIndent=13))
                index += 1
            story.append(ListFlowable(items, bulletType="bullet", start="circle", leftIndent=18, bulletFontName="SubmissionSans"))
            story.append(Spacer(1, 6))
            continue
        paragraph = [stripped]
        index += 1
        while index < len(lines):
            candidate = lines[index].strip()
            if not candidate or candidate == "---" or candidate.startswith("#") or candidate.startswith("|") or re.match(r"^[-*]\s+", candidate):
                break
            paragraph.append(candidate)
            index += 1
        joined = " ".join(paragraph)
        note = joined.startswith("*") and joined.endswith("*")
        story.append(Paragraph(inline(joined), style["note" if note else "body"]))
    return story


def footer(canvas, document):
    canvas.saveState()
    canvas.setFont("SubmissionSans", 8)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawString(0.72 * inch, 0.45 * inch, "BubbleML submission package - generated from supplied source")
    canvas.drawRightString(7.78 * inch, 0.45 * inch, f"Page {document.page}")
    canvas.restoreState()


def build(markdowns: list[Path], destination: Path, *, page_breaks: bool = False) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    document = BaseDocTemplate(str(destination), pagesize=letter, leftMargin=0.72*inch, rightMargin=0.72*inch, topMargin=0.68*inch, bottomMargin=0.72*inch, title=markdowns[0].stem.replace("_", " ").title(), author="[Author information required]")
    frame = Frame(document.leftMargin, document.bottomMargin, document.width, document.height, id="normal")
    document.addPageTemplates([PageTemplate(id="submission", frames=[frame], onPage=footer)])
    story = []
    for index, path in enumerate(markdowns):
        if index and page_breaks:
            story.append(PageBreak())
        story.extend(markdown_flowables(path.read_text(encoding="utf-8")))
    document.build(story)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("output/pdf"))
    args = parser.parse_args()
    output = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    attachments = ROOT / "submission/attachments"
    for name in ("cover_letter", "highlights", "author_statements_and_coi", "reproducibility_manifest", "submission_roadmap"):
        build([attachments / f"{name}.md"], output / f"{name}.pdf")
    supplementary = [
        attachments / "reproducibility_manifest.md",
        ROOT / "submission/supplementary/statistical_audit_note.md",
        ROOT / "submission/supplementary/runtime_environment.md",
        ROOT / "REPRODUCIBILITY_SELFTEST.md",
        ROOT / "CHECKSUMS.md",
        ROOT / "ARTIFACT_GAPS.md",
        ROOT / "BIBLIOGRAPHY_VERIFICATION.md",
        ROOT / "FIGURE_QA.md",
    ]
    build(supplementary, output / "supplementary_material.pdf", page_breaks=True)
    print(f"Generated PDFs in {output}")


if __name__ == "__main__":
    main()
