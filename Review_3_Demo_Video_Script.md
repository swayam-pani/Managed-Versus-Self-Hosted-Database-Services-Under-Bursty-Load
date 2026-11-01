# Project Review 3: Recorded Video Presentation & Live Demonstration Script

**Project Topic**: P8 · *Managed Versus Self-Hosted Database Services Under Bursty Load: A Tail-Latency and Cost-of-Ownership Study*  
**Course / Domain**: Cloud Computing (Semester 7)  
**Date of Evaluation**: October 21, 2026 (Review 3 Final Presentation)  
**Students**: Swayam Pani (23BCE1526) · Anamitra Shrivastava (23BCE5012)  
**Faculty Guide**: Dr. Indra Priyadarshini S  

---

## 1. Video Recording Setup & Technical Guidance

- **Total Duration**: Exactly 3 minutes (180 seconds).
- **Video Resolution**: 1080p (1920x1080) at 30 or 60 FPS.
- **Screen Layout**:
  - Left / Top Window: Active Terminal displaying live benchmark execution (`python scripts/live_demo.py`).
  - Right / Bottom Window: High-resolution figures (`review3_statistical_bar_with_errorbars.png` and `novelty_hysteresis_and_baf_comparison.png`).
- **Audio**: Clear microphone with background noise cancellation.

---

## 2. Minute-by-Minute Narration Script

```
+----------------------------------------------------------------------------------------------------+
|                                   3-MINUTE VIDEO PRESENTATION TIMELINE                             |
+----------------------------------------------------------------------------------------------------+
| 0:00 - 0:35  | Segment 1: Architectural Context & Core Problem Formulation                         |
| 0:35 - 1:20  | Segment 2: Live Terminal Demonstration Walkthrough (Interactive Run)                |
| 1:20 - 1:55  | Segment 3: Statistical Rigor (Multi-Workload, N=3 Trials, Mean, Variance & CIs)    |
| 1:55 - 2:35  | Segment 4: Exploratory Novelty (Iso-Workload Burst Shape Sensitivity & Hysteresis)  |
| 2:35 - 3:00  | Segment 5: Administrative Efficiency & 3-Year TCO Crossover Analysis                |
+----------------------------------------------------------------------------------------------------+
```

---

### [0:00 - 0:35] Segment 1: Architectural Context & Problem Formulation
**Visual**: Show project title slide and the high-level architecture diagram contrasting Self-Hosted Docker PostgreSQL vs. AWS Neon Serverless PostgreSQL.

**Speaker (Swayam / Anamitra)**:
> *"Good morning, respected evaluators. Welcome to the final demonstration and defense of Project P8: 'Managed Versus Self-Hosted Database Services Under Bursty Load: A Tail-Latency and Cost-of-Ownership Study.'*
> 
> *When modern engineering teams migrate from self-hosted containerized databases to managed cloud DBaaS, they face a classic engineering dilemma: does managed autoscaling actually protect tail latency ($p_{99}$) during sudden traffic surges, and at what financial cost?*
> 
> *To answer this, we engineered an empirical, reproducible testbed comparing containerized PostgreSQL 15—strictly constrained with Linux cgroups to 2.0 vCPUs and 2048 MB of RAM—against a live, production serverless cloud database on AWS Neon with built-in pgBouncer connection pooling and storage disaggregation."*

---

### [0:35 - 1:20] Segment 2: Live Terminal Demonstration Walkthrough
**Visual**: Switch full screen to the terminal. Run command:
```bash
python scripts/live_demo.py
```
Show the ANSI color streaming bars and the real-time latency updates across Phase 1, Phase 2, and Phase 3.

**Speaker**:
> *"Rather than relying on pre-rendered slides, here is our live, automated demonstration running in real time.*
> 
> *Our benchmark driver is executing a 20-second operational cycle against our seeded 10,000-row database:*
> 1. **Phase 1: Baseline [01s to 05s]**: *The system maintains a steady-state 150 QPS baseline, establishing our normal operating p99.*
> 2. **Phase 2: 4x Shock Burst [06s to 10s]**: *At second 6, we instantly escalate traffic by 300% to 600 QPS. Notice the visual red indicators in the terminal—queue depths surge, and tail latency increases.*
> 3. **Phase 3: Post-Burst Recovery [11s to 20s]**: *Load steps immediately back to 150 QPS. Our automated recovery algorithm watches for the exact second p99 returns to and remains under 1.5 times baseline for 3 consecutive seconds.*
> 
> *As you can see on the live report card, the system successfully recovered in just 1 second, achieved a Burst Amplification Factor of 0.11, and strictly fulfilled our production Service Level Objective of p99 under 1000 milliseconds."*

---

### [1:20 - 1:55] Segment 3: Statistical Soundness & Multi-Workload Trials
**Visual**: Display `results/figures/review3_statistical_bar_with_errorbars_postgres_managed.png` and `review3_timeseries_variance_envelope_postgres_managed.png`. Point out error whiskers and shaded variance envelopes.

