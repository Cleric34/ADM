# Chakravyuha Multi-Agent Simulation (`chakravyuha-sim`)

A university mini-project implementing a discrete 2D multi-agent simulation of the ancient **Chakravyuha** formation (from the *Mahabharata, Drona Parva*), formally formulated as a **multi-agent coordination problem under incomplete information**.

---

## 📖 Project Overview

On Day 13 of the Kurukshetra War, Guru Dronacharya deployed the **Chakravyuha**—a 7-layered, concentric rotating formation designed to trap and neutralize the Pandava forces. Only Arjuna and Krishna possessed the knowledge to penetrate and extract from the formation. 

This project computationalizes the tactical dynamics:
1. **Asymmetric Knowledge**: Abhimanyu possesses complete a priori knowledge of entry gates ($G_7 \to G_1$), but zero knowledge of exit corridors ($E_1 \to E_7$). Followers start with zero gate knowledge.
2. **Jayadratha's Gate Lockdown**: Once the primary infiltrator breaches the outer perimeter (Gate 7), Jayadratha seals the entrance, preventing followers from following.
3. **Inward Escalating Defense**: Defenders become progressively stronger (increased health and attack power) in inner rings, culminating in Maharathi guardians at the core.
4. **Coordination Under Uncertainty**: Evaluates how limited vision radius and message range constrain multi-agent cooperation across 4 distinct strategies:
   - `lone_entry`: Abhimanyu enters the formation entirely alone.
   - `blind_follow`: Followers trail Abhimanyu's trajectory without communication.
   - `shared_map`: Agents dynamically broadcast discovered gate locations within communication range.
   - `split_exit`: Dedicated scouts search the perimeter for exit routes while strike forces penetrate inward.

---

## 📂 Project Structure

```text
chakravyuha-sim/
├── sim/
│   ├── __init__.py
│   ├── environment.py       # 7-ring concentric grid, gate mechanics, Jayadratha lock, renderers
│   ├── agents.py            # Attacker & Defender agent models, vision, message channels, power scaling
│   ├── strategies.py        # 4 coordination strategies: lone_entry, blind_follow, shared_map, split_exit
│   └── engine.py            # Episode loop, defender patrol, combat resolution, telemetry
├── experiments/
│   ├── __init__.py
│   └── run_experiments.py   # Full factorial sweep (12,000 episodes) & figure generation
├── app/
│   ├── __init__.py
│   └── streamlit_app.py     # Interactive Streamlit dashboard with playback & batch benchmarking
├── tests/
│   ├── __init__.py
│   ├── test_basic.py        # Sanity and interface verification
│   └── test_simulation.py   # Determinism, Jayadratha lock, vision limits, messaging constraints
├── logs/
│   ├── figures/             # Matplotlib analysis figures (success, penetration, survival, comm range)
│   ├── results.csv          # Raw telemetry for 12,000 Monte Carlo runs
│   ├── results_summary.md   # Empirical analysis table and 5 factual findings
│   └── weekly_log.md        # Weekly progress, responsibility, problems, and evidence log
├── requirements.txt         # numpy, pandas, matplotlib, streamlit, pytest
├── .gitignore
└── README.md
```

---

## 🛠️ Tech Stack & Constraints

- **Python 3.10+**
- **NumPy**: Vectorized coordinate mathematics and state manipulation
- **Pandas**: Telemetry recording, data aggregation, and CSV serialization
- **Matplotlib**: Tactical grid rendering and experimental analysis charts
- **Streamlit**: Interactive web dashboard and visual scrub playback
- **Pytest**: Automated test suite

---

## 🚀 Setup & Installation

1. **Clone repository and navigate to project root:**
   ```bash
   cd chakravyuha-sim
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   # Windows (PowerShell):
   .\.venv\Scripts\Activate.ps1
   # Linux/macOS:
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## 🧪 Running the Test Suite

Run pytest to verify determinism, Jayadratha gate locking, perception limits, and messaging bounds:
```bash
pytest -v
```

---

## 🔬 Running the Experiments

To execute the 12,000-episode Monte Carlo sweep across 4 strategies, 3 difficulties, and 2 communication ranges:
```bash
python experiments/run_experiments.py
```
Outputs generated:
- Raw empirical dataset: `logs/results.csv`
- Analysis figures in `logs/figures/`:
  - `success_rate_by_strategy.png`
  - `average_rings_breached.png`
  - `survival_rate.png`
  - `comm_range_effect.png`
- Summary analysis: `logs/results_summary.md`

---

## 🖥️ Launching the Interactive Web Dashboard

Launch the Streamlit app to interactively run episodes, scrub through tactical step frames, and run real-time batch benchmarks:
```bash
streamlit run app/streamlit_app.py
```

---

## ⚠️ Limitations & Future Work

1. **Discrete Grid Representation**: The 7-ring formation is discretized onto a 2D Chebyshev grid. Continuous-space circular trigonometry or fluid crowd dynamics could provide finer granularity.
2. **Deterministic Jayadratha Barrier**: In this model, Jayadratha acts as a complete gate lock. In historical lore, Ghatotkacha or Bhima contested him with partial stochastic breach probabilities.
3. **Turn-Based Combat Resolution**: Combat is resolved via simultaneous discrete health exchanges rather than weapon ranges, stamina curves, or directional shield mechanics.
4. **Static Ring Orientations**: The rings currently retain static gate configurations per seed. Future iterations can model continuous rotational velocities for each concentric ring layer.
