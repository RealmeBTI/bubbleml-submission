# Phase-Resolved Neural Operator Learning for Boiling Flows: An Auditable Benchmark of Conservation Error

## Abstract

Neural surrogates for boiling flows must forecast smooth thermal structure, sharp liquid-vapor interfaces, and locally conservative transport over long autoregressive horizons. We introduce a rigorously auditable evaluation protocol for this task, demonstrated through a representative case study on the BubbleML archive, with a deterministic paired-analysis ledger generated directly from retained results. This paper emphasizes methodological findings over general architecture claims. In the canonical CUDA tutorial split (11 paired seeds), T-FNO has no statistically confirmed advantage over U-Net on global weighted error or either interface-temperature metric, but is significantly worse on mass-conservation error after Holm correction. A five-seed, two-trajectory cross-condition check is directionally consistent with this conservation weakness but is statistically underpowered and is reported descriptively only. In a separate checkpoint-retaining CUDA rerun on the tutorial split, a predeclared spectral divergence-penalty loss applied to a local-global hybrid passed its targeted mass-conservation non-inferiority gate; no cross-condition intervention claim is made. We additionally identify and correct a phase-validity pitfall: unconstrained vapor-phase predictions can exceed the physical [0,1] range during autoregressive rollout, confounding interface and dry-area diagnostics. A critical-heat-flux (CHF)-motivated heater-adjacent dry-area proxy is evaluated only as an autoregressive physical-stability diagnostic; no available trajectory contains a sustained ground-truth event, so no CHF-detection claim is made. The central contribution is therefore an evidence boundary: architecture comparisons require auditable data, checkpoints, paired statistics, and independent-condition evaluation before they can support claims beyond the tested protocol.

---

## 1. Introduction

Pool boiling is central to high-power electronics cooling, data-center thermal management, and nuclear thermal-hydraulics, where heat fluxes exceed single-phase capabilities. The mechanism's effectiveness is bounded by the critical heat flux (CHF)—the point at which a growing vapor film insulates the heated surface, triggering runaway temperature excursions. Classical correlations (e.g., Zuber's hydrodynamic model) estimate aggregate CHF thresholds but do not resolve transient local bubble dynamics. While deployment-grade CHF forecasting requires synchronized wall-heat-flux measurements and verified boiling-crisis transitions—neither of which is present in available open simulation benchmarks—resolving localized, heater-adjacent dry-area dynamics serves as a diagnostic for phase-interface integrity. In this work, we evaluate a heater-adjacent dry-area fraction proxy across stable boiling trajectories strictly as an autoregressive physical-stability test for neural operator rollouts, explicitly distinguishing phase-validity stress-testing from validated CHF event detection.

High-fidelity interface-tracking computational fluid dynamics (CFD) can resolve bubble nucleation, growth, coalescence, and departure, but its cost limits repeated design exploration and real-time digital-twin use. Operator learning offers a route to fast state-to-state surrogates learned directly from CFD trajectories, provided they satisfy local conservation and stability requirements over long autoregressive horizons. The Fourier Neural Operator (FNO) is an attractive candidate because it represents global spatial coupling through a resolution-invariant spectral representation. Boiling fields, however, combine non-periodic domain boundaries with a sharp, near-discontinuous liquid-vapor interface — properties in tension with FNO's implicit periodicity assumption and its low-frequency spectral truncation. The BubbleML benchmark reported that a vanilla FNO underperforms a U-Net on pool-boiling temperature forecasting by roughly a factor of two in boundary RMSE, attributed tentatively to convolutional edge sensitivity versus the Fourier layer's periodicity assumption.

This motivates a natural question: do parameter-efficient FNO variants close this gap on the full, phase-resolved multi-field boiling state (not just temperature), and — critically — **is any observed architecture ranking a genuine, generalizable property of the architectures, or an artifact of the specific trajectory it was measured on?** The second half of this question is, to our knowledge, not systematically addressed in prior boiling-operator benchmark work, which typically reports single-trajectory or single-seed comparisons. We treat it as a first-class experimental question rather than an assumed non-issue.

We state plainly at the outset: this paper's core contribution is a rigorous evaluation protocol and a set of methodological findings, demonstrated on a representative case study (a three-trajectory tutorial split plus a two-trajectory independent check from the BubbleML archive). It is not a claim about definitive neural-operator architecture selection for boiling flows in general. This scope limitation is a deliberate choice to prioritize statistical soundness and exact reproducibility over large-scale, under-audited comparisons.

This paper makes five contributions:

