# Publication Roadmap: From Draft to Submission

## Step 0 — What quality bar you've already cleared, and what's still optional

Your draft already has the things that most commonly get papers desk-rejected or bounced in first review: checksummed data, predeclared statistical protocols, honest limitations, a real (not incremental-sounding) methodological contribution. Two things are worth doing before submission that aren't scientific — they're professional polish:

1. **A language/clarity pass.** Not because anything is wrong, but reviewers at IJHMT/Applied Thermal Engineering/Physics of Fluids read hundreds of submissions and reward sentences that don't require re-reading. If English is not your first language, most journals explicitly welcome (and some require you to state you've used) a professional editing pass — this is normal, not a weakness signal.
2. **Consistent notation and units throughout.** Walk through every equation and table once, end to end, checking that symbols introduced in Methods match what's used in Results and Discussion, and that units are stated once and used consistently.

Everything else (more trajectories, extended lambda sweep) is the future-work track — genuinely not required for a strong submission at your target tier.

## Step 1 — Choosing the venue (do this before formatting anything)

Given this paper's actual profile — rigorous statistics, a genuine methodological finding (condition-dependence), modest architectural novelty, engineering-motivated application — here's the realistic ranking:

| Venue | Fit | Why |
|---|---|---|
| **International Journal of Heat and Mass Transfer (IJHMT)** | Strong | Direct domain fit (this is the venue whose Zuber lineage and boiling literature you're building on); values rigorous experimental/statistical treatment of thermal-fluid problems; ML-based papers increasingly accepted if physically grounded, which yours is. |
| **Applied Thermal Engineering** | Strong | Similar domain fit, slightly more applications-oriented; good fit for the digital-twin/electronics-cooling framing in your Introduction. |
| **Physics of Fluids** | Good | Values the multiphase-flow physics angle; may want more physical mechanism analysis than a pure ML-benchmark paper offers — your Discussion 5.1 candidate-mechanism paragraph helps here. |
| **Journal of Computational Physics (JCP)** | Moderate-good | Values the numerical-methods/operator-learning angle and statistical rigor; may find the architecture itself (T-FNO + conv branch + divergence loss) too incremental without the condition-dependence framing carrying the paper — lead with that framing explicitly in your cover letter. |
| **NeurIPS Datasets & Benchmarks / ICLR / a SciML workshop** | Conference, not journal, but worth knowing | Your benchmark-and-methodology framing is a very natural fit here if you want faster turnaround and a different audience; workshops in particular are lower-risk, faster, and good for getting community feedback before a journal submission. |

**My recommendation**: submit to **IJHMT or Applied Thermal Engineering first** — best fit for your actual contribution, most realistic acceptance odds at this evidence level, and a faster, less adversarial review process than JCP or a top ML venue for a paper whose core novelty is methodological rather than a brand-new architecture. You can always follow up with an extended version (once Track A/B future work is done) at a higher-tier venue.

**Before you submit anywhere**: post the manuscript to **arXiv** as a preprint. All the venues above permit this, it establishes priority/timestamp on your work, and it lets you share the work immediately with your advisor, collaborators, and the community while formal review proceeds (which can take months).

## Step 2 — Formatting to the target journal's requirements

Every Elsevier journal (IJHMT, Applied Thermal Engineering) uses broadly the same submission system (Editorial Manager) and similar requirements, but check the specific journal's "Guide for Authors" page for exact current numbers:

- **Manuscript template**: Elsevier provides a LaTeX template (`elsarticle` class) and a Word template. Converting your current Markdown draft to one of these is a mechanical but necessary step — do this only after content is finalized, since reformatting after edits is wasted effort.
- **Reference style**: Elsevier journals typically use numbered (Vancouver) or author-date (Harvard) style depending on the specific journal — check the current guide, don't assume.
- **Figures**: submitted as separate high-resolution files (TIFF, EPS, or high-res PNG/PDF), not embedded only in the manuscript text; typical minimum is 300 DPI for photos, 600+ DPI for line art.
- **Word/page limits**: IJHMT and Applied Thermal Engineering don't have hard word limits for full papers but reward conciseness; expect reviewers to push back if the paper reads as unnecessarily padded.
- **Tables**: usually submitted within the manuscript file itself, not as separate files, unless the journal specifies otherwise.

## Step 3 — Required attachments (what you'll actually upload)

Every Elsevier-family journal submission system asks for these as **separate uploaded files**, not sections within the manuscript PDF:

1. **Manuscript** (main text, anonymized if double-blind review is used — check the specific journal's policy).
2. **Cover letter** (provided as `cover_letter.md` — adapt and convert to PDF).
3. **Highlights** (provided as `highlights.md` — required by most Elsevier journals, 3-5 short bullet points).
4. **Graphical abstract** (optional for some journals, required by others — a single image summarizing the paper's core finding; see note below).
5. **Author contribution statement** (CRediT taxonomy — provided as part of `author_statements_and_coi.md`).
6. **Conflict of interest statement** (provided as part of `author_statements_and_coi.md`).
7. **Funding statement** (provided as part of `author_statements_and_coi.md`).
8. **Data availability statement** (provided as part of `author_statements_and_coi.md`).
9. **Supplementary material** (your reproducibility manifest — provided as `reproducibility_manifest.md`, converted into the actual linked/zipped artifacts it describes).
10. **Figures**, as separate high-resolution files (see Step 2).

### On the graphical abstract

I can't generate a publication-quality raster image directly, but I can build you an SVG concept (a clean, journal-style single-panel figure showing the core finding: tutorial-split Pareto trade-off → cross-condition test → reversal) if you want one — say the word and I'll produce it as an artifact you can refine or hand to a designer/co-author with vector graphics tools.

## Step 4 — Packaging the reproducibility artifacts

Journals increasingly expect (and some now require, e.g., via a "reproducibility badge") that code and data be in a permanently citable, publicly accessible location, not just "available upon request":

1. **Create a public GitHub repository** containing: all training/evaluation scripts, configs, the statistical analysis code, and a clear README with setup instructions and pinned dependency versions (`requirements.txt` or `environment.yml`).
2. **Archive it on Zenodo** (free, integrates directly with GitHub, issues a permanent DOI) at the point of submission — this DOI is what you cite in your Data Availability Statement, not a bare GitHub link, since GitHub links can change or disappear but a Zenodo DOI is permanent.
3. **Decide what goes where**: raw checkpoints and full per-seed JSON logs are usually too large/granular for the journal's own supplementary-material upload (most cap around 50-100MB) — host the full artifact set on Zenodo/GitHub, and use the journal's supplementary upload only for the essential summary tables, key figures, and a pointer to the full archive.
4. **Cite the BubbleML dataset's own license terms explicitly** in your Data Availability Statement — you're using their public data, and correctly attributing/licensing it is something reviewers and editors do check.

## Step 5 — The submission process itself

1. Create an account in the target journal's submission system (Editorial Manager for Elsevier journals).
2. Enter manuscript metadata: title, abstract, keywords (5-8, chosen to match how researchers would search for this work — e.g., "neural operator," "Fourier neural operator," "pool boiling," "phase-resolved forecasting," "physics-informed machine learning," "critical heat flux," "conservation laws").
3. Enter author information for every author, in correct order, with affiliations and the corresponding author clearly marked.
4. Upload files in the order the system requests (usually: manuscript, then figures, then supplementary files, then cover letter and statements).
5. **Suggested reviewers**: most journals ask for 3-5 suggested reviewers and allow you to exclude specific people (e.g., direct competitors or collaborators with a conflict). Do not invent names — select real researchers whose work you've actually cited and engaged with substantively in Related Work (e.g., authors of the BubbleML benchmark paper, authors of relevant FNO-variant papers, authors of the boiling-diagnostics IR-thermometry work) — but only after confirming they don't have an undisclosed conflict (e.g., recent co-authorship with you).
6. Submit. You'll receive a manuscript ID and a confirmation email.

## Step 6 — What happens after submission (realistic timeline and what's actually checked)

1. **Technical/editorial check** (days to ~2 weeks): the editorial office checks formatting compliance, completeness of required files, and runs a similarity/plagiarism check (iThenticate or equivalent) — this is where inconsistent citations or accidentally near-verbatim text from a source gets caught, so do a final self-check with your own eyes on anything closely paraphrased from a source paper.
2. **Editor assignment and desk-review decision** (1-3 weeks): the handling editor decides whether the paper is in scope and meets a basic quality bar before sending to reviewers; a poorly scoped submission can be desk-rejected here without full review.
3. **Peer review** (typically 2-4 months, highly variable): 2-3 reviewers are assigned. They will specifically check: whether your statistical claims match your reported numbers (some will spot-check your bootstrap/sign-flip numbers against your supplementary tables), whether your code/data links actually work (a reviewer trying your Zenodo link and finding it broken is a real, avoidable problem — test it yourself before submission), whether your claims are appropriately hedged relative to your evidence (you're well-positioned here given how carefully scoped this draft already is), and whether related work is fairly represented.
4. **Decision**: accept, minor revision, major revision, or reject. Given this paper's profile, **major or minor revision is the realistic best-case first-round outcome** — very few papers are accepted outright at first submission in this field.
5. **Revision**: you'll submit a point-by-point response letter (addressing every reviewer comment explicitly, stating what you changed and where, or arguing respectfully why you didn't) plus a revised manuscript, often with changes highlighted/tracked.
6. **Acceptance and production**: copyediting, proofs sent to you for a final check, then publication (often online-first ahead of a print issue).

Total realistic timeline from submission to publication: commonly 6-12 months for this class of journal, sometimes longer.

## Step 7 — Additional data/analysis a journal is likely to request

Based on everything reviewers in this exact space have flagged throughout this project's own review-simulation exercises, the most likely reviewer requests, roughly in order of likelihood:

1. Clarification or expansion of the lambda_div sensitivity analysis (your future-work Track A directly anticipates this).
2. A request to expand the cross-condition test's statistical power (Track B) — be ready to either have this done, or to respond convincingly that it's appropriately scoped as future work given the honest limitations already stated.
3. A request for at least one additional baseline (commonly a transformer-based operator) — you can preempt some of this by explicitly naming Bubbleformer as related-but-not-benchmarked future work, which you already do.
4. A request to clarify or expand the physical-mechanism explanation in Discussion 5.1 with more direct evidence (e.g., visualized divergence fields) — this is realistically addressable with a modest figure addition even before Track A/B are done.
5. Minor requests: define every acronym on first use (a common, easy-to-fix reviewer comment), verify all citations have correct DOIs, ensure Figure/Table numbering is consistent throughout.

None of these should be surprising if they come — you've already anticipated most of them in your own Limitations section, which is exactly what you want a reviewer to notice.

## Step 8 — Copyright, licensing, and open access

- Elsevier journals typically require either a **copyright transfer** (traditional, no fee, but publisher controls distribution) or an **open-access (CC-BY) license** (usually involves an article processing charge, often substantial — check whether your institution has a read-and-publish agreement that covers this, or whether Elevon TechionX or BUET has relevant funds/agreements).
- Posting to arXiv **before and during** review is compatible with both models at Elsevier journals — this is not the same as the final publisher version and doesn't count as prior publication for these venues, but always double check the specific journal's current policy since these change.
