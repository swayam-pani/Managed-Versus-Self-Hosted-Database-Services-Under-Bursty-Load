# Presentation Deck Guide: Project Review 3 (Canva-Ready)

**Project Title**: Characterizing Tail-Latency Hysteresis and Total Cost of Ownership in Managed Cloud vs. Containerized Database Services Under Transient Workload Bursts  
**Project Code**: P8 (Cloud Computing - Semester 7)  
**Evaluators Date**: October 21, 2026 (Review 3 Final Evaluation)  
**Students**: Swayam Pani (23BCE1526) · Anamitra Shrivastava (23BCE5012)  
**Faculty Guide**: Dr. Indra Priyadarshini S  

---

## Slide Deck Design Specifications (Canva / PPT)
- **Theme**: Light Mode, Minimalist Academic Engineering (Clean Off-White / Light Gray `#F8FAFC`, Deep Navy `#1E3A8A` for headings, Steel Blue `#2563EB` accents).
- **Aesthetic**: Card-deck layout, bold numeric KPI callouts, zero decorative emojis, no AI cartoon illustrations.
- **Visuals**: Embedded empirical figures with error bars, high-contrast statistical comparison tables.

---

## Slide 1: Title Slide (Project Review 3 - Final Evaluation)
- **Header**: Project Review 3: Final System Evaluation & Documentation
- **Title**: Managed Versus Self-Hosted Database Services Under Bursty Load: A Tail-Latency and Cost-of-Ownership Study
- **Sub-badge**: Cloud Computing Laboratory (Semester 7) · Final Evaluation (21/10/2026)
- **Presenters**: Swayam Pani (23BCE1526) · Anamitra Shrivastava (23BCE5012)
- **Faculty Guide**: Dr. Indra Priyadarshini S (SCOPE, VIT)
- **Key Deliverables Highlighted**:
  - Multi-workload evaluation with $N=3$ repeated trials and 95% Confidence Intervals.
  - Novelty contribution: Iso-workload burst shape sensitivity and performance hysteresis $H(t)$.
  - Live interactive benchmark demonstration system.
  - 6–8 page IEEE conference paper and 3-year TCO model.

---

## Slide 2: Review 3 Objectives & Evaluation Matrix
- **Header**: Review 3 Requirements & Rubric Compliance (10 Marks)
- **3-Column Card Layout**:
  - **Card 1: Evidence Across All Objectives (3 Marks)**
    - Multi-phase burst workloads: Read-Heavy (80/20), Balanced (50/50), Write-Heavy (20/80).
    - At least 3 independent trials ($N=3$) per configuration with sample mean ($\mu$) and sample variance ($\sigma^2$).
  - **Card 2: Statistical Soundness (2 Marks)**
    - Symmetric 95% Student's-$t$ confidence interval whiskers on all bar charts.
    - Continuous dynamic time-series with shaded $\pm 1\sigma$ variance envelopes.
    - Zero reliance on single-run bar charts.
  - **Card 3: Live Demonstration & Documentation (5 Marks)**
    - Runnable 20-second live terminal demonstration (`python scripts/live_demo.py`).
    - 6–8 page comprehensive IEEE conference paper + 3-minute video presentation script.

---

## Slide 3: Experimental Infrastructure & Testbed Architecture
- **Header**: Comparative Architecture: Container Baseline vs. Cloud DBaaS
- **Side-by-Side Comparison Cards**:
  - **Left Card: Self-Hosted Containerized Baseline**
    - Engine: PostgreSQL 15-alpine in Docker.
    - Operating System Resource Constraints: Linux cgroups strictly enforcing `2.0 vCPU` and `2048 MB RAM`.
    - Storage: Local Ext4 SSD Docker volume with synchronous WAL writes.
    - Baseline latency: <10 ms (Zero-latency loopback socket).
  - **Right Card: Managed Serverless Cloud Service**
    - Engine: AWS Neon Serverless PostgreSQL (PostgreSQL 16 on ARM64 Graviton).
    - Topology: Storage-disaggregated architecture (Stateless Compute $\rightarrow$ Safekeeper WAL Quorum $\rightarrow$ S3 Pageservers).
    - Connection Pooling: Integrated pgBouncer proxy pooler over TLSv1.3.
    - Region: AWS `us-east-2` (Ohio).

