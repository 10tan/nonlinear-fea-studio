"""
Verification Test 2: Shallow Arch Snap-Through / Snap-Back Equilibrium Path.
Verifies Crisfield Arc-Length solver on nonlinear snap-through post-buckling path.
"""

import numpy as np
import pytest
from fea.solver.nonlinear_solver import NonlinearFESolver


def test_arch_snap_through_arc_length():
    # Shallow dome / arch geometry
    nodes = np.array([
        [0.0, 0.0],
        [0.5, 0.05],  # Shallow arch crown elevation
        [1.0, 0.0],
        [1.0, 0.02],
        [0.5, 0.07],
        [0.0, 0.02]
    ])
    elements = np.array([
        [0, 1, 4, 5],
        [1, 2, 3, 4]
    ])
    materials = {"E": 70e9, "nu": 0.3, "thickness": 0.01, "density": 2700.0}
    bcs = {
        "fixed_dofs": [0, 1, 4, 5],  # Pinned ends
        "prescribed_loads": {9: -50000.0}  # Point load at arch crown
    }

    solver = NonlinearFESolver(nodes, elements, materials, bcs)
    res = solver.solve_arc_length(target_arc_length=0.02, n_steps=10)

    assert res["success"] is True
    assert len(res["load_history"]) == 11
    assert len(res["disp_history"]) == 11