1. A reproducible, physics-aware benchmark protocol for five-field (velocity, pressure gradient, temperature, vapor-phase indicator) phase-resolved boiling forecasting, evaluated with paired bootstrap intervals, exact sign-flip tests, and Holm-Bonferroni correction across multiple seeds.
2. Identification and correction of a previously unreported evaluation pitfall: phase-indicator predictions exceeding their physical [0,1] range under autoregressive rollout, and a demonstration that this materially confounds downstream evaluation metrics that depend on the phase field.
3. A predeclared statistical decision-gate methodology, demonstrated concretely by its correct rejection of a promising but non-replicating single-seed rollout observation — a discipline we argue should be standard practice before committing engineering effort to an observed effect.
4. **An auditable conservation finding:** the canonical 11-seed tutorial comparison identifies a Holm-significant T-FNO mass-conservation weakness but no confirmed interface-fidelity advantage; an independent two-trajectory, five-seed check is directionally consistent with the conservation finding while remaining descriptively reported because it is underpowered. The protocols differ in spatial resolution, so they do not isolate a wall-temperature effect.
5. A predeclared, mechanistically motivated conservation intervention—a spectral velocity-divergence penalty computed analytically on the decoded physical-coordinate velocity via FFT to avoid spatial discretization error. In a checkpoint-retaining canonical CUDA tutorial rerun, this specific choice passed its targeted mass-conservation non-inferiority gate. Its generalization to independent conditions remains untested on the canonical pipeline.

Consistent with contribution 4, our central finding is an auditable evidence boundary rather than a single winning architecture. The tutorial split supports a conservation weakness, not an interface-fidelity advantage. The descriptive cross-condition result is directionally consistent with that weakness but does not establish a generalizable ranking. Reporting a ranking from a single trajectory—however rigorous the seed-level inference—is therefore not sufficient evidence of a generalizable architectural property.

---

## 2. Related Work

### 2.1 Classical CHF prediction and boiling simulation

Critical heat flux has been studied mechanistically since the mid-twentieth century, most influentially through Zuber's hydrodynamic instability model. Engineering practice also uses application-specific correlations for CHF estimation. These are computationally simple aggregate predictors, but they do not resolve transient local bubble dynamics on a specific surface and offer no natural mechanism for real-time, sensor-driven early warning.

Direct numerical resolution of boiling requires interface-tracking methods — volume-of-fluid, level-set, or phase-field formulations coupled to the Navier-Stokes and energy equations. The BubbleML dataset, which underlies the present work's data, was generated with the Flash-X interface-tracking solver and spans multiple fluids, heater geometries, and boiling regimes. Its accompanying benchmark paper is, to our knowledge, the first systematic comparison of neural operator architectures against convolutional baselines on boiling data, and its reported ~2x FNO-versus-U-Net temperature BRMSE gap is the empirical starting point for the present investigation.

### 2.2 Operator learning and convolutional surrogates

The Fourier Neural Operator performs global convolution via pointwise multiplication in a truncated Fourier domain, and has demonstrated strong performance on smooth, largely periodic PDE systems. Convolutional U-Net architectures instead rely on local receptive fields and multi-scale skip connections, and serve as a strong general-purpose baseline for dense spatial prediction, including PDE surrogate modeling.

Several parameter-efficient FNO variants address the capacity and generalization trade-offs of the original architecture. Tensor-factorized (Tucker) FNO represents the spectral weight tensor in a low-rank Tucker decomposition; axis-factorized FNO (F-FNO) factorizes the spectral convolution along each spatial axis independently. The BubbleML benchmark's own results indicate both variants outperform vanilla FNO on boiling forecasting despite having substantially fewer parameters, attributed to reduced overfitting to excess spectral capacity rather than a fix to the underlying periodicity or discontinuity issue. U-shaped FNO (UNO) grafts U-Net-style multi-scale structure onto Fourier blocks; the LOGLO-FNO family of Kalimuthu et al. (2025) explicitly combines local and global spectral branches to improve local, high-frequency representation. Transformer-based operators, including a recent boiling-specific transformer forecaster (Bubbleformer) benchmarked on the extended BubbleML 2.0 release, represent a further active direction — indicating this remains a contested design space rather than a settled one. None of these architecture families, to our knowledge, has been evaluated with an explicit cross-condition replication check of the kind this paper performs. Hard-constrained alternatives to the present soft divergence penalty include the continuity-by-construction networks of Richter-Powell et al. (2022) and the differentiable spectral Leray projection used by Li et al. (2026); neither is evaluated here on phase-resolved boiling.

### 2.3 Experimental boiling diagnostics

Independent of the simulation-data operator-learning literature, Ravichandran et al. (2021) used high-resolution infrared thermometry to investigate boiling-crisis diagnostics, and Ravichandran et al. (2023) developed online dry-area detection from infrared measurements using deep learning. This experimental line of work and the simulation-based operator-learning line of work reviewed above remain largely disjoint; no result in the present paper establishes transfer to experimental measurements or deployment-grade CHF warning.

### 2.4 Reproducibility and the gap addressed

Open boiling datasets are fragmented across repositories, fields, grids, regimes, and evaluation conventions, a fragmentation documented by Dunlap et al. (2026) in their survey of open multimodal thermal-fluid datasets and software. This work's explicit, checksum-verified data and evaluation pipeline is designed to partially mitigate this within its own declared artifact boundary. Combined with the cross-condition replication check described above, we position this work primarily as a benchmark and evaluation-methodology contribution — a genuinely rigorous protocol for making and testing architecture claims on chaotic, multiphysics surrogate tasks — rather than as a claim of a novel architecture. The individual architectural components used here (Tucker/factorized FNO, local-global hybridization, spectral divergence penalties, bounded output heads) are each drawn from or closely related to existing techniques; the contribution is their careful, statistically disciplined integration and, specifically, the demonstration that even a well-powered single-condition comparison among them is not sufficient evidence of a generalizable ranking.

