"""
app/streamlit_app.py - Interactive Streamlit Dashboard for Chakravyuha Simulation.

Provides:
- Sidebar controls for Strategy, Difficulty, Communication Range, Seed, and Animation Speed.
- "Run one episode": Step-through / animated visual tactical grid of the 7 rings with agent status.
- "Run batch": Real-time empirical evaluation comparing success rates, penetration depth, and survivors across strategies.
- Plain-English explainer panel linking computational multi-agent dynamics to the Mahabharata (Drona Parva).
"""

import sys
import os
import time
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Ensure root package is available
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sim.environment import Config, ChakravyuhaEnvironment
from sim.engine import run_episode
from sim.strategies import STRATEGY_REGISTRY


st.set_page_config(
    page_title="Chakravyuha Simulator | Multi-Agent Coordination",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #E2E8F0;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #A0AEC0;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #1A202C;
        border-radius: 8px;
        padding: 12px;
        border-left: 4px solid #3182CE;
    }
    .explainer-box {
        background-color: #1A202C;
        border-radius: 10px;
        padding: 18px;
        border: 1px solid #2D3748;
        margin-top: 15px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🛡️ Chakravyuha Multi-Agent Simulation</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Modeling Drona Parva Tactical Penetration & Trapping as Coordination Under Incomplete Information</div>', unsafe_allow_html=True)

# ----------------- SIDEBAR CONTROLS -----------------
st.sidebar.header("⚙️ Simulation Controls")

strategy_options = {
    "oracle": "0. Oracle (Full Map Knowledge Baseline)",
    "lone_entry": "1. Lone Entry (Abhimanyu Alone)",
    "blind_follow": "2. Blind Follow (Followers Trail Without Comm)",
    "shared_map": "3. Shared Map (Dynamic Gate Messaging)",
    "split_exit": "4. Split Exit (Scout Perimeter + Inward Breach)",
}

selected_strategy = st.sidebar.selectbox(
    "Attacker Strategy",
    options=list(strategy_options.keys()),
    format_func=lambda x: strategy_options[x],
)

difficulty = st.sidebar.selectbox(
    "Defense Difficulty",
    options=["low", "medium", "high"],
    index=1,
    help="Determines the number and combat strength of Kaurava defenders per ring.",
)

comm_range = st.sidebar.slider(
    "Communication Range (Grid Units)",
    min_value=2.0,
    max_value=20.0,
    value=6.0,
    step=1.0,
    help="Maximum distance over which Pandava agents can broadcast gate discoveries.",
)

seed = st.sidebar.number_input(
    "Random Seed",
    min_value=0,
    max_value=999999,
    value=42,
    step=1,
    help="Sets deterministic initial conditions for formation gates and defender positions.",
)

max_steps = st.sidebar.slider(
    "Max Episode Steps",
    min_value=30,
    max_value=250,
    value=120,
    step=10,
)

# ----------------- TABS -----------------
tab1, tab2, tab3 = st.tabs(["⚔️ Single Episode Visualizer", "📊 Batch Strategy Comparison", "📜 Mahabharata Historical Context"])

# ----------------- TAB 1: SINGLE EPISODE -----------------
with tab1:
    col_btn1, col_btn2 = st.columns([1, 3])
    with col_btn1:
        run_single = st.button("▶️ Run Single Episode", use_container_width=True, type="primary")

    if run_single:
        cfg = Config(
            seed=int(seed),
            difficulty=difficulty,
            comm_range=float(comm_range),
            max_steps=int(max_steps),
        )

        with st.spinner("Executing simulation episode..."):
            result = run_episode(cfg, selected_strategy, record_history=True)

        # Display outcome badges
        m1, m2, m3, m4, m5 = st.columns(5)
        outcome_color = {
            "success": "🟢 SUCCESS (Breached & Exited)",
            "wipeout": "🔴 WIPEOUT (All Attackers Fallen)",
            "timeout": "🟡 TIMEOUT (Stalled / Trapped)",
        }.get(result["outcome"], result["outcome"])

        m1.metric("Mission Outcome", outcome_color)
        m2.metric("Elapsed Steps", result["steps"])
        m3.metric("Rings Breached", f"{result['rings_breached']} / 7")
        m4.metric("Surviving Attackers", result["survivors"])
        m5.metric("Messages Exchanged", result["messages_sent"])

        history = result.get("history", [])
        if history:
            st.markdown("### 🗺️ Tactical Grid Playback")
            step_slider = st.slider("Scrub Simulation Step", min_value=1, max_value=len(history), value=len(history))
            snap = history[step_slider - 1]
            env_snap: ChakravyuhaEnvironment = snap["env"]

            # Reconstruct agents for plotting
            class DummyAgent:
                def __init__(self, d):
                    self.agent_id = d["id"]
                    self.role = d.get("role", "follower")
                    self.pos = d["pos"]
                    self.health = d["health"]
                    self.is_alive = d["alive"]
                    self.has_reached_center = d.get("reached_center", False)
                    self.has_exited = d.get("exited", False)
                    self.strength_color = d.get("color", "#E53E3E")

            plot_attackers = [DummyAgent(a) for a in snap["attackers"]]
            plot_defenders = [DummyAgent(d) for d in snap["defenders"]]

            fig = env_snap.render_matplotlib(plot_attackers, plot_defenders, step_num=snap["step"])
            
            c_plot, c_roster = st.columns([3, 2])
            with c_plot:
                st.pyplot(fig, use_container_width=True)
                plt.close(fig)

            with c_roster:
                st.markdown("#### 🛡️ Pandava Agent Status")
                att_df = pd.DataFrame([
                    {
                        "Agent": a.agent_id,
                        "Role": a.role.title(),
                        "Position": str(a.pos),
                        "Health": f"{max(0, a.health)} HP",
                        "Status": "Exited" if a.has_exited else ("Alive" if a.is_alive else "Fallen"),
                    }
                    for a in plot_attackers
                ])
                st.dataframe(att_df, use_container_width=True, hide_index=True)

                st.markdown("#### 🔒 Formation State")
                st.info(f"**Jayadratha Outer Gate Lockdown:** {'ACTIVE (Locked)' if snap['jayadratha_active'] else 'INACTIVE'}")
                alive_defs = sum(1 for d in plot_defenders if d.is_alive)
                st.write(f"**Active Kaurava Defenders:** {alive_defs} / {len(plot_defenders)}")

# ----------------- TAB 2: BATCH COMPARISON -----------------
with tab2:
    st.markdown("### 🔬 Multi-Strategy Monte Carlo Benchmark")
    col_b1, col_b2 = st.columns([2, 2])
    with col_b1:
        batch_episodes = st.number_input("Episodes Per Strategy", min_value=10, max_value=300, value=50, step=10)
    with col_b2:
        run_batch_btn = st.button("🚀 Run Batch Comparison", use_container_width=True, type="primary")

    if run_batch_btn:
        progress_bar = st.progress(0.0)
        status_text = st.empty()
        
        strategies = ["lone_entry", "blind_follow", "shared_map", "split_exit"]
        batch_records = []
        total_runs = len(strategies) * batch_episodes
        run_count = 0

        for strat in strategies:
            for ep in range(batch_episodes):
                b_seed = 50000 + ep
                b_cfg = Config(
                    seed=b_seed,
                    difficulty=difficulty,
                    comm_range=float(comm_range),
                    max_steps=int(max_steps),
                )
                res = run_episode(b_cfg, strat, record_history=False)
                batch_records.append({
                    "strategy": strat,
                    "success": 1 if res["outcome"] == "success" else 0,
                    "wipeout": 1 if res["outcome"] == "wipeout" else 0,
                    "timeout": 1 if res["outcome"] == "timeout" else 0,
                    "steps": res["steps"],
                    "survivors": res["survivors"],
                    "rings_breached": res["rings_breached"],
                    "messages_sent": res["messages_sent"],
                })
                run_count += 1
                progress_bar.progress(run_count / total_runs)
                status_text.text(f"Evaluating {strat} ({run_count}/{total_runs})...")

        b_df = pd.DataFrame(batch_records)
        progress_bar.empty()
        status_text.empty()

        st.markdown("#### 📋 Strategy Benchmark Summary")
        summary_table = b_df.groupby("strategy").agg(
            Success_Rate=("success", lambda x: f"{x.mean() * 100:.1f}%"),
            Wipeout_Rate=("wipeout", lambda x: f"{x.mean() * 100:.1f}%"),
            Avg_Rings_Breached=("rings_breached", "mean"),
            Avg_Survivors=("survivors", "mean"),
            Avg_Steps=("steps", "mean"),
            Avg_Messages=("messages_sent", "mean"),
        ).reset_index()

        summary_table["strategy"] = summary_table["strategy"].map(strategy_options)
        st.dataframe(summary_table, use_container_width=True, hide_index=True)

        # Visualization Chart
        st.markdown("#### 📊 Comparative Success & Penetration Metrics")
        chart_col1, chart_col2 = st.columns(2)

        strat_labels = [strategy_options[s] for s in strategies]
        strat_success = [b_df[b_df["strategy"] == s]["success"].mean() * 100 for s in strategies]
        strat_rings = [b_df[b_df["strategy"] == s]["rings_breached"].mean() for s in strategies]

        with chart_col1:
            fig1, ax1 = plt.subplots(figsize=(6, 4))
            ax1.barh(strat_labels, strat_success, color=["#E53E3E", "#DD6B20", "#3182CE", "#38A169"], edgecolor="black")
            ax1.set_xlabel("Success Rate (%)", fontweight="bold")
            ax1.set_title("Mission Success Rate", fontweight="bold")
            ax1.set_xlim(0, 100)
            plt.tight_layout()
            st.pyplot(fig1)
            plt.close(fig1)

        with chart_col2:
            fig2, ax2 = plt.subplots(figsize=(6, 4))
            ax2.barh(strat_labels, strat_rings, color=["#E53E3E", "#DD6B20", "#3182CE", "#38A169"], edgecolor="black")
            ax2.set_xlabel("Mean Rings Breached (Max 7)", fontweight="bold")
            ax2.set_title("Average Penetration Depth", fontweight="bold")
            ax2.set_xlim(0, 7.5)
            plt.tight_layout()
            st.pyplot(fig2)
            plt.close(fig2)

# ----------------- TAB 3: MAHABHARATA EXPLAINER -----------------
with tab3:
    st.markdown("""
    <div class="explainer-box">
    <h3>📜 The Mahabharata Connection: Drona Parva (Day 13)</h3>
    <p>
    On the 13th day of the Kurukshetra war, Guru Dronacharya arranged the Kaurava army into the formidable 
    <b>Chakravyuha</b> (a multi-tiered rotating disc formation) to capture Yudhishthira. 
    Only Arjuna and Krishna knew the complete technique to both enter and break out of the formation.
    </p>
    
    <h4>1. Knowledge Asymmetry (Abhimanyu's Secret)</h4>
    <p>
    Arjuna's 16-year-old son, <b>Abhimanyu</b>, had overheard Arjuna narrating the entry secret to Subhadra while in her womb, 
    but fell asleep before learning how to exit. In computational multi-agent terms, Abhimanyu possesses 
    <b>complete a priori map knowledge of inward entry gates</b> ($G_7 \to G_1$), but <b>zero prior knowledge of exit corridors</b> ($E_1 \to E_7$).
    </p>
    
    <h4>2. Jayadratha's Gate Lockdown</h4>
    <p>
    King Jayadratha, armed with Lord Shiva's boon granting him the power to hold off all Pandavas except Arjuna for a single day, 
    sealed the 7th outer entrance immediately after Abhimanyu breached it. In the simulation, this cuts off 
    followers from entering the labyrinth behind Abhimanyu.
    </p>
    
    <h4>3. Inward Escalating Defense (Maharathis at the Core)</h4>
    <p>
    The outer rings are guarded by general infantry, while the innermost layers house the paramount Kaurava Maharathis 
    (Drona, Karna, Ashwatthama, Duryodhana, Dushasana, Shakuni). Defeating or bypassing inner guards requires 
    concentrated combat power and coordination.
    </p>
    
    <h4>4. Tactical Strategy Comparison</h4>
    <ul>
        <li><b>Lone Entry (The Historical Tragedy):</b> Abhimanyu penetrates deeply to Ring 1/0 alone, but without an exit map or reinforcement scouting, he is overwhelmed and wiped out.</li>
        <li><b>Blind Follow:</b> Followers attempt to trail Abhimanyu's trajectory but get trapped at Gate 7 by Jayadratha due to lack of coordination.</li>
        <li><b>Shared Map:</b> Pandavas maintain communication channels, broadcasting real-time gate coordinates and warning signals to coordinate multi-angle penetration.</li>
        <li><b>Split Exit (Optimal Multi-Agent Protocol):</b> A designated scouting detachment searches intermediate rings for exit pathways while the assault team breaches the core, relaying extraction coordinates before the core forces are exhausted.</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
