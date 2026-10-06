"""
sim/environment.py - Chakravyuha Spatial and Physical Environment.

Models the 7 concentric rings of the Chakravyuha formation from Drona Parva as a
grid-based tactical coordination environment with dynamic entry gates, exit gates,
defenders with inward-scaling power, and Jayadratha's gate-blocking mechanism.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Set, Any
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches


@dataclass
class Config:
    """Configuration parameters for the Chakravyuha simulation."""
    seed: int = 42
    grid_size: int = 31  # Must be odd to have a clean center (e.g., 31x31 -> center (15,15))
    num_rings: int = 7
    difficulty: str = "medium"  # "low", "medium", "high"
    comm_range: float = 6.0     # Low: 4.0, High: 15.0
    vision_radius: float = 4.0
    num_followers: int = 4
    max_steps: int = 150
    
    # Base combat stats
    abhimanyu_health: int = 120
    abhimanyu_attack: int = 35
    follower_health: int = 70
    follower_attack: int = 20
    
    # Defenders per ring mapping by difficulty
    # Ring 1 is innermost, Ring 7 is outermost
    defenders_per_ring: Dict[str, Dict[int, int]] = field(default_factory=lambda: {
        "low":    {1: 2, 2: 2, 3: 3, 4: 3, 5: 4, 6: 4, 7: 5},
        "medium": {1: 3, 2: 4, 3: 5, 4: 5, 5: 6, 6: 7, 7: 8},
        "high":   {1: 5, 2: 6, 3: 7, 4: 8, 5: 9, 6: 10, 7: 12},
    })


class ChakravyuhaEnvironment:
    """
    7-Ring Concentric Grid Environment representing the Chakravyuha formation.
    
    Grid Coordinate Convention:
        (x, y) where (0,0) is top-left, (center, center) is the innermost core (Ring 0).
        Rings are concentric Chebyshev distance shells R_1 = 2, R_2 = 4, ..., R_7 = 14.
    """

    def __init__(self, config: Config) -> None:
        self.config = config
        self.rng = np.random.RandomState(config.seed)
        self.grid_size = config.grid_size
        self.center = (self.grid_size // 2, self.grid_size // 2)
        
        # Radii of concentric rings: Ring 1 (inner) to Ring 7 (outer)
        # Ring 1 radius: 2, Ring 2: 4, ..., Ring 7: 14
        self.ring_radii = {r: r * 2 for r in range(1, config.num_rings + 1)}
        
        # Ring cells and gates
        self.ring_cells: Dict[int, Set[Tuple[int, int]]] = {}
        self.entry_gates: Dict[int, Tuple[int, int]] = {}
        self.exit_gates: Dict[int, Tuple[int, int]] = {}
        
        # Jayadratha state: triggers after the first Pandava enters Ring 7
        self.jayadratha_active = False
        self.jayadratha_pos: Optional[Tuple[int, int]] = None
        self.first_breach_occurred = False
        
        # Grid setup
        self._build_rings_and_gates()

    def _build_rings_and_gates(self) -> None:
        """Construct the 7 concentric ring walls and place entry and exit gates."""
        cx, cy = self.center
        
        for r in range(1, self.config.num_rings + 1):
            rad = self.ring_radii[r]
            cells = set()
            for x in range(cx - rad, cx + rad + 1):
                for y in range(cy - rad, cy + rad + 1):
                    # Chebyshev perimeter for concentric square ring
                    if max(abs(x - cx), abs(y - cy)) == rad:
                        if 0 <= x < self.grid_size and 0 <= y < self.grid_size:
                            cells.add((x, y))
            self.ring_cells[r] = cells
            
            # Select entry gate on each ring (staggered angular positions to represent spiral labyrinth)
            # Pick a deterministic random gate cell along each ring using seed
            ring_cell_list = sorted(list(cells))
            entry_idx = self.rng.randint(0, len(ring_cell_list))
            entry_gate = ring_cell_list[entry_idx]
            self.entry_gates[r] = entry_gate
            
            # Exit gate is placed at an opposing or scout-required sector on the ring
            # (different from entry gate, representing the hidden/changing exit path)
            exit_idx = (entry_idx + len(ring_cell_list) // 2) % len(ring_cell_list)
            self.exit_gates[r] = ring_cell_list[exit_idx]
        
        # Jayadratha will block the outermost gate (Ring 7 entry gate)
        self.jayadratha_pos = self.entry_gates[self.config.num_rings]

    def get_ring_of_point(self, pos: Tuple[int, int]) -> int:
        """
        Returns the ring index (0 to 7, or 8 for outside) for a position.
        0 = Center core.
        1..7 = Concentric layers.
        8 = Outside the formation.
        """
        cx, cy = self.center
        dist = max(abs(pos[0] - cx), abs(pos[1] - cy))
        if dist == 0:
            return 0
        for r in range(1, self.config.num_rings + 1):
            if dist <= self.ring_radii[r]:
                return r
        return self.config.num_rings + 1  # Outside formation

    def is_wall(self, pos: Tuple[int, int]) -> bool:
        """
        Checks if a cell is an impassable formation wall.
        Ring perimeter cells are walls UNLESS they are an open entry/exit gate.
        If Jayadratha is active, the main outer entry gate is blocked by Jayadratha!
        """
        x, y = pos
        if not (0 <= x < self.grid_size and 0 <= y < self.grid_size):
            return True  # Out of bounds is impassable
            
        # Jayadratha blocks the outer gate cell
        if self.jayadratha_active and pos == self.jayadratha_pos:
            return True
            
        for r in range(1, self.config.num_rings + 1):
            if pos in self.ring_cells[r]:
                # Gates are passable gaps in the wall
                if pos == self.entry_gates[r] or pos == self.exit_gates[r]:
                    return False
                return True
        return False

    def trigger_first_breach(self, agent_pos: Tuple[int, int]) -> None:
        """
        When an attacker enters Ring 7 (crosses outer gate), Jayadratha immediately
        locks down the outer entrance, preventing followers behind from entering.
        """
        if not self.first_breach_occurred:
            agent_ring = self.get_ring_of_point(agent_pos)
            if agent_ring <= self.config.num_rings:
                self.first_breach_occurred = True
                self.jayadratha_active = True

    def render_ascii(self, attackers: List[Any], defenders: List[Any]) -> str:
        """Renders an ASCII text grid representation of the simulation state."""
        grid = [["." for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        
        # Draw ring walls
        for r in range(1, self.config.num_rings + 1):
            for x, y in self.ring_cells[r]:
                grid[x][y] = "▓"
            gx, gy = self.entry_gates[r]
            grid[gx][gy] = " "
            ex, ey = self.exit_gates[r]
            grid[ex][ey] = "E"
            
        # Center
        cx, cy = self.center
        grid[cx][cy] = "★"
        
        # Jayadratha
        if self.jayadratha_active and self.jayadratha_pos:
            jx, jy = self.jayadratha_pos
            grid[jx][jy] = "J"
            
        # Defenders
        for d in defenders:
            if d.is_alive:
                dx, dy = d.pos
                grid[dx][dy] = "D"
                
        # Attackers
        for a in attackers:
            if a.is_alive:
                ax, ay = a.pos
                grid[ax][ay] = "A" if a.role == "infiltrator" else "F"
                
        lines = ["".join(row) for row in grid]
        return "\n".join(lines)

    def render_matplotlib(
        self,
        attackers: List[Any],
        defenders: List[Any],
        step_num: int = 0,
        ax: Optional[plt.Axes] = None,
    ) -> plt.Figure:
        """Renders high-quality 2D tactical Matplotlib visualization of the Chakravyuha."""
        if ax is None:
            fig, ax = plt.subplots(figsize=(8, 8))
        else:
            fig = ax.figure

        ax.clear()
        ax.set_facecolor("#121824")
        ax.set_xlim(-0.5, self.grid_size - 0.5)
        ax.set_ylim(-0.5, self.grid_size - 0.5)
        ax.invert_yaxis()  # Match matrix grid coordinates (top-to-bottom)

        # Plot ring wall cells
        ring_colors = ["#4A5568", "#2B6CB0", "#2C5282", "#2A4365", "#1A365D", "#1E3A8A", "#172554"]
        for r in range(1, self.config.num_rings + 1):
            color = ring_colors[(r - 1) % len(ring_colors)]
            xs = [pos[1] for pos in self.ring_cells[r] if pos != self.entry_gates[r] and pos != self.exit_gates[r]]
            ys = [pos[0] for pos in self.ring_cells[r] if pos != self.entry_gates[r] and pos != self.exit_gates[r]]
            ax.scatter(xs, ys, c=color, s=25, marker="s", alpha=0.6, label=f"Ring {r}" if step_num == 0 and r == 1 else None)
            
            # Entry Gate
            eg = self.entry_gates[r]
            ax.scatter(eg[1], eg[0], c="#48BB78", s=60, marker="o", edgecolors="white", linewidths=1.2, zorder=4)
            # Exit Gate
            ex = self.exit_gates[r]
            ax.scatter(ex[1], ex[0], c="#38B2AC", s=50, marker="v", edgecolors="white", linewidths=1.0, zorder=4)

        # Center target
        cx, cy = self.center
        ax.scatter(cy, cx, c="#ECC94B", s=180, marker="*", edgecolors="#D69E2E", linewidths=1.5, zorder=6, label="Center (Core)")

        # Jayadratha
        if self.jayadratha_active and self.jayadratha_pos:
            jx, jy = self.jayadratha_pos
            ax.scatter(jy, jx, c="#E53E3E", s=130, marker="X", edgecolors="white", linewidths=2.0, zorder=7, label="Jayadratha (Gate Locked)")
        elif self.jayadratha_pos:
            jx, jy = self.jayadratha_pos
            ax.scatter(jy, jx, c="#CBD5E0", s=60, marker="s", alpha=0.3, zorder=3)

        # Defenders
        alive_defenders = [d for d in defenders if d.is_alive]
        if alive_defenders:
            dxs = [d.pos[1] for d in alive_defenders]
            dys = [d.pos[0] for d in alive_defenders]
            # Color defenders by inner ring strength
            def_colors = [d.strength_color for d in alive_defenders]
            ax.scatter(dxs, dys, c=def_colors, s=50, marker="^", edgecolors="#FEB2B2", linewidths=1.0, zorder=5, label="Kaurava Defenders")

        # Attackers
        for a in attackers:
            if a.is_alive:
                if a.role == "infiltrator":
                    ax.scatter(a.pos[1], a.pos[0], c="#3182CE", s=160, marker="o", edgecolors="#63B3ED", linewidths=2.5, zorder=8, label="Abhimanyu (Infiltrator)")
                elif a.role == "scout":
                    ax.scatter(a.pos[1], a.pos[0], c="#ED8936", s=90, marker="D", edgecolors="#FEEBC8", linewidths=1.5, zorder=8, label="Pandava Scout")
                else:
                    ax.scatter(a.pos[1], a.pos[0], c="#38A169", s=90, marker="o", edgecolors="#C6F6D5", linewidths=1.5, zorder=8, label="Pandava Follower")

        ax.set_title(f"Chakravyuha Tactical Grid — Step {step_num} | Jayadratha Gate Lock: {'ACTIVE' if self.jayadratha_active else 'INACTIVE'}",
                     color="white", fontsize=11, fontweight="bold", pad=10)
        ax.grid(True, color="#2D3748", linestyle=":", alpha=0.5)
        ax.tick_params(colors="gray")
        
        return fig