![Figure 1. Canonical tutorial-split interface and conservation comparison.](../submission/figures/fig1_conservation_error_comparison.pdf)

**Figure 1.** Canonical CUDA tutorial-split sample means and paired bootstrap intervals for T-FNO and U-Net. The interface-temperature difference is not Holm-significant, whereas the mass-conservation comparison is unfavorable to T-FNO. This fixed-split figure does not establish a cross-condition ranking.

| Feature | BubbleML (original) | This work |
|---|---|---|
| Multiple trajectories | Yes (79 simulated conditions) | Yes |
| Interface and conservation metrics jointly reported | Not reported for the neural-PDE benchmark | Yes |
| Multi-seed paired statistical testing | Not reported | Yes (n=11 tutorial; n=5 cross-condition) |
| Cross-condition architecture replication | Not reported; the paper reports heat-flux holdout cross-validation | Yes |
| Physical output-validity enforcement | Not reported | Yes (bounded-alpha head) |
| Predeclared decision gates | Not reported | Yes |
| Artifact release | Partial (data, code, and model zoo reported) | Partial (stored-result self-test; raw data/checkpoints remain external) |

*Table 1. Protocol comparison. “Not reported” indicates that the original BubbleML paper does not document the feature for its neural-PDE benchmark; it does not establish absence.*

---

## 3. Methods

### 3.1 Data, preprocessing, and splits

**Tutorial-scale split.** The primary comparison uses three official downsampled Pool-Boiling Subcooled FC-72 examples at 48×48 resolution, preprocessed into PyTorch tensors with no synthetic fallback. The trajectory-level split prevents temporal leakage: Twall-103 is train, Twall-106 is validation, and Twall-100 is test. Each source has 169 released-grid frames, yielding 160 valid five-history/five-future temporal windows per split.

| Source | SHA-256 | Role |
|---|---|---|
| `Twall-103.hdf5` | `25b305661dee59cf5df49eb2563a4ed08f79664ba377e57877fcda5a948956dd` | train |
| `Twall-106.hdf5` | `4308e5be884c3edcf301e9c12bff8d499d53729be3820aa18e255a5152fbd004` | validation |
| `Twall-100.hdf5` | `5bf2539628c3595f39517c466f6971da76f137358771592c14ad1a5881e4d1bf` | test / rollout |

The released fields are time×y×x grids; row 0 is immediately above the heater; physical boundary cells are omitted. Reported outer-grid quantities are therefore interior-edge proxies, not wall residuals.

**Independent multi-trajectory split.** The cross-condition replication check uses the official ten-trajectory, native 384×384 Pool-Boiling Subcooled legacy archive (SHA-256 `2eba140d74cbb7b01a55f0684227dea94306aea516a0f864831485d31d25f655`; 201 frames/trajectory; Twall 79, 81, 85, 90, 95, 98, 100, 103, 106, 110). Trajectory roles were frozen before any model training or test inspection: train on Twall 79, 85, 90, 95; validate on Twall 81; test independently on Twall 98 and Twall 110. Twall 100, 103, and 106 were excluded, since they form the tutorial split. Continuous fields were bilinearly downsampled to 96×96; the binary phase mask used nearest-neighbor downsampling; physical grid spacings were rescaled consistently. In the preprocessing implementation, `dfun` is the signed-distance field from which the binary vapor mask is derived (`dfun > 0`). After discarding source frames 0–29, each trajectory contributes 170 frame records, yielding 644/161/322 valid windows for train/validation/test. The distinct tutorial and cross-condition protocols are visualized in Figure 2. A separate one-epoch, batch-size-one feasibility check was also run at native 384×384 resolution to test direct execution and memory feasibility only (not convergence or ranking).

![Figure 2. The tutorial and cross-condition designs are distinct trajectory-level splits.](../submission/figures/fig6_split_design.pdf)

**Figure 2.** The tutorial split evaluates a fixed three-trajectory comparison; the independent cross-condition protocol tests whether that comparison persists on two held-out conditions. The protocols also differ in spatial resolution (48×48 versus 96×96), so the comparison does not isolate a wall-temperature effect. Roles were frozen before training or test inspection.

### 3.2 Model architectures and training protocol

Four base models are compared: vanilla FNO, Tucker-factorized FNO (T-FNO, rank 0.1), axis-factorized FNO (F-FNO), and a U-Net baseline using the same temporal input/output convention. The architectures are not parameter-matched: the stored T-FNO and U-Net counts are 548,837 and 7,770,169 parameters, respectively. Each uses five history and five forecast frames (25 input/output channels), AdamW (lr 1e-3, weight decay 0.01), batch size 8, horizontal reflection augmentation, global gradient-norm clipping at 1.0, and training to a predeclared two-window validation-plateau stopping rule (200-epoch ceiling). Fourier-family models use a fixed 24×24 real-FFT mode cap at both resolutions for comparability. This is below the one-sided real-FFT Nyquist maxima of 25 modes at 48×48 and 49 modes at 96×96; the cap is a design choice, not a maximum representable count.

