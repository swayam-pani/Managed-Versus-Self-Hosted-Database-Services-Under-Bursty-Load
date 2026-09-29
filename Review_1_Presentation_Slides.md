# Project Review 1 Presentation Slides Outline

**Topic**: P8 · Managed Versus Self-Hosted Database Services Under Bursty Load: A Tail-Latency and Cost-of-Ownership Study  
**Date**: 27/08/26  
**Review 1 Target**: Problem Formulation and Baseline (10 Marks)

---

## Slide 1: Title & Overview
- **Project Title**: Managed Versus Self-Hosted Database Services Under Bursty Load: A Tail-Latency and Cost-of-Ownership Study
- **Domain**: Cloud Computing & Database Systems
- **Objective**: Comparative evaluation of Managed (AWS RDS / Cloud SQL) vs. Self-Hosted (Docker VM PostgreSQL) under diurnal & bursty workloads.

---

## Slide 2: Problem Restatement
- **Current Practice**: Cloud DB selections rely on steady-state benchmarks (constant QPS), showing self-hosted VMs as cheaper and faster.
- **Real-World Reality**: Production workloads are inherently **bursty & diurnal** with sharp load spikes.
- **Unaddressed Gaps**:
  1. How tail-latency ($p_{99}$) and recovery times degrade during load bursts.
  2. Missing operational/administrative DBA effort hours in 3-year TCO models.

---

## Slide 3: Falsifiable Hypothesis
> **Hypothesis**: Managed Cloud Database Services reduce 99th percentile tail-latency ($p_{99}$) by at least **45%** and post-burst recovery time by at least **60%** compared to a Self-Hosted containerized PostgreSQL baseline under bursty load conditions (burst factor $\ge 3.0\times$), despite Self-Hosted PostgreSQL exhibiting a **30% lower** steady-state hourly infrastructure cost when administrative labor is omitted.

---

## Slide 4: Literature Survey & Gap Analysis
- **Reviewed 15 Papers (2021–2026)**:
  - *Zhang et al. (2021)* & *Kumar & Singh (2022)*: Evaluated steady-state average latency; omitted burst recovery and DBA labor costs.
  - *Li et al. (2022)* & *Zhao et al. (2024)*: Focused on serverless auto-scaling lag rather than persistent relational containers.
  - *Patel & Verma (2023)*: Modeled static TCO without empirical DBA wall-clock logging.
- **Our Unifying Gap**: Simultaneous empirical measurement of **$p_{99}$ tail-latency degradation**, **recovery time**, **failure recovery**, and **labor-sensitive 3-year TCO**.

---

## Slide 5: Testbed Architecture & Verified Execution Evidence
- **Environment Stack**:
  - **Self-Hosted Engine**: PostgreSQL 15-alpine in Docker (`cpus: 2.0`, `memory: 2048MB`).
  - **Workload Harness**: Python OLTP benchmark runner (`scripts/run_baseline.py`).
  - **Database Schema**: Accounts, Transactions, Audit Logs seeded with 10,000 active records.
- **Empirical Execution Log Proof (`logs/environment_proof.log`)**:
  ```text
  [2026-08-30 15:12:19] Starting Testbed Environment Probe...
  [2026-08-30 15:12:19] System Node: DESKTOP-71KH1AK
  [2026-08-30 15:12:19] Deploying Self-Hosted Relational Database Testbed Container/Engine...
  [2026-08-30 15:12:19] Seeding testbed database with 10,000 account records...
  [2026-08-30 15:12:19] Testbed database initialized. Total accounts: 10,000
  [2026-08-30 15:12:19] Database Testbed is ACTIVE and ready for workload generation.
  [2026-08-30 15:12:49] All baseline benchmark scenarios completed successfully.
  ```

---

## Slide 6: Reproduced Baseline Results (Steady State)
- **Baseline Workload Runs**:

| Scenario | Target Load | Achieved QPS | Achieved TPS | Avg Latency | $p_{95}$ Latency | $p_{99}$ Tail Latency |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Low Load** | 100 QPS | 113.60 QPS | 18.88 TPS | 1.84 ms | 8.54 ms | **11.32 ms** |
| **Moderate Load**| 300 QPS | 265.72 QPS | 43.49 TPS | 1.68 ms | 8.16 ms | **9.64 ms** |
| **Write Heavy** | 500 QPS | 371.58 QPS | 123.86 TPS | 8.06 ms | 10.45 ms | **14.36 ms** |

- **Observation**: At steady-state, baseline performance remains stable with predictable low latency ($p_{99} < 15\text{ ms}$).

---

## Slide 7: Roadmap to Review 2 & Conclusion
- **Review 1 Deliverables Accomplished**:
  - Literature Survey Gap Table (15 Papers)
  - Falsifiable Hypothesis
  - Verified Running Testbed
  - Reproduced Baseline Benchmarks
- **Next Steps (Review 2 - 23/09/26)**:
  - Generate Diurnal & Bursty Workload Profiles ($3.0\times, 5.0\times$ bursts).
  - Comparative tail-latency & recovery time curves on shared axes.
  - Failure recovery & administrative time logging.
