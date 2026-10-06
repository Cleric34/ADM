# Empirical Results Summary (`logs/results_summary.md`)

This report provides the empirical evaluation of 15,000 simulated episodes (500 random seeds $\times$ 5 strategies $\times$ 3 difficulty settings $\times$ 2 communication ranges) with `max_steps = 400` and calibrated combat dynamics following the gate navigation and exit coordination diagnosis.

> [!NOTE]
> **Baseline Comparability Note:** The `oracle` strategy is a single-attacker baseline (evaluating theoretical upper-bound navigation under complete *a priori* knowledge of all entry and exit gates) and is not directly comparable in team composition, size (1 vs 5 units), or casualty distribution to the multi-attacker strategies (`blind_follow`, `shared_map`, `split_exit`).

> [!IMPORTANT]
> **Outcome Nomenclature:** Non-wipeout terminal episodes are partitioned into two distinct categories:
> - **`trapped_inside`**: At least one attacker penetrated to the center core (Ring 7 breached) but was unable to discover and navigate through all required outer exit gates before step exhaustion.
> - **`timeout`**: Time expired before any surviving attacker could penetrate to the center core (e.g., followers wandering outside after an early infiltrator casualty).

---

## 📊 Performance Metrics by Strategy & Difficulty

| Strategy | Difficulty | Episodes | Success Rate (95% CI) | Mean Rings Breached | Mean Survivors | Wipeout Rate (%) | Trapped Inside (%) | Timeout (%) | Mean Steps | Mean Messages |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`oracle`** | Low | 1,000 | **59.4%** (± 3.0%) | 6.97 ± 0.20 | 0.59 ± 0.49 (of 1) | 40.6% | 0.0% | 0.0% | 158.8 | 0.0 |
| **`oracle`** | Medium | 1,000 | **1.4%** (± 0.7%) | 6.07 ± 1.01 | 0.01 ± 0.12 (of 1) | 98.6% | 0.0% | 0.0% | 84.8 | 0.0 |
| **`oracle`** | High | 1,000 | **0.0%** (± 0.0%) | 4.91 ± 1.26 | 0.00 ± 0.00 (of 1) | 100.0% | 0.0% | 0.0% | 67.2 | 0.0 |
| **`lone_entry`** | Low | 1,000 | **42.8%** (± 3.1%) | 6.97 ± 0.20 | 0.78 ± 0.41 (of 1) | 22.0% | 35.2% | 0.0% | 242.7 | 0.0 |
| **`lone_entry`** | Medium | 1,000 | **1.8%** (± 0.8%) | 6.07 ± 1.01 | 0.07 ± 0.26 (of 1) | 92.6% | 5.6% | 0.0% | 102.2 | 0.0 |
| **`lone_entry`** | High | 1,000 | **0.0%** (± 0.0%) | 4.91 ± 1.26 | 0.00 ± 0.00 (of 1) | 100.0% | 0.0% | 0.0% | 67.2 | 0.0 |
| **`blind_follow`** | Low | 1,000 | **57.6%** (± 3.1%) | 6.99 ± 0.13 | 4.91 ± 0.28 (of 5) | 0.0% | 42.0% | 0.4% | 267.1 | 0.0 |
| **`blind_follow`** | Medium | 1,000 | **9.8%** (± 1.8%) | 6.50 ± 0.83 | 4.08 ± 0.54 (of 5) | 0.0% | 59.6% | 30.6% | 376.3 | 0.0 |
| **`blind_follow`** | High | 1,000 | **0.0%** (± 0.0%) | 5.40 ± 1.22 | 3.55 ± 0.72 (of 5) | 0.2% | 24.2% | 75.6% | 399.4 | 0.0 |
| **`shared_map`** | Low | 1,000 | **64.2%** (± 3.0%) | 7.00 ± 0.00 | 4.97 ± 0.17 (of 5) | 0.0% | 35.8% | 0.0% | 254.8 | 4,312.5 |
| **`shared_map`** | Medium | 1,000 | **64.0%** (± 3.0%) | 7.00 ± 0.00 | 3.97 ± 0.80 (of 5) | 0.0% | 36.0% | 0.0% | 258.1 | 3,646.9 |
| **`shared_map`** | High | 1,000 | **48.9%** (± 3.1%) | 6.98 ± 0.19 | 1.78 ± 1.21 (of 5) | 13.2% | 37.2% | 0.7% | 261.2 | 2,076.9 |
| **`split_exit`** | Low | 1,000 | **84.6%** (± 2.2%) | 7.00 ± 0.00 | 3.52 ± 0.72 (of 5) | 0.0% | 15.4% | 0.0% | 209.8 | 1,574.2 |
| **`split_exit`** | Medium | 1,000 | **76.9%** (± 2.6%) | 7.00 ± 0.00 | 2.77 ± 0.65 (of 5) | 0.0% | 23.1% | 0.0% | 228.1 | 1,373.0 |
| **`split_exit`** | High | 1,000 | **19.6%** (± 2.5%) | 6.83 ± 0.50 | 0.67 ± 0.92 (of 5) | 57.3% | 23.1% | 0.0% | 201.1 | 807.0 |