The canonical tutorial-split T-FNO/U-Net comparison uses the 11 paired seeds 42, 100, 1234, 2025, 9999, 7, 17, 314, 2718, 4242, and 7777 in one CUDA campaign. The cross-condition comparison uses seeds 42, 100, 1234, 2025, and 9999 on an NVIDIA Tesla T4 via CUDA. With five paired seeds, the minimum attainable two-sided exact sign-flip p-value is 0.0625; direction and interval width, not corrected significance, are the primary evidence at this sample size.

### 3.3 Physical output-bounding for the phase indicator

Unconstrained models produced decoded vapor-fraction (alpha) predictions outside the physical [0,1] interval during autoregressive rollout (observed ranges up to [-0.157, 1.408]). We correct this at the model level: writing the raw normalized-space alpha logit as $z_\alpha$, and $a_0, a_1$ as the normalized coordinates that decode to physical alpha 0 and 1 respectively, the bounded output is

$$
\widehat{\alpha}_N = a_0 + (a_1 - a_0)\,\sigma(z_\alpha), \qquad \widehat{\alpha} = \operatorname{decode}(\widehat{\alpha}_N) \in [0,1]. \tag{1}
$$

All non-alpha channels remain unconstrained. This guarantees physical validity by construction, without post-hoc clipping of autoregressively fed-back predictions.

### 3.4 Local-global hybrid architecture

For hybrid layer $\ell$, the local-global composition adds a learned local convolution branch in parallel with the spectral and pointwise-residual paths:

$$
z^{(\ell+1)} = \phi\!\left(\mathcal{K}^{(\ell)}_{\text{Tucker}}z^{(\ell)} + \mathcal{C}^{(\ell)}_{3\times 3}z^{(\ell)} + W^{(\ell)}z^{(\ell)}\right), \tag{2}
$$

where $\mathcal{K}_{\text{Tucker}}$ is the truncated Tucker-factorized spectral convolution, $\mathcal{C}_{3\times3}$ is a learned 3×3 local convolution, $W$ is the pointwise residual map, and $\phi$ is the layer nonlinearity. The local branch and the divergence penalty below target a conservation weakness directly; they are not premised on an unconfirmed interface-fidelity advantage. A predeclared statistical decision gate (Section 3.6) separately and correctly rejected an earlier, unrelated intervention aimed at a non-replicating single-seed rollout artifact; these questions are distinct and should not be conflated.

### 3.5 Conservation-targeted divergence penalty

The conservation intervention augments the local-global hybrid's training objective with a spectral velocity-divergence penalty. Crucially, this penalty is computed on the decoded physical-coordinate velocity field via Fast Fourier Transform (FFT) rather than via finite-difference discretization on the spatial grid, and it is computed in physical space rather than in the normalized latent space:

$$
\mathcal{L} = \mathcal{L}_{\text{data}} + \lambda_{\text{div}} \cdot \frac{1}{BTHW}\sum_{b,t,x,y} \left| \mathcal{F}^{-1}\!\left[ i k_x \mathcal{F}(u_{b,t}) + i k_y \mathcal{F}(v_{b,t}) \right]_{x,y} \right|, \tag{3}
$$

using each sample's physical grid spacings for the wavenumbers $k_x, k_y$. This specific methodological choice ensures that the loss term penalizes the analytical divergence of the Fourier representation. A naive finite-difference implementation would compound spatial discretization error into the conservation penalty itself, confounding the optimization. While spectral divergence penalties are established (see Richter-Powell et al. (2022) and Li et al. (2026) for related hard-constrained approaches), applying the soft penalty on decoded physical-coordinate velocity is the implementation choice evaluated here, not a claim of inventing spectral divergence regularization. Validation data MSE remains the checkpoint-selection criterion. The value $\lambda_{\text{div}}=.30$ was frozen before the checkpoint-retaining CUDA rerun; the present confirmatory claim depends on that rerun, not on numerical results from the retired pipeline that originally motivated the candidate.

### 3.6 Statistical protocol and decision gates

All architecture and intervention claims use paired, multi-seed inference: a deterministic 10,000-sample paired bootstrap for confidence intervals, an exact paired sign-flip test for significance, and Holm-Bonferroni correction across the full family of error metrics tested in a given comparison. For the canonical T-FNO/U-Net comparison, that complete family contains 22 error endpoints, including rollout counterparts; compute-only metrics are excluded. Consequently, the mass-conservation unadjusted value $p=.000976562$ becomes Holm $p=.0214844$. The smaller value $p=.00390625$ would result from a post-hoc four-headline-metric family and is not the predeclared correction used here. The implementation enforces the standard step-down monotonicity of Holm-adjusted values. An earlier statistical audit also removed an unnecessary Monte Carlo add-one correction from the exact sign-flip enumeration, and all numbers reported in Section 4 reflect the corrected implementation.

