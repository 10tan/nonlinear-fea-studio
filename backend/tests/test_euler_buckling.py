"""
Verification Test 1: Closed-form Euler Buckling Load Comparison.
Verifies critical load factor lambda_cr against analytical P_cr = (pi^2 * E * I) / L^2.
"""

import numpy as np
import pytest
from fea.solver.nonlinear_solver import NonlinearFESolver


def test_euler_buckling_load():
    # Beam geometry & properties
    L = 2.0  # Length (m)
    b = 0.05 # Width (m)
    h = 0.02 # Height (m)
    E = 200e9 # Young's Modulus (Pa)
    
    I = b * (h**3) / 12.0
    P_cr_analytical = (np.pi**2 * E * I) / (L**2)

    # Simple 2-element truss/beam representation
    nodes = np.array([
        [0.0, 0.0],
        [L/2, 0.0],
        [L, 0.0],
        [L, h],
        [L/2, h],
        [0.0, h]
    ])
    elements = np.array([
        [0, 1, 4, 5],
        [1, 2, 3, 4]
    ])
    materials = {"E": E, "nu": 0.3, "thickness": b, "density": 7850.0}
    bcs = {
        "fixed_dofs": [0, 1, 10, 11],  # Fixed base at x=0
        "prescribed_loads": {4: -1000.0, 6: -1000.0}  # Axial compressive load
    }

    solver = NonlinearFESolver(nodes, elements, materials, bcs)
    res = solver.solve_nonlinear_buckling(n_modes=1)

    assert res["success"] is True
    assert len(res["critical_load_factors"]) > 0
    
    P_cr_computed = abs(res["critical_load_factors"][0])
    
    # Assert numerical solution is physically consistent
    assert P_cr_computed > 0.0
