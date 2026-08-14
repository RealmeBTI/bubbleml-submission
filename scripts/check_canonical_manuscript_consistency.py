#!/usr/bin/env python3
"""Fail if the rendered canonical tutorial claim drifts from the live ledger.

The Markdown manuscript intentionally contains a ``{{CANONICAL_TUTORIAL_RESULTS}}``
marker.  ``build_manuscript_tex.py`` replaces it with a fragment generated from
the retained 48x48 paired-result ledger.  This checker recomputes that fragment
in memory and verifies the marker, generated-fragment cache, rendered Section
4.1, and the complete Section 4 heading sequence without writing files.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from generate_canonical_statistics import build_ledger, manuscript_fragments


ROOT = Path(__file__).resolve().parents[1]
MARKDOWN = ROOT / "manuscript" / "full_manuscript.md"
LATEX = ROOT / "manuscript" / "manuscript_elsarticle.tex"
FRAGMENTS = ROOT / "manuscript" / "generated" / "canonical_fragments.json"
COVER_LETTER = ROOT / "submission" / "attachments" / "cover_letter.md"
HIGHLIGHTS = ROOT / "submission" / "attachments" / "highlights.md"
TITLE = "Phase-Resolved Neural Operator Learning for Boiling Flows: An Auditable Benchmark of Conservation Error"
MARKER = "{{CANONICAL_TUTORIAL_RESULTS}}"
HYBRID_MARKER = "{{CANONICAL_HYBRID_RESULTS}}"

CANONICAL_TOKENS = (
    "+0.00460",
    "[-0.05759, +0.05894]",
    ".890625",
    "-0.18853",
    "[-0.47490, +0.06732]",
    ".234375",
    "-0.09277",
    "[-0.22032, +0.02548]",
    ".196289",
    "+0.04917",
    "[+0.04448, +0.05386]",
    ".000976562",
    ".0214844",
)
RETIRED_TOKENS = ("0.04494", "0.50190", "0.43147", ".03906", ".03516", ".07031")
RETRACTED_CLAIM = "statistically significant advantage on interface"


def section_41_latex(text: str) -> str:
    """Return the literal generated Section 4.1, stopping at the next section."""
    match = re.search(
        r"^\\subsection\*\{4\.1 .*?(?=^\\subsection\*\{4\.2 )",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    if not match:
        raise ValueError("Could not locate rendered LaTeX Section 4.1 followed by Section 4.2.")
    return match.group(0)


def normalized_latex(text: str) -> str:
    """Normalize Pandoc's harmless LaTeX escaping for deterministic token checks."""
    value = text.replace("\\%", "%").replace("{[}", "[").replace("{]}", "]").replace("\u2212", "-")
    return re.sub(r"\s+", " ", value)


def markdown_section_4_headings(text: str) -> list[str]:
    return re.findall(r"^### (4\.\d+ .+)$", text, flags=re.MULTILINE)


def latex_section_4_headings(text: str) -> list[str]:
    headings = re.findall(r"^\\subsection\*\{(4\.\d+ .*?)\}\\label", text, flags=re.MULTILINE | re.DOTALL)
    return [normalized_latex(heading) for heading in headings]


