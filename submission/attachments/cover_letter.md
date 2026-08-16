# Cover Letter

August 14, 2026

Dear Editor,

I am pleased to submit my manuscript, "Phase-Resolved Neural Operator Learning for Boiling Flows: An Auditable Benchmark of Conservation Error," for consideration for publication in *Computer Methods in Applied Mechanics and Engineering* (CMAME).

This manuscript is a computational-methods contribution: an auditable protocol for evaluating neural PDE surrogates when accuracy, phase-interface behavior, and physical conservation can point to different conclusions. Pool boiling supplies a demanding multiphysics case study, but the central question is broader: whether a well-powered, single-condition neural-operator comparison is sufficient evidence for an architecture claim. That question is native to CMAME's computational-mechanics scope and closely aligned with the fair neural-operator comparison of Lu et al. (*Computer Methods in Applied Mechanics and Engineering* 393 (2022) 114778).

Using an auditable 11-seed CUDA tutorial comparison (paired bootstrap intervals, exact sign-flip tests, and Holm-Bonferroni correction), we find no confirmed T-FNO interface-temperature advantage but a significant T-FNO mass-conservation disadvantage. A five-seed check on two independently held physical conditions is directionally consistent with that conservation concern but is reported descriptively because it is underpowered. In a separate checkpoint-retaining canonical CUDA tutorial rerun, a predeclared spectral velocity-divergence penalty passed its targeted mass-conservation non-inferiority gate: mean mass-conservation MAE was 0.09528 versus 0.16562 for U-Net (paired difference -0.07034, 95% CI [-0.07454, -0.06654], exact one-sided p=.000488281). No cross-condition intervention claim is made.

We believe this is a valuable methodological contribution to the literature on numerical methods and scientific machine learning: it makes the evidence boundary auditable and demonstrates why a single trajectory, however carefully analyzed at the seed level, cannot establish a general architecture ranking in this domain. We chose CMAME rather than a thermal-engineering venue because the principal contribution is the evaluation methodology and conservation-property analysis for neural PDE surrogates, rather than a new boiling mechanism or heat-transfer correlation.

The manuscript also reports and corrects a previously unreported evaluation pitfall (physically invalid phase-indicator outputs under autoregressive rollout) and demonstrates a predeclared statistical decision-gate methodology that we use to correctly reject a promising but non-replicating single-seed observation before committing further engineering effort to it.

The release package identifies the code and retained stored-result artifacts, while raw data, complete checkpoints, and complete cross-condition exports remain external as declared in the Data Availability Statement. Every claim in the manuscript is explicitly scoped to what the statistical evidence supports; confirmatory findings are distinguished from descriptive, directionally consistent observations.

This manuscript is not under consideration elsewhere. I have approved the manuscript for submission and declare no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper. No preprint DOI or arXiv record is asserted in this letter.

I believe this work will interest CMAME readers working on computational mechanics, numerical evaluation, and physically informed machine-learning surrogates for multiphysics systems, and I thank you for your consideration.

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
