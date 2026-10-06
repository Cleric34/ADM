# Chakravyuha Simulation (`chakravyuha-sim`)

A multi-agent simulation of the legendary **Chakravyuha** (from the *Mahabharata, Drona Parva*), formally modelled as a **multi-agent coordination problem under incomplete information**.

---

## 📖 Project Overview

The Chakravyuha is an ancient multi-tier, rotating military formation designed to trap and neutralize enemy forces. In game-theoretic and multi-agent systems terms, it represents:
- **Dynamic Spatial Topology**: Concentric rotating rings with time-varying entry/exit corridors.
- **Asymmetric Information & Observability**: Agents possess localized visibility (fog of war), incomplete knowledge of enemy coordination signals, and evolving belief states.
- **Multi-Agent Coordination & Trapping Dynamics**: Defenders cooperate to close breaches, adapt rotation speeds, and isolate infiltrators, while the infiltrator balances penetration depth against extraction feasibility.

---

## 📂 Project Structure

```text
chakravyuha-sim/
├── sim/                     # Core simulation engine and agent mechanics
│   ├── __init__.py
│   ├── environment.py       # Spatial grid, concentric rings, rotation dynamics, visibility
│   ├── agents.py            # Agent models (Infiltrator, Ring Defenders, Commanders)
│   ├── strategies.py        # Coordination policies, penetration heuristics, belief updates
│   └── engine.py            # Discrete-time simulation loop and combat/movement resolver
├── experiments/             # Parameter sweeps, metrics evaluation, and benchmark runs
│   └── __init__.py
├── app/                     # Interactive Streamlit visualizer dashboard
│   ├── __init__.py
│   └── app.py
├── tests/                   # Unit & integration test suite
│   ├── __init__.py
│   └── test_basic.py
├── logs/                    # Simulation telemetry and event log outputs
│   └── .gitkeep
├── requirements.txt         # Core dependencies
├── .gitignore
└── README.md
```

---

## 🛠️ Tech Stack & Constraints

- **Python 3.10+**
- **NumPy**: Vectorized spatial computations and matrix operations
- **Pandas**: Event logging, telemetry parsing, and metrics analysis
- **Matplotlib**: Formation visualization, trajectory plots, and heatmaps
- **Streamlit**: Interactive real-time simulation dashboard
- **Pytest**: Unit testing and verification

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

4. **Run test suite:**
   ```bash
   pytest
   ```

5. **Launch interactive dashboard:**
   ```bash
   streamlit run app/app.py
   ```