For a decoded physical-space prediction $p$ and target $y$, GWRMSE is the reference-gradient-weighted RMSE computed over all five channels and all grid cells. Let $g=\sqrt{(\Delta_x y)^2+(\Delta_y y)^2}$ use the implementation's backward finite differences (zero at the leading row and column), $\bar g=\operatorname{mean}_{c,i,j}(g_{cij})$, and $w_{cij}=1+g_{cij}/\max(\bar g,10^{-6})$. With the configured weight strength equal to one, the per-sample metric is

$$
\operatorname{GWRMSE}(p,y)=\left(\frac{\sum_{c,i,j} w_{cij}(p_{cij}-y_{cij})^2}{\sum_{c,i,j} w_{cij}}\right)^{1/2}. \tag{4}
$$

This is the direct transcription of `gradient_weighted_rmse` in `bubbleml_benchmark/metrics.py`; no per-field weighting or normalization beyond the decoded physical-space target gradient is introduced.

Architectural interventions are evaluated under **predeclared decision gates**: a fixed statistical criterion (non-inferiority margin, significance threshold, and metric family) is frozen before training and evaluation, and the intervention is only reported as successful if the frozen criterion is met. This discipline was demonstrated concretely when an initial single-seed pair showed a promising reversal in rollout dry-area tracking after the phase-bounding fix (Section 3.3); a predeclared 11-seed confirmatory test showed this reversal did not replicate (Section 4.4), and the corresponding architectural interventions were correctly not pursued on that basis. The local-global hybrid (Section 3.4) and divergence penalty (Section 3.5) instead address the conservation objective directly and are not affected by that earlier gate's rejection.

### 3.7 CHF-motivated autoregressive proxy evaluation

A fully autoregressive evaluator feeds each model's own five-frame predictions back as input for the next step (no ground-truth injection), producing long rollouts from a short seed history. The CHF-motivated proxy signal is the fraction of heater-adjacent cells (rows 0:4) with predicted alpha > 0.5. The event threshold is $\max\!\left(0.10,\; \operatorname{median}(\text{first 20 ground-truth forecast frames}) + 0.10\right)$, requiring three consecutive frames at or above threshold to count as a sustained precursor. This is an illustrative phase-based proxy, not a calibrated CHF label: none of the available trajectories has a synchronized wall-heat-flux series or an independently verified stable-to-CHF transition. Figure 3 locates this evaluation within the retained-artifact workflow.

![Figure 3. Benchmark workflow from official trajectories to the stored-result release.](../submission/figures/fig5_benchmark_workflow.pdf)

**Figure 3.** Benchmark workflow. The last transition makes the artifact boundary explicit: the stored-result statistical self-test is reviewer-runnable, while raw data, full checkpoints, and complete cloud-side cross-condition exports remain external.

### 3.8 Nomenclature

| Symbol | Definition |
|---|---|
| $\alpha$ | Physical vapor-fraction / phase indicator, $\alpha\in[0,1]$ |
| $z_\alpha$ | Raw normalized-space alpha logit (pre-bounding) |
| $a_0,a_1$ | Normalized coordinates decoding to physical $\alpha=0$ and $\alpha=1$ |
| $\widehat{\alpha}_N$ | Bounded normalized-space alpha, defined by Eq. 1 |
| $\widehat{\alpha}$ | Bounded physical alpha, $\operatorname{decode}(\widehat{\alpha}_N)\in[0,1]$ |
| $\sigma(\cdot)$ | Sigmoid activation function |
| $z^{(\ell)}$ | Hidden-state tensor at hybrid layer $\ell$ |
| $\mathcal{K}^{(\ell)}_{\mathrm{Tucker}}$ | Truncated Tucker-factorized spectral convolution operator at layer $\ell$ |
| $\mathcal{C}^{(\ell)}_{3\times3}$ | Learned $3\times3$ local convolution branch at layer $\ell$ |
| $W^{(\ell)}$ | Pointwise residual map at layer $\ell$ |
| $\phi$ | Layer nonlinearity (activation function) |
| $\lambda_{\mathrm{div}}$ | Spectral velocity-divergence penalty weight |
| $\mathcal{L}$ | Total training loss |
| $\mathcal{L}_{\mathrm{data}}$ | Data-fit (reconstruction) loss term |
| $u,v$ | Decoded physical-coordinate velocity components (x- and y-direction) |
| $k_x,k_y$ | Spatial wavenumbers from each sample's physical grid spacing |
| $\mathcal{F},\mathcal{F}^{-1}$ | Forward and inverse Fourier transform |
| $B,T,H,W$ | Batch size, time-window length, grid height, grid width |
| $T_{\mathrm{wall}}$ | Wall superheat / boiling operating condition labeling each source trajectory |
| GWRMSE | Global reference-gradient-weighted RMSE aggregate metric (Eq. 4) |
| BRMSE | Boundary RMSE, the metric reported by the original BubbleML benchmark (Section 1) |
| MAE | Mean absolute error |
| dfun | Signed-distance/level-set function underlying the binary phase mask; $\mathrm{dfun}>0$ denotes vapor. |