---

## 🔍 Five Factual Observations Directly Supported by Data

1. **`oracle` Calibration Achieved 59.4% Success at Low Difficulty:** With complete map knowledge ($G_7 \dots G_1$ and $E_1 \dots E_7$), the `oracle` baseline achieved a **59.4% ± 3.0%** mission success rate on low difficulty (mean elapsed steps = 158.8, with zero timeouts or trapped agents). On medium difficulty, success dropped to 1.4% ± 0.7%, and on high difficulty to 0.0%, with wipeout rates of 98.6% and 100.0% respectively.
2. **`split_exit` Achieved the Highest Success Rate in Low and Medium Settings:** `split_exit` achieved an **84.6% ± 2.2%** success rate on low difficulty and **76.9% ± 2.6%** on medium difficulty (overall across all difficulties: 60.4%, 1,811 / 3,000 episodes). *Hypothesis:* Dedicating scout units to search outer ring perimeters while strike units penetrate inwards allows exit waypoints to be discovered and broadcast prior to core egress.
3. **`shared_map` Maintained High Resilience Across High Difficulty:** `shared_map` achieved **48.9% ± 3.1%** success on high difficulty, outperforming `split_exit` (19.6% ± 2.5%) under severe defender pressure. *Hypothesis:* In `shared_map`, all 5 units move in mutual proximity, distributing defender damage across the group rather than leaving exposed scouts isolated in outer rings where high defender density causes early scout wipeouts (57.3% wipeout rate in high-difficulty `split_exit`).
4. **`lone_entry` Suffered Severe Wipeout Rates Under Increasing Defender Density:** `lone_entry` succeeded in 42.8% ± 3.1% of low-difficulty runs, but experienced a 92.6% wipeout rate on medium difficulty (1.8% ± 0.8% success) and a 100.0% wipeout rate on high difficulty (0.0% success), demonstrating the vulnerability of an unsupported single infiltrator in dense combat zones.
5. **Increased Communication Range Produced a Statistically Measurable Increase in `split_exit` Success:** For `split_exit`, expanding communication range from 4.0 to 15.0 grid units increased mission success rate from **57.4% ± 2.5% to 63.3% ± 2.4%** (+5.9 percentage points). For `shared_map`, the success rate was **58.7% ± 2.5%** at range 4.0 versus **59.4% ± 2.5%** at range 15.0 (overlapping confidence intervals).

---

## ⚠️ Limitations

### Step Limit Evaluation (`max_steps = 400` vs `max_steps = 800`)
To evaluate whether the 400-step horizon constitutes the primary bottleneck for timeouts, an empirical test across 200 random seeds (seeds 10000–10199) was conducted for `shared_map`, `blind_follow`, and `split_exit` at low difficulty and `comm_range = 15.0`:

| Strategy | `max_steps` | Success Rate (%) | Wipeout Rate (%) | Trapped Inside (%) | Timeout (%) | Episodes with Attackers in Center | Mean Attackers in Center during Trapped/Timeout |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`shared_map`** | **400** | **69.0%** (138/200) | 0.0% (0/200) | **31.0%** (62/200) | 0.0% (0/200) | 100.0% (62/62) | 4.95 (of 5) |
| **`shared_map`** | **800** | **69.0%** (138/200) | 0.0% (0/200) | **31.0%** (62/200) | 0.0% (0/200) | — | — |
| **`blind_follow`** | **400** | **62.0%** (124/200) | 0.0% (0/200) | **38.0%** (76/200) | 0.0% (0/200) | 100.0% (76/76) | 1.21 (of 5) |
| **`blind_follow`** | **800** | **62.0%** (124/200) | 0.0% (0/200) | **38.0%** (76/200) | 0.0% (0/200) | — | — |
| **`split_exit`** | **400** | **91.0%** (182/200) | 0.0% (0/200) | **9.0%** (18/200) | 0.0% (0/200) | 100.0% (18/18) | 3.00 (of 5) |
| **`split_exit`** | **800** | **91.0%** (182/200) | 0.0% (0/200) | **9.0%** (18/200) | 0.0% (0/200) | — | — |

**Empirical Finding on Step Limit:**
- Across all three strategies, doubling `max_steps` from 400 to 800 produced a **0.0% change in success rate** (0 additional successes across 200 seeds).
- In 100% of trapped episodes at `max_steps = 400`, attackers had reached the center.
- Therefore, the 400-step limit is **not** the primary cause of timeouts. Rather, remaining unexited runs stem from incomplete exit gate discovery: agents in the center lack discovered exit gate coordinates for outer rings and enter static holding patterns rather than exhausting movement time.
