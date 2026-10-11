"""
Unit tests for Explicit Central-Difference Dynamics with added-mass FSI.
"""

import numpy as np
import pytest
from fea.solver.nonlinear_solver import NonlinearFESolver


def test_explicit_dynamics_pulse():
    # Simple 2-element cantilever beam
    nodes = [[0.0, 0.0], [1.0, 0.0], [2.0, 0.0], [2.0, 0.2], [1.0, 0.2], [0.0, 0.2]]
    elements = [[0, 1, 4, 5], [1, 2, 3, 4]]
    materials = {"E": 210e9, "nu": 0.3, "thickness": 0.01, "density": 7850.0}
    bcs = {"fixed_dofs": [0, 1, 10, 11], "prescribed_loads": {7: -50000.0}}
    
    solver = NonlinearFESolver(nodes, elements, materials, bcs)
    
    res = solver.solve_explicit_dynamics(total_time=0.001, dt=1e-5, added_mass_factor=0.25)
    
    assert res["success"]
    assert len(res["time"]) > 0
    assert len(res["displacements"]) > 0
    assert len(res["velocities"]) > 0
    # Tip deflection should be non-zero after pulse
    final_disp = np.array(res["displacements"][-1])
    assert final_disp[7] != 0.0
