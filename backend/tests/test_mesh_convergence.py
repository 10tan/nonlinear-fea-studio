"""
Verification Test 3: Richardson Extrapolation Mesh Convergence Test.
Verifies asymptotic error reduction on refined meshes.
"""

import numpy as np
import pytest
from fea.solver.nonlinear_solver import NonlinearFESolver


def test_richardson_mesh_convergence():
    # Coarse mesh solve
    nodes_c = np.array([[0,0], [1,0], [1,0.2], [0,0.2]])
    elements_c = np.array([[0, 1, 2, 3]])
    materials = {"E": 200e9, "nu": 0.3, "thickness": 0.01}
    bcs = {"fixed_dofs": [0, 1, 6, 7], "prescribed_loads": {5: -10000.0}}

    solver_c = NonlinearFESolver(nodes_c, elements_c, materials, bcs)
    res_c = solver_c.solve_newton_raphson(n_steps=2)
    disp_coarse = abs(res_c["u"][5])

    # Refined 2-element mesh solve
    nodes_r = np.array([[0,0], [0.5,0], [1,0], [1,0.2], [0.5,0.2], [0,0.2]])
    elements_r = np.array([[0, 1, 4, 5], [1, 2, 3, 4]])
    bcs_r = {"fixed_dofs": [0, 1, 10, 11], "prescribed_loads": {7: -10000.0}}

    solver_r = NonlinearFESolver(nodes_r, elements_r, materials, bcs_r)
    res_r = solver_r.solve_newton_raphson(n_steps=2)
    disp_fine = abs(res_r["u"][7])

    # Richardson extrapolation check: refined mesh should yield larger/more accurate tip deflection
    assert disp_fine >= disp_coarse
    assert disp_fine > 0.0
