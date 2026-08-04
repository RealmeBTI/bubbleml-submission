# Cover Letter

[Date]

Dear Editor,

We are pleased to submit our manuscript, "A Physics-Aware Benchmark for Phase-Resolved Neural Operator Learning in Boiling Flows: Statistically Rigorous Evidence for Condition-Dependent Architecture Trade-offs," for consideration for publication in [Journal Name].

Pool boiling is central to high-power electronics cooling, data-center thermal management, and nuclear thermal-hydraulics, and neural operator surrogates offer a promising route to fast, CFD-quality forecasting for these applications. Prior benchmark work (BubbleML, NeurIPS 2023) established that standard Fourier Neural Operators underperform convolutional baselines on boiling temperature forecasting, but — to our knowledge — no published study has systematically tested whether an architecture comparison established on one boiling trajectory generalizes to independently held-out physical conditions from the same source data.

This is the central question our manuscript addresses. We show, using a statistically rigorous multi-seed protocol (paired bootstrap intervals, exact sign-flip tests, Holm-Bonferroni correction), that a confirmed architecture trade-off between interface-temperature fidelity (favoring a Tucker-factorized Fourier Neural Operator) and mass-conservation accuracy (favoring a U-Net baseline) on one trajectory does not reproduce when tested on two independently held-out physical conditions from the same dataset. We further show that a predeclared, physically motivated conservation intervention (a spectral velocity-divergence penalty) partially transfers across this condition shift where a purely architectural intervention does not.

We believe this is a valuable and, to our knowledge, novel methodological contribution to the growing literature on neural operators for multiphysics simulation: it provides direct, controlled evidence that single-trajectory benchmarking — even when analyzed with rigorous per-seed statistics — is insufficient to establish a generalizable architectural claim in this domain, and it demonstrates a concrete replication-check methodology that we believe should become standard practice for future work in this area.

The manuscript also reports and corrects a previously unreported evaluation pitfall (physically invalid phase-indicator outputs under autoregressive rollout) and demonstrates a predeclared statistical decision-gate methodology that we use to correctly reject a promising but non-replicating single-seed observation before committing further engineering effort to it.

All data, code, model checkpoints, and statistical analysis scripts are made publicly available and permanently archived (see Data Availability Statement), and every claim in the manuscript is explicitly scoped to what our statistical evidence actually supports — we have been careful throughout to distinguish confirmatory findings from descriptive, directionally-consistent-but-unconfirmed observations.

This manuscript is not under consideration elsewhere. All authors have approved the manuscript for submission and have no conflicts of interest to declare [update if applicable]. A preprint version [is / will be] available on arXiv [add link once posted].

We believe this work will be of interest to [Journal Name]'s readership working at the intersection of computational thermal-fluid sciences and scientific machine learning, and we thank you for your consideration.

Sincerely,

[Corresponding Author Name]
[Affiliation]
[Email]
[On behalf of all co-authors]

---

*Notes for the author before sending: replace all bracketed placeholders; confirm the journal name and tailor paragraph 5 ("we believe this work will be of interest...") to reference that specific journal's stated scope; confirm arXiv posting status; list any actual conflicts of interest or funding sources explicitly rather than leaving the placeholder.*
