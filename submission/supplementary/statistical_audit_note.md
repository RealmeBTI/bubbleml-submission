# Statistical Audit Note

The final stored analyses use one audited implementation for paired inference.
For up to 20 seeds, the two-sided sign-flip test enumerates all sign assignments
exactly and divides the number at least as extreme as the observed statistic by
the exact enumeration size. It does not apply a Monte Carlo add-one correction.

Holm-Bonferroni families exclude compute-only quantities such as parameter count,
latency, and throughput. Those quantities remain descriptive. The reviewer-facing
script `scripts/reproduce_reported_results.py` independently recomputes paired
means and exact sign-flip probabilities from the stored per-seed results and
checks the archived bootstrap intervals and Holm-adjusted values against the
manuscript.

The cross-condition comparison has five paired seeds. Its minimum attainable
two-sided exact sign-flip probability is 0.0625. Accordingly, the cross-condition
directions are reported as descriptive and underpowered, not confirmatory.

