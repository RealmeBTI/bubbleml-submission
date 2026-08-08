# Cover Letter

August 8, 2026

Dear Editor,

I am pleased to submit my manuscript, "A Physics-Aware Benchmark for Phase-Resolved Neural Operator Learning in Boiling Flows: Statistically Rigorous Evidence for Condition-Dependent Architecture Trade-offs," for consideration for publication in *International Journal of Heat and Mass Transfer*.

Pool boiling is central to high-power electronics cooling, data-center thermal management, and nuclear thermal-hydraulics, and neural operator surrogates offer a promising route to fast, CFD-quality forecasting for these applications. Prior benchmark work (BubbleML, NeurIPS 2023) established that standard Fourier Neural Operators underperform convolutional baselines on boiling temperature forecasting, but — to our knowledge — no published study has systematically tested whether an architecture comparison established on one boiling trajectory generalizes to independently held-out physical conditions from the same source data.

This is the central question our manuscript addresses. We show, using a statistically rigorous multi-seed protocol (paired bootstrap intervals, exact sign-flip tests, Holm-Bonferroni correction), that a confirmed architecture trade-off between interface-temperature fidelity (favoring a Tucker-factorized Fourier Neural Operator) and mass-conservation accuracy (favoring a U-Net baseline) on one trajectory does not reproduce when tested on two independently held-out physical conditions from the same dataset. We further show that a predeclared, physically motivated conservation intervention (a spectral velocity-divergence penalty) partially transfers across this condition shift where a purely architectural intervention does not.

We believe this is a valuable and, to our knowledge, novel methodological contribution to the growing literature on neural operators for multiphysics simulation: it provides direct, controlled evidence that single-trajectory benchmarking — even when analyzed with rigorous per-seed statistics — is insufficient to establish a generalizable architectural claim in this domain, and it demonstrates a concrete replication-check methodology that we believe should become standard practice for future work in this area.

The manuscript also reports and corrects a previously unreported evaluation pitfall (physically invalid phase-indicator outputs under autoregressive rollout) and demonstrates a predeclared statistical decision-gate methodology that we use to correctly reject a promising but non-replicating single-seed observation before committing further engineering effort to it.

The release package identifies the code and retained stored-result artifacts, while raw data, complete checkpoints, and complete cross-condition exports remain external as declared in the Data Availability Statement. Every claim in the manuscript is explicitly scoped to what the statistical evidence supports; confirmatory findings are distinguished from descriptive, directionally consistent but unconfirmed observations.

This manuscript is not under consideration elsewhere. I have approved the manuscript for submission and declare no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper. No preprint DOI or arXiv record is asserted in this letter.

I believe this work will be of interest to the readership of *International Journal of Heat and Mass Transfer* working at the intersection of computational thermal-fluid sciences and scientific machine learning, and I thank you for your consideration.

Sincerely,

S. B. Mahafuj Bondhon\
Department of Mechanical Engineering\
Bangladesh University of Engineering and Technology (BUET)\
Ramna, Dhaka-1000, Bangladesh\
ORCID: 0009-0009-6695-365X\
Email: 2210062@me.buet.ac.bd\
Secondary email: sbmahafujbondhon@gmail.com\
Phone: +880 1865375578

---

*Single author and corresponding author: S. B. Mahafuj Bondhon. Confirm the final venue, funding statement, and preprint status before submission.*
