# Managed vs Self-Hosted Database Services Under Bursty Load
### Review 2 — Implementation & Preliminary Results

**Team**: Swayam Pani (23BCE1526) · Anamitra Shrivastava (23BCE5012)  
**Faculty Guide**: Dr. Indra Priyadarshini S  
**Course**: Cloud Computing (Sem 7) · Date: September 2026

---

## Slide 1: Review 1 → Review 2 Evolution

- **Decoupled Architecture**: Upgraded from SQLite prototype to dual-backend testbed (`db_backend.py`).
- **Real Database Runtimes**: Dockerized PostgreSQL 15 vs. AWS Neon Managed Cloud PostgreSQL.
- **New Milestones**:
  - 3-Phase step-burst workload (150 QPS → 600 QPS → 150 QPS).
  - Auditable Recovery Time Metric ($p_{99} \le 1.5\times$ baseline).
  - 1x to 5x Burst-Factor parameter sweep.

---

## Slide 2: Experimental Setup

| Parameter | Self-Hosted Baseline | Managed Cloud DB |
| :--- | :--- | :--- |
| **Engine** | Docker PostgreSQL 15-alpine | AWS Neon Serverless Postgres |
| **Resource Limits** | 2.0 vCPU, 2048 MB RAM (cgroups) | Autoscaling Serverless Compute |
| **Proxy / Pooler** | Direct DB Connection | Automated pgBouncer Proxy |
| **Workload** | 75/25 Read/Write OLTP (10k seeded accounts) | 75/25 Read/Write OLTP (10k seeded accounts) |

---

## Slide 3: Comparative Burst Latency ($p_{99}$)

![Burst Tail Latency Comparison](figures/burst_p99_comparison_timeseries.png)

- **Self-Hosted Docker**: **+214% $p_{99}$ spike** (7.91 ms → **24.87 ms**) due to cgroup CPU throttling & WAL sync lock contention.
- **Managed Cloud**: **+32% relative variance** (935 ms → 1242 ms) — stable shock absorption via managed connection pooling.
- **Recovery Time**: Both cleared queue saturation in **< 1.0 second** post-burst.

---

## Slide 4: Ablation Study — Burst-Factor Sweep (1.0x to 5.0x)

![Ablation Burst Factor Sweep](figures/ablation_burst_factor.png)

- **Self-Hosted**: $p_{99}$ latency degrades progressively from 10.46 ms (1x) to 12.42 ms (5x) with increasing variance.
- **Managed Cloud**: Zero dropped queries (**0.0% error rate**), maintaining steady transaction throughput across all burst factors.
- **Key Insight**: Embedded databases fail to capture multi-process cloud concurrency shocks.

---

## Slide 5: Administrative Effort Logging (O3)

- **Self-Hosted Backup & Recovery Drill**: **72.0 minutes**  
  *(Manual `pg_dump`, crash simulation, volume remount & schema validation)*
- **Managed Cloud PITR & Branching**: **10.0 minutes total**  
  *(Instant point-in-time recovery & instant dev branching)*
- **Impact**: **7.2x Higher Operational Effort** for self-hosted database management.

---

## Slide 6: 3-Year Total Cost of Ownership (O4)

![TCO Crossover Chart](figures/tco_crossover_chart.png)

- **Raw Cloud Bill**: Self-Hosted (\$45/mo) vs Managed DB (\$150/mo).
- **TCO Crossover Point**: **$18.50 / hour** DBA labor rate.
- **Key Finding**: Managed Cloud DB is **more cost-effective** for any enterprise with DBA labor rates above $18.50/hr.

---

## Slide 7: Summary & Review 3 Roadmap

### Key Findings
- Managed Cloud DB absorbs burst shocks with **7x lower relative latency spike** (+32% vs +214%).
- Self-hosted operations require **7.2x more human admin effort**.

### Review 3 Execution Roadmap
- **VPC Co-location**: Move client to AWS EC2 in same region to remove WAN baseline latency.
- **Multi-Client Concurrency**: Deploy sysbench / YCSB multi-threaded drivers.
- **Fault Injection**: Automated container/node kill & RTO/RPO measurement.
