"""
Unit tests for SIMP Topology Optimization with Adjoint Sensitivity Analysis.
"""

import numpy as np
import pytest
from fea.topopt.simp_topopt import SIMPTopologyOptimizer


def test_simp_filter_preparation():
    opt = SIMPTopologyOptimizer(nelx=10, nely=5, volfrac=0.5, rmin=1.5)
    assert opt.H.shape == (50, 50)
    assert np.all(opt.Hs > 0)


def test_simp_optimization_loop():
    opt = SIMPTopologyOptimizer(nelx=10, nely=6, volfrac=0.4, rmin=1.5)
    
    # Quadratic compliance model where element 0 has highest strain energy
    def mock_solver(rho, penal):
        U = np.zeros(20)
        # Mock compliance c = sum( (1 / rho^p) * strain_energies )
        strain_energies = np.linspace(100.0, 10.0, len(rho))
        c = float(np.sum((rho**(-penal)) * strain_energies * 0.01))
        return U, c, strain_energies

    res = opt.optimize(mock_solver, max_iter=15, tol=1e-2)
    
    assert "final_densities" in res
    assert len(res["compliance_history"]) > 0
    assert len(res["volfrac_history"]) > 0
    # Average volume fraction should respect targeted volfrac
    final_densities = np.array(res["final_densities"])
    assert final_densities.shape == (6, 10)
    assert np.isclose(res["volfrac_history"][-1], 0.4, atol=0.05)