---

## 4. Results

### 4.1 Canonical tutorial split: no confirmed interface advantage, significant conservation weakness

{{CANONICAL_TUTORIAL_RESULTS}}

### 4.2 A local branch alone does not recover conservation; a targeted divergence penalty does, on the tutorial split

{{CANONICAL_HYBRID_RESULTS}}

### 4.3 Cross-condition consistency check: descriptive evidence only

On two independently held-out physical conditions (Twall 98 and Twall 110; five paired seeds), the retained summary is:

{{CANONICAL_CROSS_CONDITION_TABLE}}

{{CANONICAL_CROSS_CONDITION_RESULTS}}

An earlier divergence-hybrid cross-condition comparison came from the retired pipeline and is excluded from numerical claims. The checkpoint-retaining canonical CUDA rerun in Section 4.2 covers the tutorial split only; it therefore cannot establish intervention transfer to these independent conditions.

### 4.4 Physical validity is an evaluation requirement, independent of architecture ranking

Unbounded models produced physically invalid alpha values under rollout ([−0.157, 1.408] for T-FNO, [−0.108, 1.417] for U-Net over 164 steps). The output-head fix (Eq. 1) constrained both to [0,1] by construction. An initial single-seed comparison after this fix showed a large reversal in cumulative dry-area tracking error (bounded T-FNO 0.12167 vs. bounded U-Net 0.05275); a predeclared 11-seed confirmation, however, found this did not replicate as a significant effect (paired difference +0.00775, 95% CI [−0.00393, +0.01829], Holm p=1.0 across all 21 tested rollout metrics, smallest adjusted p=0.3997). We report this explicitly as a methodological finding: physical-validity correction and architecture superiority are distinct questions, and single-seed rollout observations — even after a legitimate bug fix — require the same multi-seed confirmatory discipline as any other architecture claim.

### 4.5 Exploratory resolution records are withheld from inference pending analysis reconciliation

The retained 96×96 stored result contains 11 raw paired seed rows, but its stored paired bootstrap confidence intervals do not reproduce from those rows under the documented bootstrap procedure. The accompanying control matrix also documents preprocessing, source-commit, and retained-artifact differences from the canonical 48×48 campaign. We therefore do not use this exploratory arm to make a resolution claim, present an architecture×resolution interaction, or report its numerical comparisons in this manuscript. The discrepancy and the excluded provenance are recorded in the canonical numerical ledger.

### 4.6 CHF-motivated proxy: no sustained event in any available trajectory

The dry-area proxy (Section 3.7) was evaluated on Twall-100 (tutorial test) and, newly, on the independent Twall-98 and Twall-110 trajectories. None showed a sustained crossing: Twall-100 had 3/164 above-threshold frames (longest run 2), Twall-98 had 0/170, and Twall-110 had 1/170 (longest run 1). Figure 4 shows the retained rollout traces and thresholds. No trajectory in the currently available data supports a lead-time, sensitivity, or missed-event-rate evaluation. This is a negative feasibility result for CHF-proxy event evaluation with current data, not evidence about CHF predictability in general.

![Figure 4. Retained autoregressive dry-area proxy traces.](../submission/figures/fig2_dry_area_trace.pdf)

**Figure 4.** Heater-adjacent dry-area proxy traces for the available tutorial and held-out trajectories. The plotted thresholds are not crossed for three consecutive frames, so none of these trajectories supports a sustained-event evaluation.

### 4.7 Native-resolution feasibility and computational cost

One-epoch, batch-size-one runs at native 384×384 completed successfully for all four models on the Tesla T4 (5.91–6.99s/epoch for the Fourier-family models, 2.77s for U-Net), confirming direct execution feasibility without establishing convergence or ranking. At the converged 96×96 cross-condition scale:

| Model | Parameters (stored / real-scalar) | Mean training time/seed (s) | Inference latency (ms/window) | Throughput (windows/s) |
|---|---:|---:|---:|---:|
| T-FNO | 548,837 / 1,040,625 | 216.09 | 4.467 | 223.94 |
| U-Net | 7,770,169 / 7,770,169 | 98.72 | 2.026 | 493.63 |

U-Net is the fastest model to train and the lowest-latency at inference, despite having roughly 6–14× more parameters than the FNO-family variants — a practical consideration alongside the accuracy/conservation results above. The historical MPS training histories are not used in this manuscript because that campaign is retired from current evidence; complete canonical tutorial and cross-condition per-seed histories are outside the present retained numerical ledger.

---

## 5. Discussion

### 5.1 Conservation weakness is the replicating signal; no interface property is confirmed

The canonical tutorial split (Section 4.1) establishes a T-FNO mass-conservation disadvantage under a paired 11-seed protocol, while it establishes no interface-fidelity advantage. The cross-condition summary (Section 4.3) points in the same conservation direction but is explicitly descriptive because it has two held-out trajectories and five seeds. Thus, no single metric ranking should be promoted to a general architectural property on the current evidence. Seed-level rigor and condition-level rigor remain separate axes of evidence.

