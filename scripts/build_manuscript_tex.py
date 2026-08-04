#!/usr/bin/env python3
"""Convert the supplied Markdown manuscript to an elsarticle source file."""

from __future__ import annotations

import argparse
import re
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TITLE = "A Physics-Aware Benchmark for Phase-Resolved Neural Operator Learning in Boiling Flows: Statistically Rigorous Evidence for Condition-Dependent Architecture Trade-offs"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pandoc", default="pandoc")
    args = parser.parse_args()
    source = ROOT / "manuscript/full_manuscript.md"
    template = ROOT / "manuscript/elsarticle_template.tex"
    destination = ROOT / "manuscript/manuscript_elsarticle.tex"
    text = source.read_text(encoding="utf-8")
    first, separator, body = text.partition("\n")
    expected = f"# {TITLE}"
    if first != expected or not separator:
        raise RuntimeError("Manuscript title differs from the audited title; conversion stopped.")
    marker = "## Abstract\n\n"
    if marker not in body:
        raise RuntimeError("Abstract heading not found.")
    before, abstract_and_body = body.split(marker, 1)
    abstract_text, body_after_abstract = abstract_and_body.split("\n---\n", 1)
    # The source's opening italic warning is retained in the body after the abstract.
    pandoc_input = before + "\n---\n" + body_after_abstract
    with tempfile.TemporaryDirectory(prefix="bubbleml-pandoc-") as directory:
        temporary = Path(directory) / "body.md"
        temporary.write_text(pandoc_input, encoding="utf-8")
        subprocess.run(
            [
                args.pandoc,
                str(temporary),
                "--from=gfm+tex_math_dollars",
                "--to=latex",
                "--standalone",
                "--shift-heading-level-by=-1",
                f"--template={template}",
                f"--metadata=title:{TITLE}",
                f"--metadata=abstract:{abstract_text.strip()}",
                f"--output={destination}",
            ],
            cwd=ROOT / "manuscript",
            check=True,
        )
    latex = destination.read_text(encoding="utf-8")
    three_column = r"\begin{longtable}[]{@{}lll@{}}"
    five_column = r"\begin{longtable}[]{@{}lrrrr@{}}"
    latex = latex.replace(
        three_column,
        r"\begin{longtable}[]{@{}P{0.22\textwidth}P{0.58\textwidth}P{0.14\textwidth}@{}}",
        1,
    )
    latex = latex.replace(
        three_column,
        r"\begin{longtable}[]{@{}P{0.18\textwidth}P{0.47\textwidth}P{0.27\textwidth}@{}}",
        1,
    )
    latex = latex.replace(
        five_column,
        r"\begin{longtable}[]{@{}P{0.20\textwidth}P{0.13\textwidth}P{0.18\textwidth}P{0.19\textwidth}P{0.16\textwidth}@{}}",
        1,
    )
    latex = latex.replace(
        five_column,
        r"\begin{longtable}[]{@{}P{0.18\textwidth}P{0.21\textwidth}P{0.15\textwidth}P{0.17\textwidth}P{0.16\textwidth}@{}}",
        1,
    )
    latex = re.sub(
        r"\\texttt\{([0-9a-f]{64})\}",
        lambda match: r"\texttt{\seqsplit{" + match.group(1) + "}}",
        latex,
    )
    latex = re.sub(r"\\(sub)*section\{", lambda match: "\\" + (match.group(1) or "") + "section*{", latex)
    destination.write_text(latex, encoding="utf-8")
    print(destination)


if __name__ == "__main__":
    main()
