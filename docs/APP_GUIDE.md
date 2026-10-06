# Beginner's Guide to the Chakravyuha Simulator (`docs/APP_GUIDE.md`)

Welcome to the **Chakravyuha Multi-Agent Simulation Web App**! This guide is written for first-year students and newcomers who have never seen the dashboard before. It walks through the application top-to-bottom, explaining every button, slider, metric, table column, color, and symbol exactly as named in the code, along with its direct connection to the *Mahabharata (Drona Parva)* episode.

---

## 🏛️ 1. Top Header & Quick Legend

### `🛡️ Chakravyuha Multi-Agent Simulation`
- **What it is on screen:** The primary title header.
- **What it means:** Identifies the software as an agent-based model simulating tactical coordination under incomplete information.
- **Mahabharata Connection:** On Day 13 of the Kurukshetra war, Guru Dronacharya deployed the **Chakravyuha**—a 7-layered rotating wheel/disc military labyrinth designed to trap the Pandavas.

### `📖 How to read this screen` (Collapsible Expander)
- **What it is on screen:** An expandable reference card at the top of the page.
- **What it means:** Provides a quick visual key for all colors, symbols, entity roles, and outcome badges before launching a simulation.

---

## ⚙️ 2. Sidebar Controls (`⚙️ Simulation Controls`)

Located on the left-hand panel, these widgets configure the environment and agent parameters before running a scenario.

### 1. `Attacker Strategy` (`selected_strategy`)
- **What it is on screen:** A dropdown selector offering 5 tactical strategies:
  1. **`0. Oracle (Full Map Knowledge Baseline)` (`oracle`)**: A single infiltrator with complete *a priori* knowledge of all entry gates ($G_7 \to G_1$) and exit gates ($E_1 \to E_7$). Serves as a theoretical upper-bound benchmark (Mahabharata link: represents Krishna or Arjuna, who knew the complete secret to enter and exit).
  2. **`1. Lone Entry (Abhimanyu Alone)` (`lone_entry`)**: Abhimanyu enters alone with knowledge of entry gates only and zero exit map (Mahabharata link: the historical tragedy where Abhimanyu breached the core alone without extraction support).
  3. **`2. Blind Follow (Followers Trail Without Comm)` (`blind_follow`)**: Pandava followers trail Abhimanyu's position visually without radio/messaging channels (Mahabharata link: Yudhishthira, Bhima, Nakula, and Sahadeva attempting to follow Abhimanyu into the breach).
  4. **`3. Shared Map (Dynamic Gate Messaging)` (`shared_map`)**: Agents broadcast discovered entry and exit gates over peer-to-peer message channels whenever within range (Mahabharata link: coordinated battlefield signalling among Pandava divisions).
  5. **`4. Split Exit (Scout Perimeter + Inward Breach)` (`split_exit`)**: Dedicated scouts patrol outer/intermediate rings to locate exit corridors while assault warriors drive toward the center (Mahabharata link: a planned military breakout doctrine).

### 2. `Defense Difficulty` (`difficulty`)
- **What it is on screen:** A dropdown selector with options `low`, `medium`, and `high`.
- **What it means:** Controls the number of Kaurava defenders spawned per ring and their inward combat scaling.
- **Mahabharata Connection:** Represents the concentration and martial resistance of Kaurava divisions guarding each tier of the formation.

### 3. `Communication Range (Grid Units)` (`comm_range`)
- **What it is on screen:** A slider ranging from `2.0` to `20.0` grid units (default `6.0`).
- **What it means:** The maximum Euclidean distance across which Pandava agents can successfully transmit discovered gate coordinates to teammates.
- **Mahabharata Connection:** Represents the shouting distance, conch-shell call, or visual signalling limit amidst the noise, dust, and chaos of the Kurukshetra battlefield.

### 4. `Random Seed` (`seed`)
- **What it is on screen:** A numeric input field (default `42`).
- **What it means:** Seeds Python's pseudo-random number generator to place gates and defender patrol points deterministically for exact repeatability.
- **Mahabharata Connection:** Represents the specific physical layout and gate orientations chosen by Guru Drona for that day's battle.