---

## Slide 4: Multi-Workload Empirical Results (Mean $\pm$ Variance)
- **Header**: Statistical Rigor: 3 Workloads Across $N=3$ Independent Trials
- **Central Data Table**:
  | Architecture | Workload Profile | Base $p_{99}$ Mean $\pm$ 95% CI | Peak Burst $p_{99}$ Mean $\pm$ 95% CI | Sample Variance ($\sigma^2$) | Burst Amplif. (BAF) | Recovery Time ($T_{\text{recov}}$) |
  | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
  | **Self-Hosted Container** | Read-Heavy (80/20) | $4.76 \pm 0.28\text{ ms}$ | $22.68 \pm 6.42\text{ ms}$ | $4.82$ | $0.21 \pm 0.05$ | $1.0\text{ s}$ |
  | **Self-Hosted Container** | Balanced (50/50) | $5.12 \pm 0.35\text{ ms}$ | $24.87 \pm 7.15\text{ ms}$ | $6.21$ | $0.28 \pm 0.06$ | $1.0\text{ s}$ |
  | **Self-Hosted Container** | Write-Heavy (20/80)| $6.84 \pm 0.52\text{ ms}$ | $38.45 \pm 11.20\text{ ms}$| $15.40$| $0.46 \pm 0.09$ | $3.0\text{ s}$ |
  | **Managed Cloud (AWS)** | Read-Heavy (80/20) | $784.2 \pm 62.4\text{ ms}$ | $985.4 \pm 78.1\text{ ms}$ | $1,248.5$ | $0.09 \pm 0.02$ | $1.0\text{ s}$ |
  | **Managed Cloud (AWS)** | Balanced (50/50) | $826.5 \pm 71.8\text{ ms}$ | $1,114.2 \pm 94.6\text{ ms}$| $1,850.2$ | $0.12 \pm 0.03$ | $1.0\text{ s}$ |
  | **Managed Cloud (AWS)** | Write-Heavy (20/80)| $935.3 \pm 88.5\text{ ms}$ | $1,242.3 \pm 112.4\text{ ms}$| $2,420.8$| $0.11 \pm 0.03$ | $1.0\text{ s}$ |
- **Key Takeaway**: Increasing write ratio from 20% to 80% increases self-hosted tail latency by **+69%** due to lock serialization and WAL contention.

---

## Slide 5: Statistical Soundness: Error Bars & Confidence Intervals
- **Header**: Error Bar Visualization: 95% Student's-$t$ Confidence Intervals
- **Graphic**: Insert `results/figures/review3_statistical_bar_with_errorbars_postgres_managed.png`.
- **Bullet Points**:
  - Demonstrates strict compliance with Review 3 scoring guideline (*"A bar chart from a single run scores 0"*).
  - Explicit error whiskers represent symmetric 95% Confidence Intervals calculated via $t_{0.975, df=2} = 4.303$.
  - Both baseline and peak burst latencies show stable variance boundaries across repeated trial executions.
  - Recovery time consistently achieves bounded stabilization within 1.0 to 3.0 seconds post-burst.

---

## Slide 6: Dynamic Timeline with Shaded Variance Envelopes
- **Header**: Time-Series Progression with Shaded $\pm 1\sigma$ Variance Envelopes
- **Graphic**: Insert `results/figures/review3_timeseries_variance_envelope_postgres_managed.png`.
- **Phased Operational Insights**:
  - **Phase 1 [01s to 06s] Baseline**: Tight variance envelope confirms steady-state equilibrium at 150 QPS.
  - **Phase 2 [07s to 16s] 4x Shock Burst**: Envelope widens during the initial 3 seconds of load shock, reflecting transient queue buildup before settling into saturated throughput.
  - **Phase 3 [17s to 30s] Post-Burst Recovery**: Immediate convergence back to pre-burst bounds upon burst cessation.

---

## Slide 7: Exploratory Novelty: Iso-Workload Burst Shape Sensitivity
- **Header**: Novelty Contribution: Temporal Shape Matters as Much as Workload Volume
- **Concept Formulation**:
  - Enforced Iso-Workload Invariant: Total extra transactional volume held strictly constant at **3,600 extra requests**.
  - Three distinct arrival shapes:
    - **Sudden Step (`██████`)**: Constant +300 QPS plateau over 12 seconds.
    - **Gradual Ramp (`▂▃▄▅▆█`)**: Symmetrical triangular surge peaking at +550 QPS.
    - **Repeated Pulse (`██  ██`)**: Two +450 QPS pulses separated by a 4-second baseline lull.
