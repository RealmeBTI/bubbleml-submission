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
        r"\begin{longtable}[]{@{}P{0.25\textwidth}P{0.55\textwidth}P{0.14\textwidth}@{}}",
        1,
    )
    latex = latex.replace(
        three_column,
        r"\begin{longtable}[]{@{}P{0.25\textwidth}P{0.33\textwidth}P{0.29\textwidth}@{}}",
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
    latex = re.sub(
        r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}",
        r"\\includegraphics[width=\\linewidth]{\1}",
        latex,
    )
    # Convert the six audited Markdown image-plus-caption blocks into real
    # LaTeX figures so every substantive manuscript reference resolves through
    # an explicit label.  This avoids relying on manually typed figure numbers.
    figures = {
        "fig1_pareto_front.pdf": (1, "fig:pareto-tradeoff"),
        "fig6_split_design.pdf": (2, "fig:split-design"),
        "fig5_benchmark_workflow.pdf": (3, "fig:benchmark-workflow"),
        "fig3_lambda_sensitivity.pdf": (4, "fig:lambda-sensitivity"),
        "fig2_dry_area_trace.pdf": (5, "fig:dry-area-traces"),
        "fig4_loss_curves.pdf": (6, "fig:training-histories"),
    }
    for filename, (number, label) in figures.items():
        pattern = re.compile(
            rf"\\pandocbounded\{{(?P<image>\\includegraphics\[width=\\linewidth\]\{{(?P<path>[^}}]*{re.escape(filename)})\}})\}}"
            rf"\n\n\\textbf\{{Figure {number}\.\}} (?P<caption>.*?)(?=\n\n)",
            flags=re.DOTALL,
        )

        def figure_replacement(match: re.Match[str]) -> str:
            return (
                "\\begin{figure}[htbp]\n"
                "\\centering\n"
                f"{match.group('image')}\n"
                f"\\caption{{{match.group('caption')}}}\n"
                f"\\label{{{label}}}\n"
                "\\end{figure}"
            )

        latex, replacements = pattern.subn(figure_replacement, latex)
        if replacements != 1:
            raise RuntimeError(f"Expected one Figure {number} block for {filename}; found {replacements}.")
    for filename, (number, label) in figures.items():
        latex = latex.replace(f"Figure {number}", rf"Figure~\ref{{{label}}}")
    # Pandoc marks captionless longtables with LTcaptype=none. The longtable
    # package requires a real counter name there, so the generated elsarticle
    # source aborts at the first Markdown table unless this invalid override is
    # removed. The surrounding group remains harmless.
    latex = latex.replace(r"{\def\LTcaptype{none} % do not increment counter", "{")
    # pdflatex does not define the Unicode minus and multiplication characters
    # emitted by Pandoc in ordinary prose.  The LaTeX forms below are valid in
    # both text and math contexts (including dimensions in table cells).
    latex = latex.replace("−", "-").replace("×", r"\ensuremath{\times}")
    named_citations = {
        r"Zuber\textquotesingle s hydrodynamic instability model": r"Zuber\textquotesingle s hydrodynamic instability model\cite{zuber1959hydrodynamic}",
        "The BubbleML dataset,": r"The BubbleML dataset\cite{hassan2023bubbleml},",
        "The Fourier Neural Operator performs": r"The Fourier Neural Operator\cite{li2021fno} performs",
        "Convolutional U-Net architectures": r"Convolutional U-Net architectures\cite{ronneberger2015unet}",
        "axis-factorized FNO (F-FNO)": r"axis-factorized FNO (F-FNO)\cite{tran2023ffno}",
        "U-shaped FNO (UNO)": r"U-shaped FNO (UNO)\cite{rahman2022uno}",
        "Bubbleformer) benchmarked": r"Bubbleformer\cite{hassan2025bubbleformer}) benchmarked",
        "Dunlap et al. (2026)": r"Dunlap et al. (2026)\cite{dunlap2026open}",
        "Ravichandran et al. (2021)": r"Ravichandran et al. (2021)\cite{ravichandran2021decrypting}",
        "Ravichandran et al. (2023)": r"Ravichandran et al. (2023)\cite{ravichandran2023dryareas}",
        "Kalimuthu et al. (2025)": r"Kalimuthu et al. (2025)\cite{kalimuthu2025loglo}",
        "Richter-Powell et al. (2022)": r"Richter-Powell et al. (2022)\cite{richterpowell2022neural}",
        "Li et al. (2026)": r"Li et al. (2026)\cite{li2026project}",
    }
    for text, citation in named_citations.items():
        latex = latex.replace(text, citation)
    destination.write_text(latex, encoding="utf-8")
    print(destination)


if __name__ == "__main__":
    main()