### 5. `Max Episode Steps` (`max_steps`)
- **What it is on screen:** A slider ranging from `30` to `250` steps (default `120`).
- **What it means:** The maximum simulation turns allowed before an episode terminates due to time exhaustion.
- **Mahabharata Connection:** Represents the timeline of Day 13—the battle must be resolved before sunset, after which the day's war code mandates cessation of hostilities.

---

## ⚔️ 3. Tab 1: Single Episode Visualizer

### Control Button: `▶️ Run Single Episode`
- **What it is on screen:** Primary blue action button.
- **What it means:** Instantiates the environment, runs one complete simulation episode step-by-step, records full trajectory history, and displays results.

### Metrics Row (Top Cards)
1. **`Mission Outcome`**:
   - `🟢 SUCCESS (Breached & Exited)`: At least one attacker penetrated Ring 1 to the center core and successfully navigated outside the 7th ring.
   - `🔴 WIPEOUT (All Attackers Fallen)`: All Pandava attackers were defeated in combat (health reduced to 0).
   - `🟡 TIMEOUT (Stalled / Trapped)`: Maximum episode steps were reached. In results analysis, episodes where the center was reached but exit was blocked are sub-categorized as `trapped_inside`.
2. **`Elapsed Steps`**: Total simulation turns elapsed during the mission.
3. **`Rings Breached`**: Deepest concentric wall penetrated (displayed as `X / 7`).
4. **`Surviving Attackers`**: Number of Pandava agents alive at episode termination.
5. **`Messages Exchanged`**: Total peer-to-peer message transmissions sent during the episode.