The available results do not identify a causal mechanism for the conservation gap. A mechanism study would need a prospectively controlled comparison of resolution, data preprocessing, operating condition, and training runtime together with relevant physical statistics; the presently retained exploratory 96×96 record does not meet that evidence standard (Section 4.5).

### 5.2 The divergence penalty is the more robust of the two interventions tested

The divergence penalty's specific analytical implementation—computed on the decoded physical-coordinate velocity field via FFT to avoid compounding spatial discretization error—was the more robust of the two interventions in the checkpoint-retaining canonical CUDA tutorial rerun. It passed the targeted mass-conservation non-inferiority gate, whereas the zero-penalty local branch did not (Section 4.2). This supports the narrower conclusion that an explicitly formulated physical penalty can improve its targeted objective on the tested split; it does not establish cross-condition transfer. The differentiable Leray-projection approach of Li et al. (2026) is a natural harder alternative: it constrains the velocity field to a divergence-free subspace, whereas the present work only penalizes divergence during training. This paper does not test that hard constraint, and it should not be interpreted as a comparison with it.

### 5.3 Physical output validity is necessary but architecturally orthogonal

The phase-bounding correction (Section 3.3) is, independent of any architecture ranking, a requirement for trustworthy autoregressive evaluation of any phase or volume-fraction field. The initial single-seed reversal it produced in rollout behavior (Section 4.4) is a cautionary example of exactly the single-condition/single-seed over-interpretation risk this paper's broader argument (Section 5.1) warns against, now demonstrated at the seed level rather than the trajectory level. We recommend both checks — physical-bound verification and multi-seed confirmation — as standard practice for future phase-resolved operator-learning evaluations.

### 5.4 CHF-motivated evaluation remains proxy-only

Across every trajectory available to this study, no sustained ground-truth dry-area event was observed (Section 4.6). The dry-area proxy therefore functions in this paper as an autoregressive-stability stress test and a demonstration of the physical-bounding pitfall (Section 4.4), not as an evaluation of CHF detectability, which would require at minimum one trajectory with a verified stable-to-film-boiling transition and, ideally, a synchronized wall-heat-flux measurement independent of the model's own output.

### 5.5 Limitations

| Dimension | Limitation | Status in this work |
|---|---|---|
| Statistical power, cross-condition | Independent test uses 2 trajectories, 5 seeds; minimum exact p=.0625, no Holm-significant cross-condition result | Directionally consistent, explicitly reported as unconfirmed |
| Physical-condition sampling | 2 held-out conditions cannot characterize population-level regime variation | Explicitly scoped; not generalized beyond these conditions |
| Resolution | 96×96 cross-condition training is converged; 384×384 is feasibility-only (1 epoch) | Native-resolution convergence is future work |
| Phase representation | Binary `dfun>0` mask, not continuous volume fraction; omits surface tension/contact-angle dynamics | Acknowledged; continuous-target ablation is future work |
| CHF validity | No trajectory contains a verified stable-to-CHF transition or synchronized heat-flux series | Proxy-only throughout; no detection claim made |
| Divergence-penalty selection | The canonical CUDA confirmation evaluates the frozen $\lambda_{\text{div}}=.30$ candidate only; it does not establish an interior optimum | Section 6 future work extends the range |
| Intervention generalization | The checkpoint-retaining canonical CUDA intervention rerun covers the tutorial split only | No cross-condition divergence-hybrid numerical claim is made |
| Conservation scope | Only velocity divergence is penalized; energy/momentum conservation are not explicitly constrained | Noted as an open direction |
| Architecture coverage | No comparison to transformer-based operators (e.g., Bubbleformer) or hard-constrained conservation layers | Explicitly out of scope this cycle; noted as related work |
| Resolution arm | The 96×96 stored paired CIs do not reproduce from the retained raw seed rows; additional preprocessing and provenance differences prevent a controlled interpretation | Excluded from numerical claims; reconciliation required before use |
| Historical tutorial artifact | An earlier MPS tutorial result was generated by a distinct pipeline and is retired from current claims | Root-cause audit retained; canonical CUDA artifact replaces it |
| Reproducibility | The canonical tutorial result includes retained paired metrics, configurations, prepared-data manifest, and checkpoint bundle; complete cross-condition per-seed histories are unavailable locally | Tutorial stored-result self-test is reproducible; cross-condition evidence remains summary-level |

An exploratory 96×96 cross-resolution comparison was attempted. During canonical reconciliation, its stored paired confidence intervals could not be reproduced from the retained raw per-seed rows; it has therefore been excluded from all numerical claims in this version rather than reported with unverifiable intervals. The previously specified matched-factorial 48×48/96×96 protocol in Section 6 remains the appropriate path to a resolution-sensitivity claim and is unaffected by this exclusion.

### 5.6 Practical and methodological implications

