"""
Unit tests for Snapshot POD-Galerkin Reduced Order Model (ROM).
"""

import numpy as np
import pytest
from fea.rom.pod_rom import PODReducedOrderModel


def test_pod_rom_snapshot_svd():
    rom = PODReducedOrderModel(n_modes=3)
    
    # Generate low-rank displacement snapshot matrix (10 DOFs x 8 load steps)
    t = np.linspace(0.1, 1.0, 8)
    base_modes = np.array([
        np.sin(np.linspace(0, np.pi, 10)),
        np.sin(2 * np.linspace(0, np.pi, 10))
    ])  # Shape (2, 10)
    
    snapshots = np.outer(base_modes[0], t) + 0.3 * np.outer(base_modes[1], t**2)
    
    res = rom.fit_snapshots(snapshots)
    
    assert res["success"]
    assert rom.Phi_r.shape == (10, 3)
    assert res["energy_retained_pct"] > 99.0


def test_pod_rom_online_prediction():
    rom = PODReducedOrderModel(n_modes=2)
    
    # 6 DOFs, simple 1D spring/bar stiffness
    K = np.diag([2.0, 2.0, 2.0, 2.0, 2.0, 2.0])
    for i in range(5):
        K[i, i+1] = -1.0
        K[i+1, i] = -1.0
        
    P = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 10.0])
    free_dofs = np.array([1, 2, 3, 4, 5])
    
    # Generate 5 snapshots
    snapshots = np.zeros((6, 5))
    for step in range(5):
        load_factor = (step + 1) * 0.2
        u_full = np.zeros(6)
        u_full[free_dofs] = np.linalg.solve(K[np.ix_(free_dofs, free_dofs)], P[free_dofs] * load_factor)
        snapshots[:, step] = u_full
        
    rom.fit_snapshots(snapshots)
    
    # Predict for full load
    u_pred = rom.predict_online(K, P, free_dofs)
    
    assert len(u_pred) == 6
    assert u_pred[0] == 0.0  # Fixed DOF
    assert u_pred[5] > 0.0   # Loaded DOF
