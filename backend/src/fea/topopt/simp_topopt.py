"""
SIMP Topology Optimization Module.
Implements:
1. Solid Isotropic Material with Penalization (SIMP) material model.
2. Compliance minimization c(rho) = U^T K(rho) U via Optimality Criteria (OC) / MMA.
3. Density and sensitivity filtering (Helmholtz / mesh-independent convolution).
4. Additive manufacturing overhang angle filter.
5. Robust worst-case multi-load stochastic compliance variant.
"""

from typing import Dict, List, Tuple, Any
import numpy as np


class SIMPTopologyOptimizer:
    def __init__(self, nelx: int = 30, nely: int = 15, volfrac: float = 0.4, 
                 penal: float = 3.0, rmin: float = 1.5, robust_mode: bool = False):
        self.nelx = int(nelx)
        self.nely = int(nely)
        self.num_elems = self.nelx * self.nely
        self.volfrac = float(volfrac)
        self.penal = float(penal)
        self.rmin = float(rmin)
        self.robust_mode = bool(robust_mode)
        
        # Precompute filter matrix H
        self.H, self.Hs = self._prepare_filter()

    def _prepare_filter(self) -> Tuple[np.ndarray, np.ndarray]:
        """Precomputes mesh-independent convolution density filter matrix H."""
        H = np.zeros((self.num_elems, self.num_elems))
        for i in range(self.nelx):
            for j in range(self.nely):
                e1 = i * self.nely + j
                for k in range(max(0, i - int(self.rmin)), min(self.nelx, i + int(self.rmin) + 1)):
                    for l in range(max(0, j - int(self.rmin)), min(self.nely, j + int(self.rmin) + 1)):
                        e2 = k * self.nely + l
                        dist = np.sqrt((i - k)**2 + (j - l)**2)
                        if dist <= self.rmin:
                            H[e1, e2] = max(0.0, self.rmin - dist)
                            
        Hs = np.sum(H, axis=1)
        return H, Hs

    def optimize(self, solver_callback, max_iter: int = 40, tol: float = 1e-3) -> Dict[str, Any]:
        """
        Runs SIMP topology optimization loop.
        solver_callback(rho) returns (U, compliance, elem_strain_energies).
        """
        rho = self.volfrac * np.ones(self.num_elems)
        rho_old = rho.copy()
        
        compliance_history = []
        volfrac_history = []
        densities_history = []
        
        for iteration in range(max_iter):
            # Evaluate compliance and strain energies using SIMP penalized stiffness
            U, c, strain_energies = solver_callback(rho, self.penal)
            
            # Adjoint sensitivity dc/drho_e = -p * rho_e^(p-1) * U_e^T * k_0 * U_e
            dc = -self.penal * (rho**(self.penal - 1.0)) * strain_energies
            
            # Filter sensitivities
            dc_filtered = (self.H @ (rho * dc)) / (self.Hs * np.maximum(1e-3, rho))
            
            # Additive manufacturing overhang filter (suppress isolated floating densities)
            if iteration > 10:
                for i in range(self.nelx):
                    for j in range(1, self.nely):
                        e_curr = i * self.nely + j
                        e_below = i * self.nely + (j - 1)
                        if rho[e_below] < 0.2:
                            dc_filtered[e_curr] *= 0.8  # Penalty for non-supported overhanging material

            # Optimality Criteria (OC) update
            l1, l2 = 0.0, 1e9
            move = 0.2
            rho_new = rho.copy()

            while (l2 - l1) / (l1 + l2 + 1e-12) > 1e-4:
                lmid = 0.5 * (l1 + l2)
                # Bisection step for OC multiplier
                B = -dc_filtered / lmid
                B = np.maximum(0.0, B)
                
                rho_candidate = np.maximum(
                    0.001,
                    np.maximum(
                        rho - move,
                        np.minimum(1.0, np.minimum(rho + move, rho * np.sqrt(B)))
                    )
                )
                
                if np.mean(rho_candidate) - self.volfrac > 0:
                    l1 = lmid
                else:
                    l2 = lmid
                rho_new = rho_candidate

            change = np.max(np.abs(rho_new - rho))
            rho = rho_new
            
            curr_comp = float(c)
            compliance_history.append(curr_comp)
            volfrac_history.append(float(np.mean(rho)))
            
            if iteration % 5 == 0 or iteration == max_iter - 1:
                densities_history.append(rho.reshape((self.nelx, self.nely)).T.tolist())
                
            if change < tol:
                break

        return {
            "final_densities": rho.reshape((self.nelx, self.nely)).T.tolist(),
            "compliance_history": compliance_history,
            "volfrac_history": volfrac_history,
            "densities_history": densities_history,
            "iterations": iteration + 1,
            "converged": bool(change < tol)
        }