- **Graphic**: Insert `beta_novelty/results/figures/novelty_hysteresis_and_baf_comparison.png`.

---

## Slide 8: The Performance Hysteresis Footprint ($\text{AUC}_H$)
- **Header**: Empirical Hysteresis: Why Arrival Rhythm Causes Lingering Degradation
- **Key Empirical Metrics**:
  - **Gradual Ramp**: $\text{AUC}_H = 0.004$ (Near-Zero Performance Hangover).
  - **Sudden Step**: $\text{AUC}_H = 0.272$ (Moderate Transient Hangover).
  - **Repeated Pulse**: $\text{AUC}_H = 0.673$ (**168x Higher Hangover!** Lingering $H(5\text{s}) = +0.223$).
- **Core Systems Discovery**:
  - Intermittent valleys between burst pulses cause the PostgreSQL engine to trigger deferred checkpointing and buffer page eviction.
  - When the subsequent shock wave arrives, the database experiences severe cache misses and lock contention, creating persistent post-burst latency degradation.

---

## Slide 9: Administrative Burden & 3-Year TCO Sensitivity Analysis
- **Header**: Operational Overhead & Financial Crossover Analysis
- **Left Card: Administrative Effort Logging (Objective O3)**
  - Empirical logging across 8 routine DBA operational tasks.
  - Self-Hosted Container: **98.0 minutes** initial onboarding.
  - Managed Cloud Database: **10.0 minutes** initial onboarding.
  - Result: **9.8x reduction in human maintenance toil**.
- **Right Card: 3-Year TCO Break-Even Crossover (Objective O4)**
  - Direct hosting: Self-hosted (\$45/mo) vs. Managed Cloud (\$150/mo).
  - Monthly labor: 25 hrs/mo (self-hosted) vs. 3 hrs/mo (managed).
  - **Empirical Crossover Wage: \$18.50 / hour**.
  - At industry-median DBA wage (\$50/hr), **Managed Cloud saves \$15,820 over 3 years**.
- **Graphic**: Insert `results/figures/tco_crossover_chart.png`.

---

## Slide 10: Live Demonstration Overview
- **Header**: Live Interactive Demonstration System (2 Marks)
- **Command Executed**: `python scripts/live_demo.py`
- **Interactive Features Demonstrated to the Panel**:
  - Connects to live database and validates schema idempotency.
  - Real-time ANSI colored progress streaming with visual latency bar graph.
  - Automatic calculation of empirical recovery threshold ($1.5\times$ baseline).
  - Dynamic detection of recovery timestamp (3 consecutive seconds under threshold).
  - Instant production SLO compliance evaluation ($p_{99} < 1000\text{ ms}$).

---

## Slide 11: Threats to Validity & Engineering Guidelines
- **Header**: Threats to Validity & Architectural Recommendations
- **Transparent Threats to Validity**:
  - Public Internet WAN transit introduces physical network RTT (~800 ms) conflated with engine processing.
  - Benchmark client driver operates sequentially; future work will test 500+ concurrent connection threads.
- **Architectural Recommendations for Cloud Practitioners**:
  - **Sub-10ms Latency Requirement**: Deploy self-hosted PostgreSQL within local private VPC to eliminate network hops.
  - **Bursty / Oscillating Traffic & Lean Team**: Choose Managed DBaaS (Neon / Cloud SQL) to eliminate buffer thrashing via connection proxies and save 22+ hours/month of human operational toil.

---

## Slide 12: Conclusion & Q&A
- **Header**: Summary of Contributions & Defense
- **Summary Bullet Points**:
  - Completed all 4 project objectives with multi-workload evidence and statistical error bars ($N=3$).
  - Discovered 168x hysteresis surge under repeated burst arrival geometry.
  - Quantified 9.8x administrative time savings and \$18.50/hr economic break-even crossover.
  - Provided runnable live terminal demonstration and 6–8 page IEEE conference paper.
- **Closing**: Thank you to our faculty guide Dr. Indra Priyadarshini S and the examination panel. We welcome your questions!
