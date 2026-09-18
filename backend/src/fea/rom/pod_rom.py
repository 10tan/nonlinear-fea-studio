"""
POD-Galerkin Reduced-Order Model (ROM) Module.
Implements:
1. Snapshot SVD factorization of nonlinear displacement/stress trajectories.
2. POD reduced basis extraction Phi_r.
3. Online Galerkin projection solver for near-real-time parameter sweeps.
"""

from typing import Dict, List, Tuple, Any
import numpy as np


class PODReducedOrderModel:
    def __init__(self, n_modes: int = 5):
        self.n_modes = int(n_modes)
        self.Phi_r: Any = None
        self.singular_values: Any = None
        self.energy_retained: float = 0.0

    def fit_snapshots(self, snapshot_matrix: np.ndarray) -> Dict[str, Any]:
        """
        snapshot_matrix: (N_dofs, N_snapshots) array of displacement states across load steps.
        SVD: S = U * Sigma * V^T
        Returns summary of reduced basis energy & singular spectrum.
        """
        S = np.array(snapshot_matrix, dtype=float)
        U, s, Vt = np.linalg.svd(S, full_matrices=False)
        
        r = min(self.n_modes, len(s))
        self.Phi_r = U[:, :r]
        self.singular_values = s
        
        total_variance = np.sum(s**2)
        retained_variance = np.sum(s[:r]**2)
        self.energy_retained = float(retained_variance / (total_variance + 1e-12)) * 100.0

        return {
            "n_modes": r,
            "singular_values": s.tolist(),
            "energy_retained_pct": self.energy_retained,
            "success": True
        }

    def predict_online(self, K_full: np.ndarray, P_full: np.ndarray, free_dofs: np.ndarray) -> np.ndarray:
        """
        Sub-second online evaluation via Galerkin projection onto reduced space:
        K_r = Phi_r^T * K * Phi_r
        f_r = Phi_r^T * P
        a = K_r^-1 * f_r
        u_approx = Phi_r * a
        """
        if self.Phi_r is None:
            raise ValueError("POD ROM has not been fitted with snapshot data.")

        total_dofs = len(P_full)
        Phi_free = self.Phi_r[free_dofs, :]
        K_free = K_full[np.ix_(free_dofs, free_dofs)]
        P_free = P_full[free_dofs]

        K_r = Phi_free.T @ K_free @ Phi_free
        f_r = Phi_free.T @ P_free

        a_coeff = np.linalg.solve(K_r + 1e-8 * np.eye(K_r.shape[0]), f_r)
        
        u_approx = np.zeros(total_dofs)
        u_approx[free_dofs] = Phi_free @ a_coeff
        
        return u_approx
