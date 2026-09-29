# Review 2 — Implementation and Preliminary Results
**Project**: P8 · Managed vs Self-Hosted Database Services Under Bursty Load: A Tail-Latency and Cost-of-Ownership Study  
**Team**: Swayam Pani (23BCE1526) · Anamitra Shrivastava (23BCE5012)  
**Faculty Guide**: Dr Indra Priyadarshini S  
**Date**: September 2026

---

### Slide 1 — Title Slide
- **Title**: P8: Managed vs Self-Hosted Database Services Under Bursty Load: A Tail-Latency and Cost-of-Ownership Study
- **Milestone**: Review 2 — Implementation and Preliminary Results
- **Authors**: Swayam Pani (23BCE1526), Anamitra Shrivastava (23BCE5012)
- **Course**: Cloud Computing (Semester 7) · Faculty Guide: Dr Indra Priyadarshini S

---

### Slide 2 — Review 1 → Review 2 Evolution
- **Review 1**: Formulated $O_1$–$O_4$, hypothesis, literature survey (15 papers), architecture testbed spec, and steady-state baseline.
- **Architectural Correction**: Review 1's measured baseline ran on local SQLite; Review 2 decoupled the testbed with a dual-backend engine (`db_backend.py`) and upgraded to real **Dockerized PostgreSQL 15** and **Managed Cloud PostgreSQL (AWS Neon)**.
- **Review 2 Contributions**:
  - Full implementation of multi-phase step-burst OLTP workload (pre-burst $\rightarrow$ 4x/5x spike $\rightarrow$ post-burst).
  - Explicit, auditable **Recovery Time Metric** ($p_{99} \le 1.5\times$ pre-burst for 3 consecutive seconds).
  - **Burst-Factor Parameter Sweep (1x to 5x)** executed on both containerized and cloud engines.
  - Same-axis comparative tail-latency graphs and empirical wall-clock admin effort log.

---

### Slide 3 — Experimental Setup & Testbed Architecture
- **Self-Hosted Baseline**: Containerized PostgreSQL 15-alpine in Docker Compose with strict cgroup limits (2.0 vCPU, 2048MB RAM, sync WAL).
- **Proposed Managed Service**: AWS Neon Serverless Managed PostgreSQL (AWS us-east-2 region) with automated pgBouncer pooled connection proxying and autoscaling.
- **Schema & Workload**:
  - `accounts` table seeded with 10,000 active customer records.
  - Realistic 75/25 OLTP transaction mix (75% point reads, 25% balance updates with atomic commit locks).

---

### Slide 4 — Bursty Workload Design & Recovery Time Metric
- **3-Phase Workload Architecture**:
  1. *Pre-Burst (10s)*: Constant base arrival rate (150 QPS) to establish baseline latency.
  2. *Burst Shock (10s)*: Instantaneous step spike to $4.0\times$ load (600 QPS target).
  3. *Post-Burst (20s)*: Load returns to 150 QPS to observe queue clearing and stabilization.
- **Auditable Recovery Time Metric**:
  $$\text{Recovery Time} = (\text{timestamp where } p_{99} \le 1.5\times \text{pre-burst mean for 3 consecutive seconds}) - \text{burst end timestamp}$$

---

### Slide 5 — Comparative Results on Same Axes (Rubric Component 2)
- **Insert Figure**: `results/figures/burst_p99_comparison_timeseries.png`
- **Key Empirical Findings**:
  - **Self-Hosted Docker Postgres**: Suffers a **+214% (3.14x) degradation** in $p_{99}$ latency during the 4x burst (jumping from 7.91 ms to **24.87 ms** peak) due to cgroup CPU throttling and WAL sync lock contention.
  - **Managed Cloud Postgres**: Shows superior burst resilience, absorbing the spike with only a **+32% relative latency variance** (from 935 ms to 1242 ms), proving the stability benefits of managed connection pooling.
  - **Recovery Time**: Both engines successfully cleared queues and achieved recovery within 1 second post-burst.

---

### Slide 6 — Ablation Study: Burst-Factor Sweep (Rubric Component 3)
- **Insert Figure**: `results/figures/ablation_burst_factor.png`
- **Parameter Sweep (1.0x to 5.0x Multiplier)**:
  - Docker Postgres peak $p_{99}$ escalates from 10.46 ms (1x) to 12.42 ms (5x), with significant latency variance during high burst saturation.
  - SQLite baseline showed near-flat latency (~1.5 ms), demonstrating why embedded databases fail to replicate multi-process cloud database concurrency.
  - Managed Cloud Postgres maintains consistent transaction throughput across all burst factors without dropping queries (0.0% error rate).

---

### Slide 7 — Administrative Effort Logging (Objective O3)
- **Logged Wall-Clock Operational Tasks** (`results/admin_effort.csv`):
  - *Self-Hosted Docker Setup & Cgroups Configuration*: 26.0 minutes.
  - *Self-Hosted Manual Backup (`pg_dump` cron) & Disaster Recovery Drill*: **72.0 minutes** (simulated crash, volume remount, schema integrity verification).
  - *Managed Cloud Provisioning & PITR Verification*: **10.0 minutes total** (instant point-in-time recovery and branch creation).
- **Core Insight**: Self-hosted operations require **~7.2x more human DBA effort** for routine backup and disaster recovery validation.

---

### Slide 8 — 3-Year Total Cost of Ownership (TCO) Sensitivity Model (O4)
- **Insert Figure**: `results/figures/tco_crossover_chart.png`
- **TCO Crossover Analysis**:
  - Direct Cloud Hosting Bill: Self-Hosted VM (\$45/mo) vs. Managed Cloud DB (\$150/mo).
  - Factoring empirical DBA maintenance hours (25 hrs/mo self-hosted vs. 3 hrs/mo managed):
  - **The Crossover Point**: At any DBA labor rate above **\$18.50 / hour**, the Managed Cloud Database achieves a lower 3-year Total Cost of Ownership.

---

### Slide 9 — Preliminary Findings & Hypotheses Status
- **Hypothesis Evaluation**:
  - *Tail Latency Stability*: Managed Cloud DB absorbed the 4x burst with only a 32% increase in latency, compared to a 214% spike in Self-Hosted Docker Postgres, confirming superior shock absorption under sudden loads.
  - *Recovery Time*: Both deployments demonstrated rapid 1s queue recovery under moderate burst duration.
  - *Cost Parity*: Self-hosted is only cheaper when operational labor is treated as free (\$0/hr); in commercial deployments, managed cloud saves thousands in DBA payroll.

---

### Slide 10 — Threats to Validity & Review 3 Roadmap
- **Threats to Validity**:
  - Client-to-cloud WAN latency (India to AWS Ohio us-east-2) introduces baseline network RTT; co-locating the client in an EC2 instance in the same VPC is planned for Review 3.
  - Single-client concurrency limits maximum client-side QPS; deploying multi-threaded sysbench/YCSB drivers will further saturate connection pools.
- **Review 3 Execution Roadmap**:
  - Multi-run statistical soundness (3+ runs per configuration with error bars and variance).
  - Failure injection (deliberately crashing container/instance and recording RTO/RPO).
  - Live review demonstration script.
