# Diagnostic Report: `shared_map` Strategy Timeout Investigation (`logs/diagnosis_shared_map.md`)

This report documents the diagnostic investigation into why the `shared_map` strategy exhibited ~90% timeouts in initial experimental runs despite consistently breaching all concentric rings to reach the center.

---

## 1. Initial Episode Inspection (5 Low-Difficulty Seeds)

Five consecutive timeout episodes at `difficulty="low"`, `comm_range=15.0`, and `max_steps=400` were inspected:

| Seed | Final Positions ($t=400$) | Reached Center | Known Exit Gates | Last 20 Positions Trajectory |
| :--- | :--- | :---: | :--- | :--- |
| **10001** | Abhimanyu: `(29, 28)`<br>Followers 1–4: `(30, 27)`, `(30, 26)`, `(30, 25)`, `(30, 24)` | `False` | `{1: (16, 13), 2: (19, 19), 3: (9, 21), 4: (7, 13), 5: (20, 25), 6: (3, 6), 7: (14, 29)}` | **Standing Still**: Abhimanyu standing at outer Gate 7 `(29, 28)`; followers queued behind. |
| **10002** | Abhimanyu: `(29, 13)`<br>Followers 1–4: `(30, 12)`, `(30, 11)`, `(30, 10)`, `(30, 9)` | `False` | `{1: (16, 13), 2: (18, 11), 3: (9, 18), 4: (9, 7), 5: (6, 25), 7: (7, 1)}` | **Standing Still**: Abhimanyu standing at outer Gate 7 `(29, 13)`; followers queued behind. |
| **10003** | Abhimanyu: `(1, 6)`<br>Followers 1–4: `(2, 5)`, `(2, 4)`, `(2, 3)`, `(3, 2)` | `False` | `{1: (17, 15), 2: (16, 11), 3: (21, 15), 4: (17, 23), 5: (25, 19), 6: (27, 20), 7: (18, 1)}` | **Standing Still**: Abhimanyu standing at outer Gate 7 `(1, 6)`; followers queued behind. |
| **10004** | Abhimanyu: `(1, 8)`<br>Followers 1–4: `(2, 9)`, `(2, 10)`, `(2, 11)`, `(3, 12)` | `False` | `{1: (17, 15), 4: (21, 7), 6: (3, 12), 7: (19, 1)}` | **Standing Still**: Abhimanyu standing at outer Gate 7 `(1, 8)`; followers queued behind. |
| **10005** | Abhimanyu: `(11, 1)`<br>Followers 1–4: `(12, 2)`, `(13, 2)`, `(14, 2)`, `(15, 2)` | `False` | `{1: (14, 17), 2: (11, 12), 3: (21, 13)}` | **Standing Still**: Abhimanyu standing at outer Gate 7 `(11, 1)`; followers queued behind. |

---

## 2. Root Cause: Two Software Bugs Identified

### Bug 1: Inward Target Fallback to Gate 7 After Gate 1
- **Mechanism:** When navigating inwards, `target_entry_ring` counts down from 7 to 1. When an agent breached Ring 1 (`target_entry_ring == 1`), `target_entry_ring` was decremented to `0`.
- **Faulty Code (`sim/strategies.py`):**
  ```python
  if not a.has_reached_center:
      if a.target_entry_ring in a.known_entry_gates:
          target = a.known_entry_gates[a.target_entry_ring]
          if a.pos == target:
              a.target_entry_ring -= 1
              target = a.known_entry_gates.get(a.target_entry_ring, env.center)
      else:
          target = a.known_entry_gates.get(7, env.entry_gates[7])  # BUG
  ```
- **Failure Sequence:** On the step after breaching Gate 1, `a.target_entry_ring` was `0`. Because `0 not in a.known_entry_gates`, execution entered the `else:` branch, resetting the target to Gate 7 (`entry_gates[7]`). The agent reversed direction, traversed back to the outer ring, and arrived at Gate 7 (which was locked by Jayadratha), standing frozen there until timeout.

### Bug 2: Exit Success Condition Incomplete for Non-Sequential Exit Knowledge
- **Mechanism:** Agents under incomplete information do not always discover exit gates in strict inner-to-outer sequence ($E_1 \dots E_7$). If intermediate exit gates were skipped, `a.target_exit_ring` remained $< 7$.
- **Faulty Code (`sim/strategies.py`):**
  ```python
  if a.has_reached_center and (current_ring > config.num_rings or a.target_exit_ring > 7):
      a.has_exited = True
  ```
- **Failure Sequence:** When an agent reached the outermost exit gate (`pos == env.exit_gates[7]`), `env.get_ring_of_point(pos)` evaluated to 7 (on the Ring 7 perimeter, not $> 7$). Because neither `target_exit_ring > 7` nor `current_ring > 7` was satisfied, `has_exited` remained `False` and the agent loitered indefinitely on the exit cell.

---

## 3. Code Modifications

In [`sim/strategies.py`](file:///C:/Users/Yashik%20S/OneDrive/Desktop/ADM/chakravyuha-sim/sim/strategies.py):
1. Corrected inward navigation to check `if a.target_entry_ring > 0:` and set `target = env.center` when `target_entry_ring == 0`.
2. Updated exit completion to check `if a.has_reached_center and (a.pos == env.exit_gates[7] or current_ring > config.num_rings or a.target_exit_ring > 7): a.has_exited = True`.
3. Added automated unit test [`test_shared_map_breaches_center_and_navigates_exit`](file:///C:/Users/Yashik%20S/OneDrive/Desktop/ADM/chakravyuha-sim/tests/test_simulation.py) to [`tests/test_simulation.py`](file:///C:/Users/Yashik%20S/OneDrive/Desktop/ADM/chakravyuha-sim/tests/test_simulation.py).

---

## 4. Before vs After Performance of `shared_map` (1,000 Episodes per Difficulty)

| Metric | Difficulty | Pre-Fix (`logs/results_v1.csv` / initial) | Post-Fix (`logs/results.csv`) | Absolute Change |
| :--- | :--- | :---: | :---: | :---: |
| **Success Rate (%)** | **Low** | 10.1% | **64.2%** (± 3.0%) | **+54.1%** |
| **Success Rate (%)** | **Medium** | 9.9% | **64.0%** (± 3.0%) | **+54.1%** |
| **Success Rate (%)** | **High** | 6.0% | **48.9%** (± 3.1%) | **+42.9%** |
| **Overall Success Rate** | **All** | 8.7% (260 / 3,000) | **59.0%** (1,771 / 3,000) | **+50.3%** |
| **Timeout Rate (%)** | **Low** | 89.8% | **35.8%** | **-54.0%** |
| **Timeout Rate (%)** | **Medium** | 87.6% | **36.0%** | **-51.6%** |
| **Timeout Rate (%)** | **High** | 86.3% | **37.9%** | **-48.4%** |