### Tactical Grid Playback & Visual Map
- **`Scrub Simulation Step` Slider:** Allows stepping forward and backward turn-by-turn through the battle history.
- **Map Elements, Symbols & Colors (rendered by Matplotlib):**
  - **Background (`#121824`)**: Dark navy blue representing the Kurukshetra battlefield terrain.
  - **Ring Walls (`marker="s"`, Square Blocks, `#4A5568` to `#172554`)**: The 7 concentric square barrier walls of the Chakravyuha (Ring 7 outer to Ring 1 inner).
  - **Entry Gates (`marker="o"`, Green Circle `#48BB78`)**: Open inward passageways known to Abhimanyu.
  - **Exit Gates (`marker="v"`, Teal Downward Triangle `#38B2AC`)**: Hidden breakout passageways leading to outer rings.
  - **Center Core (`marker="*"`, Golden Star `#ECC94B`)**: The innermost sanctum (Ring 0 / Center) where the command tent of the formation lies.
  - **Jayadratha Lockdown (`marker="X"`, Red Cross `#E53E3E`)**: Appears at Ring 7 Entry Gate once Abhimanyu breaches the formation. Marks the entrance as permanently impassable. (Mahabharata link: King Jayadratha using Shiva's boon to cut off Pandava reinforcements).
  - **Kaurava Defenders (`marker="^"`, Upward Triangles, `#FEB2B2` to `#9B2C2C`)**: Enemy defenders patrolling their assigned rings. Darker red indicates higher health and attack power in the inner rings (Mahabharata link: Drona, Karna, Ashwatthama, Duryodhana, Dushasana at the core).
  - **Abhimanyu (`marker="o"`, Large Blue Circle `#3182CE`)**: The primary infiltrator agent.
  - **Pandava Scouts (`marker="D"`, Orange Diamond `#ED8936`)**: Dedicated reconnaissance units searching for exit gates.
  - **Pandava Followers (`marker="o"`, Green Circle `#38A169`)**: Supporting infantry trailing the assault.

### `🛡️ Pandava Agent Status` Table
- **`Agent`**: The unique identifier of the warrior (`abhimanyu`, `follower_1`, `scout_1`, `warrior_1`).
- **`Role`**: Tactical classification (`Infiltrator`, `Follower`, `Scout`).
- **`Position`**: Current $(x, y)$ grid coordinates on the $31 \times 31$ board.
- **`Health`**: Remaining health points (`HP`) out of initial maximum.
- **`Status`**: Operational state (`Alive`, `Exited`, or `Fallen`).

### `🔒 Formation State` Info Box
- **`Jayadratha Outer Gate Lockdown`**: Reports `ACTIVE (Locked)` when the outer entrance has been sealed, or `INACTIVE` prior to the initial breach.
- **`Active Kaurava Defenders`**: Displays the count of surviving enemy guards (`Alive / Total`).

---

## 📊 4. Tab 2: Batch Strategy Comparison

Allows running automated Monte Carlo benchmark experiments directly in the browser to compare strategy performance.

### Controls & Inputs
- **`Episodes Per Strategy` (`batch_episodes`)**: Number of random seeds to evaluate per strategy (10 to 300, default 50).
- **`🚀 Run Batch Comparison`**: Launches the parallel multi-episode benchmark with a live progress bar.

### `📋 Strategy Benchmark Summary` Table
- **`strategy`**: Name of the tactical coordination strategy.
- **`Success_Rate`**: Percentage of episodes resulting in successful breach and exit.
- **`Wipeout_Rate`**: Percentage of episodes where all attacking units were defeated.
- **`Avg_Rings_Breached`**: Mean penetration depth achieved (scale 0 to 7).
- **`Avg_Survivors`**: Average count of surviving Pandava agents at episode end.
- **`Avg_Steps`**: Mean number of simulation steps taken per run.
- **`Avg_Messages`**: Mean peer-to-peer message transmissions sent per episode.

### Comparative Bar Charts
- **`Mission Success Rate` (Horizontal Bar Chart)**: Compares the percentage of victorious breakouts across strategies. Colors match strategy identities (Red: `lone_entry`, Orange: `blind_follow`, Blue: `shared_map`, Green: `split_exit`).
- **`Average Penetration Depth` (Horizontal Bar Chart)**: Compares mean rings breached (0 to 7) across strategies.
- **Error Bars (95% Confidence Intervals in `logs/figures/`)**: In the static experimental figures generated by `run_experiments.py`, error bars represent the **95% Wilson/Wald confidence interval** ($\pm 1.96 \cdot \text{SE}$), demonstrating statistical significance across 500 seeds per condition.

---

## 📜 5. Tab 3: Mahabharata Historical Context

Provides an educational narrative linking the multi-agent simulation mechanics to the epic text:
- **Drona Parva (Day 13):** Why the Chakravyuha was constructed and why Arjuna was diverted south by the Samsaptakas.
- **Knowledge Asymmetry:** Why Abhimanyu knew entry paths ($G_7 \to G_1$) but lacked exit knowledge ($E_1 \to E_7$).
- **Jayadratha's Boon:** The theological and tactical reason for the rear-gate lockout.
- **Core Defense Scaling:** Why inner rings feature formidable Maharathi defenders.

---

## 🎬 6. Five-Line "How to Run a Good Demo" Script

1. **Set the Stage:** Select `Attacker Strategy: 1. Lone Entry`, `Difficulty: low`, `Seed: 42`, and click `▶️ Run Single Episode` to show Abhimanyu breaching the core but falling or getting trapped due to lack of an exit map.
2. **Demonstrate the Jayadratha Lock:** Switch to `2. Blind Follow` and scrub the step slider to show Abhimanyu entering while Jayadratha's red `X` locks all 4 green followers outside.
3. **Show Dynamic Communication:** Switch to `3. Shared Map` and run the episode to demonstrate how messaging coordinates multi-agent gate sharing and pushes the message counter over 4,000.
4. **Show the Winning Protocol:** Switch to `4. Split Exit` to show orange diamond scouts discovering cyan exit triangles while blue assault units breach the center and escape together.
5. **Run the Monte Carlo Benchmark:** Switch to Tab 2 (`📊 Batch Strategy Comparison`), set 50 episodes, click `🚀 Run Batch Comparison`, and present the comparative bar chart showing `split_exit` outperforming `lone_entry`.