For practitioners, the safest actionable guidance from this study is: do not select an architecture for phase-resolved boiling forecasting from one trajectory alone, regardless of how many seeds support that trajectory-level result. The canonical tutorial comparison identifies a conservation concern for T-FNO; it does not demonstrate an offsetting interface-fidelity advantage. Where an explicit conservation requirement exists, a targeted physical penalty (Section 4.2) is a testable lever, but its cross-condition behavior remains untested on the canonical pipeline.

For the broader field, we argue the methodological contribution — predeclared decision gates, physical-validity checks, and cross-condition replication — is at least as valuable as any specific architecture finding reported here, and we encourage its adoption as a standard evaluation practice for neural operator claims on chaotic, multiphysics, condition-varying systems.

---

## 6. Future Work (Explicitly Non-Blocking for This Submission)

The following are identified, well-motivated next steps that would strengthen this line of work but are not required to support the claims made above, each of which is scoped and evidenced independently of them:

- Extending the $\lambda_{\text{div}}$ sensitivity sweep beyond 0.30 to identify whether an interior optimum exists or whether performance continues to improve, plateaus, or degrades at higher values.
- Expanding the cross-condition test beyond two held-out trajectories toward the full ten-trajectory archive, to move from a directionally-consistent-but-underpowered result toward a properly powered, Holm-corrected cross-condition significance test.
- Training the cross-condition comparison to full convergence at native 384×384 resolution, beyond the current one-epoch feasibility check.
- The frozen matched-factorial 2×2 resolution protocol: 48×48 and 96×96 resolution crossed with T-FNO and U-Net, 11 paired seeds per cell, a single CUDA environment, matched preprocessing and stopping rules, and a preregistered interaction test on the per-seed T-FNO-minus-U-Net contrast. This is the appropriate design for a resolution-sensitivity claim.
- Comparison against transformer-based operators (e.g., Bubbleformer-style architectures) and hard-constrained/projection-based conservation layers, as a stronger baseline set than the soft-penalty approach used here.
- A continuous (non-binary) phase-fraction target, to test whether the conservation finding is sensitive to the signed-distance-derived binary mask used in this study.
- Acquisition of at least one real trajectory with a verified stable-to-CHF transition and synchronized heat-flux labeling, to move the CHF-motivated proxy toward an actual validated detection evaluation.

A concrete, ready-to-execute prompt for the first two items (the highest-leverage, most directly comparable extensions of this paper's existing protocol) is provided as a companion document.

---

## 7. Reproducibility and Artifact Manifest

The canonical tutorial analysis is generated from `benchmark_results/resolution_control_48x48/benchmark_results.json` by `scripts/generate_canonical_statistics.py`, which records its bootstrap seed and validates the stored paired statistics before manuscript conversion. The same generator validates the checkpoint-retaining CUDA intervention rerun against the canonical T-FNO/U-Net baseline metrics before inserting Section 4.2. The cross-condition experiment is represented locally by its compact audited summary rather than complete cloud-side per-seed histories and checkpoints; this boundary is documented in the artifact manifest. The earlier `phase1_gpu_decisive_tfno_unet_n11` MPS result and all intervention outputs derived from that retired pipeline are retained only as historical provenance and excluded from current numerical claims. The root-cause audit documents this retirement. The prior public `v1.0.4` repository release is archived at Zenodo, DOI https://doi.org/10.5281/zenodo.21967986; it is a version-specific historical snapshot and does not remove the stated limitations.

---

## Data availability

The primary data are the publicly available BubbleML Pool-Boiling Subcooled FC-72 dataset; the exact source release and checksums are documented in `CHECKSUMS.md`. The repository does not redistribute the raw data. Code, retained stored-result artifacts, configurations, statistical-analysis scripts, and the verified checkpoint-retaining CUDA intervention reviewer bundle (`hybrid_cuda_rerun_48x48_n11_reviewer_bundle.zip`, SHA-256 `1a73240957cc1a3375a1e146c76772b5551080e232926df9b4abefa33fa0a349`) supporting Section 4.2 are publicly available in the verified `v1.1.0` release:

- GitHub release: https://github.com/RealmeBTI/bubbleml-submission/releases/tag/v1.1.0
- Version archive DOI: https://doi.org/10.5281/zenodo.21967986

Raw data, complete cross-condition exports, and other unavailable artifacts remain bounded as documented in `ARTIFACT_GAPS.md`.

---

## CRediT authorship contribution statement

S. B. Mahafuj Bondhon: Conceptualization, Methodology, Software, Validation, Formal analysis, Investigation, Data curation, Visualization, Writing – original draft.

---

## Funding

This research received no specific grant from any funding agency in the public, commercial, or not-for-profit sectors.

---

## Declaration of competing interests

The author declares that they have no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.
---

## Declaration of generative AI and AI-assisted technologies in the writing process

During the preparation of this work, the author used Large Language Models (Claude, ChatGPT, Gemini) in order to improve language clarity, formatting readability, and grammatical polish. OpenAI Codex and Antigravity were used for LaTeX formatting and repository-audit assistance. After using these services, the author reviewed and edited the content as needed and takes full responsibility for the content of the published article.
