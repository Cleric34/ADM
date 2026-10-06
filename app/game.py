"""
app/game.py - Playable Chakravyuha Interactive Turn-Based Game.
Mahabharata Drona Parva: Guide Abhimanyu into the 7 concentric rings and escape!
"""

import streamlit as st
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from sim.environment import Config, ChakravyuhaEnvironment
from sim.agents import Attacker
from sim.strategies import get_strategy
from sim.engine import initialize_defenders, step_defenders, resolve_combat

st.set_page_config(page_title="Chakravyuha: The Game", page_icon="🏹", layout="wide")

# Custom Dark Theme & Board Styling
st.markdown("""
<style>
.stApp { background-color: #0b0f19; color: #e2e8f0; }
.board-grid {
    display: grid;
    grid-template-columns: repeat(31, 14px);
    grid-template-rows: repeat(31, 14px);
    gap: 1px;
    background-color: #1a202c;
    padding: 6px;
    border-radius: 8px;
    border: 2px solid #3182ce;
    width: fit-content;
    margin: 0 auto;
}
.cell { width: 14px; height: 14px; border-radius: 2px; font-size: 9px; text-align: center; line-height: 14px; font-weight: bold; }
.wall { background-color: #1e3a8a; }
.path { background-color: #0f172a; }
.center-core { background-color: #d97706; box-shadow: 0 0 8px #f59e0b; }
.entry-gate { background-color: #fbbf24; }
.exit-gate-known { background-color: #06b6d4; box-shadow: 0 0 5px #22d3ee; }
.exit-gate-hidden { background-color: #1e3a8a; }
.abhimanyu { background-color: #facc15; color: #000; border: 1px solid #fff; box-shadow: 0 0 8px #fde047; font-weight: 900; }
.follower { background-color: #22c55e; color: #000; border-radius: 50%; font-size: 8px; }
.defender { background-color: #ef4444; color: #fff; }
.defender-inner { background-color: #991b1b; color: #fff; }
.jayadratha { background-color: #a855f7; box-shadow: 0 0 6px #c084fc; color: #fff; }
.log-box { background: #1e293b; border-left: 4px solid #3b82f6; padding: 10px; border-radius: 4px; height: 140px; overflow-y: auto; font-family: monospace; font-size: 12px; }
</style>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR CONTROLS -----------------
with st.sidebar:
    st.title("🏹 Battle Configuration")
    st.caption("Mahabharata — Drona Parva (Day 13)")
    diff = st.selectbox("Defense Difficulty", ["low", "medium", "high"], index=0)
    strat_choice = st.selectbox("Follower Strategy", ["shared_map", "split_exit", "blind_follow", "none"], index=0)
    seed = st.number_input("Random Seed", value=42, step=1)
    if st.button("🔄 Reset / Start New Battle", use_container_width=True, type="primary"):
        st.session_state.pop("game", None)

# ----------------- GAME STATE INITIALIZATION -----------------
def init_game(difficulty: str, strategy: str, random_seed: int):
    cfg = Config(seed=int(random_seed), difficulty=difficulty, max_steps=400)
    env = ChakravyuhaEnvironment(cfg)
    defenders = initialize_defenders(env, cfg)
    
    if strategy != "none":
        strat_obj = get_strategy(strategy)
        attackers = strat_obj.setup_attackers(env, cfg)
    else:
        strat_obj = None
        g7 = env.entry_gates[7]
        abhimanyu = Attacker(
            agent_id="abhimanyu", role="infiltrator",
            pos=(min(cfg.grid_size - 1, g7[0] + 2), g7[1]),
            health=cfg.abhimanyu_health, attack_power=cfg.abhimanyu_attack,
            vision_radius=cfg.vision_radius, comm_range=cfg.comm_range,
            known_entry_gates=dict(env.entry_gates),
        )
        attackers = [abhimanyu]

    abhimanyu = attackers[0]
    abhimanyu.scout_vision(env)

    return {
        "config": cfg, "env": env, "defenders": defenders,
        "attackers": attackers, "strategy": strat_obj, "strat_name": strategy,
        "step": 0, "logs": ["🏹 Day 13 begins: Abhimanyu approaches the Chakravyuha entrance!"],
        "game_over": False, "won": False,
    }

if "game" not in st.session_state:
    st.session_state.game = init_game(diff, strat_choice, seed)

game = st.session_state.game
env: ChakravyuhaEnvironment = game["env"]
attackers = game["attackers"]
defenders = game["defenders"]
abhimanyu: Attacker = attackers[0]

# ----------------- STEP LOGIC -----------------
def execute_player_turn(dx: int, dy: int):
    if game["game_over"] or not abhimanyu.is_alive:
        return
    
    game["step"] += 1
    cx, cy = abhimanyu.pos
    nx, ny = cx + dx, cy + dy
    
    # 1. Validate player move against walls and boundaries
    if 0 <= nx < env.grid_size and 0 <= ny < env.grid_size and not env.is_wall((nx, ny)):
        abhimanyu.pos = (nx, ny)
        current_ring = env.get_ring_of_point((nx, ny))
        if current_ring <= game["config"].num_rings:
            env.trigger_first_breach((nx, ny))
            if env.jayadratha_active and "Jayadratha locks the gate!" not in game["logs"][-1]:
                game["logs"].append("⚔️ Jayadratha blocks the rear gate! Followers are locked outside!")
        if abhimanyu.pos == env.center:
            abhimanyu.has_reached_center = True
            game["logs"].append("🌟 Abhimanyu breaches the core of the Chakravyuha!")
        if abhimanyu.has_reached_center and (abhimanyu.pos == env.exit_gates[7] or current_ring > game["config"].num_rings):
            abhimanyu.has_exited = True
            game["won"] = True
            game["game_over"] = True
            game["logs"].append("🏆 VICTORY: Abhimanyu successfully breached the center and escaped!")
    else:
        game["logs"].append(f"⛔ Move blocked! Wall or closed perimeter at ({nx}, {ny}).")

    # 2. Step AI followers (if strategy enabled)
    if game["strategy"] and len(attackers) > 1:
        saved_pos = abhimanyu.pos
        game["strategy"].coordinate_and_step(attackers, defenders, env, game["config"])
        abhimanyu.pos = saved_pos  # Preserve player manual position

    # 3. Scout vision update
    abhimanyu.scout_vision(env)

    # 4. Defenders move & attack
    step_defenders(defenders, attackers, env)
    
    # Combat resolution with telemetry log
    pre_ab_hp = abhimanyu.health
    resolve_combat(attackers, defenders)
    dmg_taken = pre_ab_hp - abhimanyu.health
    if dmg_taken > 0:
        game["logs"].append(f"💥 Combat: Abhimanyu takes {dmg_taken} damage! (HP: {max(0, abhimanyu.health)})")

    # 5. Check terminal conditions
    if not abhimanyu.is_alive:
        game["game_over"] = True
        game["won"] = False
        game["logs"].append("💀 DEFEAT: Abhimanyu has fallen in battle defending the Dharma.")
    elif game["step"] >= game["config"].max_steps and not game["won"]:
        game["game_over"] = True
        game["won"] = False
        game["logs"].append("⏳ TIMEOUT: Night falls on Kurukshetra. Max steps reached.")

# ----------------- UI LAYOUT -----------------
col_board, col_panel = st.columns([13, 11])

with col_panel:
    st.subheader("📜 Drona Parva: The Chakravyuha")
    st.caption("Guide young hero Abhimanyu through Guru Drona's labyrinthine disc formation.")
    
    # Hero Stats & Meters
    hp_pct = max(0.0, min(1.0, abhimanyu.health / game["config"].abhimanyu_health))
    st.write(f"**Abhimanyu Health:** {max(0, abhimanyu.health)} / {game['config'].abhimanyu_health} HP")
    st.progress(hp_pct)
    
    m1, m2, m3 = st.columns(3)
    curr_ring = env.get_ring_of_point(abhimanyu.pos)
    m1.metric("Current Layer", f"Ring {curr_ring}" if curr_ring <= 7 else "Outside")
    m2.metric("Turn", f"{game['step']} / {game['config'].max_steps}")
    alive_fol = sum(1 for a in attackers[1:] if a.is_alive)
    m3.metric("Followers Alive", f"{alive_fol} / {len(attackers)-1}")

    # Directional Controls
    st.markdown("#### 🎮 Directional Controls")
    c_u1, c_u2, c_u3 = st.columns([1, 1, 1])
    with c_u2:
        if st.button("⬆️ Up", use_container_width=True, disabled=game["game_over"]):
            execute_player_turn(-1, 0)
            st.rerun()
    c_l, c_d, c_r = st.columns([1, 1, 1])
    with c_l:
        if st.button("⬅️ Left", use_container_width=True, disabled=game["game_over"]):
            execute_player_turn(0, -1)
            st.rerun()
    with c_d:
        if st.button("⬇️ Down", use_container_width=True, disabled=game["game_over"]):
            execute_player_turn(1, 0)
            st.rerun()
    with c_r:
        if st.button("➡️ Right", use_container_width=True, disabled=game["game_over"]):
            execute_player_turn(0, 1)
            st.rerun()

    # Story & Battle Log
    st.markdown("#### 📜 Battle Chronicle")
    log_text = "<br>".join(reversed(game["logs"][-6:]))
    st.markdown(f"<div class='log-box'>{log_text}</div>", unsafe_allow_html=True)
    
    # Win / Game Over Screen
    if game["game_over"]:
        if game["won"]:
            st.success(f"🎉 **VICTORY!** Escaped in {game['step']} turns with {abhimanyu.health} HP left and {alive_fol} surviving followers!")
        else:
            st.error(f"☠️ **GAME OVER!** Abhimanyu was overwhelmed at Ring {curr_ring} after {game['step']} turns.")
        if st.button("🔄 Play Again", use_container_width=True, type="primary"):
            st.session_state.game = init_game(diff, strat_choice, seed + 1)
            st.rerun()

with col_board:
    # Build fast 31x31 HTML/CSS Grid representation
    alive_attackers = {a.pos: a for a in attackers if a.is_alive}
    alive_defenders = {d.pos: d for d in defenders if d.is_alive}
    known_exits = set(abhimanyu.known_exit_gates.values())

    grid_html = ['<div class="board-grid">']
    for r in range(env.grid_size):
        for c in range(env.grid_size):
            pt = (r, c)
            cell_class = "path"
            cell_char = ""
            
            # 1. Base Layer
            if pt == env.center:
                cell_class = "center-core"
                cell_char = "★"
            elif env.jayadratha_active and pt == env.jayadratha_pos:
                cell_class = "jayadratha"
                cell_char = "J"
            elif any(pt == env.entry_gates[k] for k in env.entry_gates):
                cell_class = "entry-gate"
                cell_char = "G"
            elif pt in known_exits:
                cell_class = "exit-gate-known"
                cell_char = "E"
            elif env.is_wall(pt):
                cell_class = "wall"
            
            # 2. Agent Entities Overlay
            if pt == abhimanyu.pos:
                cell_class = "abhimanyu"
                cell_char = "A"
            elif pt in alive_attackers:
                cell_class = "follower"
                cell_char = "f"
            elif pt in alive_defenders:
                d = alive_defenders[pt]
                cell_class = "defender-inner" if d.layer <= 3 else "defender"
                cell_char = str(d.layer)

            grid_html.append(f'<div class="cell {cell_class}">{cell_char}</div>')
    grid_html.append('</div>')
    
    st.markdown("".join(grid_html), unsafe_allow_html=True)
    st.caption("🟡 **A**: Abhimanyu | 🟢 **f**: Follower | 🔴 **1-7**: Defender Layer | 🟣 **J**: Jayadratha | 🟡 **G**: Entry Gate | 🔵 **E**: Discovered Exit Gate | 🟠 **★**: Core")