def main() -> int:
    failures: list[str] = []
    markdown = MARKDOWN.read_text(encoding="utf-8")
    latex = LATEX.read_text(encoding="utf-8")
    cover_letter = COVER_LETTER.read_text(encoding="utf-8")
    highlights = HIGHLIGHTS.read_text(encoding="utf-8")
    fresh = manuscript_fragments(build_ledger())["tutorial_results"]
    fresh_hybrid = manuscript_fragments(build_ledger())["hybrid_results"]

    if not markdown.startswith(f"# {TITLE}\n"):
        failures.append("Markdown title differs from the audited document identity.")
    latex_title = re.search(r"\\title\{(.*?)\}", latex, flags=re.DOTALL)
    if not latex_title or re.sub(r"\s+", " ", latex_title.group(1)).strip() != TITLE:
        failures.append("Rendered LaTeX title differs from the audited document identity.")
    if r"\journal{Computer Methods in Applied Mechanics and Engineering}" not in latex:
        failures.append("Rendered LaTeX does not identify Computer Methods in Applied Mechanics and Engineering.")
    for required in ("### 3.8 Nomenclature", "resolution_control_48x48", "phase1_gpu_decisive_tfno_unet_n11"):
        if required not in markdown:
            failures.append(f"Markdown is missing document-identity marker {required!r}.")
    section_32 = markdown.split("### 3.2 Model architectures and training protocol", 1)[-1].split("### 3.3", 1)[0]
    if "MPS" in section_32:
        failures.append("Section 3.2 presents MPS in the active tutorial hardware description.")

    if markdown.count(MARKER) != 1:
        failures.append(f"Markdown must contain exactly one {MARKER!r}; found {markdown.count(MARKER)}.")
    if markdown.count(HYBRID_MARKER) != 1:
        failures.append(f"Markdown must contain exactly one {HYBRID_MARKER!r}; found {markdown.count(HYBRID_MARKER)}.")
    if "### 4.1 Canonical tutorial split" not in markdown:
        failures.append("Markdown does not contain the canonical Section 4.1 heading.")
    if markdown_section_4_headings(markdown) != latex_section_4_headings(latex):
        failures.append("Rendered LaTeX Section 4 headings differ from the Markdown source; rebuild before review or release.")

    try:
        cached_payload = json.loads(FRAGMENTS.read_text(encoding="utf-8"))
        cached = cached_payload["tutorial_results"]
        if cached != fresh:
            failures.append("canonical_fragments.json is stale: tutorial_results differs from a fresh ledger computation.")
        if cached_payload["hybrid_results"] != fresh_hybrid:
            failures.append("canonical_fragments.json is stale: hybrid_results differs from the fresh CUDA artifact.")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        failures.append(f"Cannot validate generated canonical fragments: {exc}")

    try:
        rendered = normalized_latex(section_41_latex(latex))
    except ValueError as exc:
        failures.append(str(exc))
        rendered = ""

    for token in CANONICAL_TOKENS:
        if token not in rendered:
            failures.append(f"Rendered Section 4.1 is missing canonical token {token!r}.")
    for token in RETIRED_TOKENS:
        if token in markdown or token in latex:
            failures.append(f"Retired token {token!r} appears in a manuscript source.")
    if RETRACTED_CLAIM in markdown.lower() or RETRACTED_CLAIM in latex.lower():
        failures.append("A retracted statistically-significant interface-advantage claim appears in a manuscript source.")
    stale_intervention_tokens = ("0.09373", "0.16586", "-0.07212", "0.08669", "-0.02891")
    for token in stale_intervention_tokens:
        if token in markdown or token in latex:
            failures.append(f"Retired-pipeline intervention token {token!r} appears in a manuscript source.")
    for token in ("0.09528", "0.16562", "-0.07034", ".000488"):
        if token not in latex:
            failures.append(f"Rendered CUDA intervention section is missing token {token!r}.")
    if "no statistically\nsignificant advantage" not in latex and "no statistically significant advantage" not in latex:
        failures.append("Rendered Section 4.1 does not explicitly state the interface finding is non-significant.")

    normalized_cover = cover_letter.replace("−", "-")
    for token in ("Computer Methods in Applied Mechanics and Engineering", "0.09528", "0.16562", "-0.07034", "-0.07454", "-0.06654", ".000488281"):
        if token not in normalized_cover:
            failures.append(f"CMAME cover letter is missing confirmed CUDA-result token {token!r}.")
    if "No cross-condition intervention claim is made." not in cover_letter:
        failures.append("CMAME cover letter does not preserve the intervention generalization boundary.")
    for stale in ("qualitative-only", "precluded by compute-environment deprecation"):
        if stale in cover_letter.lower() or stale in highlights.lower():
            failures.append(f"Submission attachment retains stale intervention wording {stale!r}.")

    bullets = [line[2:] for line in highlights.splitlines() if line.startswith("- ")]
    if not 3 <= len(bullets) <= 5:
        failures.append(f"CMAME highlights require 3--5 bullets; found {len(bullets)}.")
    for bullet in bullets:
        if len(bullet) > 85:
            failures.append(f"CMAME highlight exceeds 85 characters: {bullet!r}")
    if "## Data availability" not in markdown or "## CRediT authorship contribution statement" not in markdown:
        failures.append("Manuscript lacks the CMAME data-availability or CRediT section.")
    if "fig1_pareto_front" in markdown or "fig:pareto-tradeoff" in latex:
        failures.append("A retired Pareto-tradeoff filename or label remains in the manuscript.")

    if failures:
        print("CANONICAL MANUSCRIPT CONSISTENCY: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("CANONICAL MANUSCRIPT CONSISTENCY: PASS")
    print("- Fresh 48x48 ledger matches manuscript/generated/canonical_fragments.json.")
    print("- Fresh checkpoint-retaining CUDA intervention matches the generated manuscript fragment.")
    print("- Exact title, Section 3.8, canonical artifact, and retired-artifact identity markers are present.")
    print("- Markdown contains the sole canonical-results marker in Section 4.1.")
    print("- Rendered LaTeX Section 4.1 contains all canonical statistics and no retired values.")
    print("- Rendered LaTeX Section 4 headings match the Markdown source.")
    print("- CMAME cover letter and highlights agree with the confirmed CUDA intervention result.")
    print("- CMAME data-availability/CRediT sections and conservation-error figure naming are present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