**Speaker**:
> *"To fulfill the strict statistical rubric of Review 3, our evaluation goes far beyond single-run charts. We evaluated three distinct production OLTP workloads:*
> - **Read-Heavy (80% SELECT / 20% UPDATE)** *simulating catalogs,*
> - **Balanced (50/50)** *simulating e-commerce carts, and*
> - **Write-Heavy (20/80)** *simulating financial ledgers.*
> 
> *Each workload was repeated across N=3 independent trials to compute true sample means, sample variances, and 95% Student's-t confidence intervals.*
> 
> *Notice our error-bar chart: as write intensity increases from 20% to 80%, peak tail latency escalates by 69% on self-hosted containers due to WAL disk serialization bottlenecks, whereas the managed cloud service absorbs write surges with twice the relative resilience, maintaining tight variance envelopes."*

---

### [1:55 - 2:35] Segment 4: Exploratory Novelty — Iso-Workload Burst Shape Sensitivity
**Visual**: Display `beta_novelty/results/figures/novelty_hysteresis_and_baf_comparison.png` and `performance_hysteresis_decay_postgres_managed.png`. Highlight the 168x hysteresis contrast.

**Speaker**:
> *"For our novelty contribution, we investigated a critical systems question: Does the temporal arrival geometry of a burst matter, independent of total workload volume?*
> 
> *We formulated an Iso-Workload Invariant, holding total extra work strictly constant at exactly 3,600 transactions across three shapes: Sudden Step, Gradual Ramp, and Repeated Pulse.*
> 
> *Our empirical finding was striking: While a gradual ramp produces near-zero hangover, the Repeated Pulse pattern induces **168 times higher cumulative hysteresis ($AUC_H = 0.673$)** and lingering latency elevation 5 seconds after the burst ended.*
> 
> *This occurs because intermittent pulse valleys trigger uncoordinated checkpointing and cache eviction, leaving the engine vulnerable when subsequent shockwaves hit. This proves arrival rhythm—not just volume—is a primary driver of database tail latency."*

---

### [2:35 - 3:00] Segment 5: Administrative Burden & 3-Year TCO Crossover
**Visual**: Display Table III (Administrative Effort) and `results/figures/tco_crossover_chart.png`.

**Speaker**:
> *"Finally, we evaluated operational and financial sustainability. Administrative time tracking across 8 DBA operational tasks showed a **9.8x reduction in human maintenance toil**—from 98 minutes down to 10 minutes on managed cloud.*
> 
> *In our 3-year TCO sensitivity model, we identified the exact economic break-even crossover at **\$18.50 per hour**. While self-hosted appears cheaper if developer labor is free ($0/hr), at any commercial wage above \$18.50/hr, the managed cloud database yields significant net savings—saving over **\$15,820 to \$39,220 over three years**.*
> 
> *In conclusion, for burst-heavy production applications, managed serverless databases justify their hosting premium through tail resilience and labor efficiency. Thank you, and we welcome your questions."*

---

## 3. Reviewer Defense Guide: Anticipated Questions & Model Answers

### Question 1: *"Why is the absolute baseline latency of your managed cloud database (~800 ms) so much higher than the Docker container (<10 ms)?"*
**Answer**:
> *"That is an essential architectural distinction. The Docker container executes locally over a zero-latency Linux socket/loopback, measuring pure internal database engine processing. In contrast, our managed database is deployed on AWS Neon in Ohio (us-east-2), while our benchmark client operated from India. That ~800 ms baseline is physical transatlantic network round-trip time (RTT) and TLSv1.3 cryptographic negotiation across the public internet.*
> 
> *What is scientifically significant is not the absolute network floor, but the **relative tail amplification (BAF)**: when hit by a 400% load surge, the local container's tail latency exploded by +214%, whereas the cloud database increased by only +32%, proving the resilience of its connection-pooling architecture."*

### Question 2: *"Why does the Repeated Pulse burst shape cause 168x higher hysteresis than the Gradual Ramp?"*
**Answer**:
> *"When a burst ramps gradually, the PostgreSQL buffer manager and dirty-page background writer adapt progressively. However, under repeated pulses, the temporary 4-second baseline lull between pulses misleads the engine into initiating deferred background WAL flushing and buffer page eviction. When the second 450 QPS pulse arrives, the database suffers severe cache misses and lock contention on half-flushed pages, resulting in a persistent post-burst hangover ($AUC_H = 0.673$)."*

### Question 3: *"How do you prove that your results are statistically sound and not just random run-to-run noise?"*
**Answer**:
> *"In accordance with the Review 3 rubric, we never report single-run observations. Every workload—Read-Heavy, Balanced, and Write-Heavy—was executed across N=3 independent trials. For every single metric, we compute the sample mean, sample variance, standard deviation, and formal 95% Confidence Intervals using Student's-t distribution (df=2, t=4.303). Every chart features explicit error whiskers and shaded variance envelopes."*

### Question 4: *"What is your TCO crossover point and how did you derive it?"*
**Answer**:
> *"We modeled 3-year TCO as 36 times monthly infrastructure cost plus 36 times monthly DBA hours multiplied by hourly wage. With self-hosted requiring $45/mo infrastructure and 25 hours/mo maintenance, versus managed cloud requiring $150/mo infrastructure and only 3 hours/mo maintenance, equating the two formulas yields an exact break-even wage rate of **\$18.50 per hour**. At any standard industry wage (e.g. $50/hr), the managed cloud database saves over $15,800 over 3 years."*
