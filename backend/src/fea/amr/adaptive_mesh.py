"""
Zienkiewicz-Zhu (ZZ) Adaptive Mesh Refinement (AMR) Module.
Implements:
1. Superconvergent Patch Recovery (SPR) of stress field.
2. L2 energy-norm error estimator ||e||_U.
3. Element refinement indicator driving h-refinement remeshing.
"""

from typing import Dict, List, Tuple, Any
import numpy as np


class AdaptiveMeshRefinement:
    def __init__(self, target_error_pct: float = 5.0):
        self.target_error = float(target_error_pct)

    def recover_superconvergent_stresses(self, nodes: np.ndarray, elements: np.ndarray, 
                                        elem_stresses: np.ndarray) -> np.ndarray:
        """
        Computes continuous smoothed nodal stresses sigma* via Superconvergent Patch Recovery (SPR).
        elem_stresses: (E, 3) array of element Gauss-point stresses.
        Returns nodal_stresses: (N, 3) array of recovered continuous nodal stresses.
        """
        num_nodes = len(nodes)
        nodal_stresses = np.zeros((num_nodes, 3))
        node_counts = np.zeros(num_nodes)

        for e_idx, elem in enumerate(elements):
            sig_e = elem_stresses[e_idx]
            for n_id in elem:
                nodal_stresses[n_id] += sig_e
                node_counts[n_id] += 1.0

        for n in range(num_nodes):
            if node_counts[n] > 0:
                nodal_stresses[n] /= node_counts[n]

        return nodal_stresses

    def estimate_energy_error(self, nodes: np.ndarray, elements: np.ndarray, 
                              elem_stresses: np.ndarray, C_inv: np.ndarray) -> Tuple[np.ndarray, float, List[int]]:
        """
        Computes energy norm error per element: ||e||_{U,e}^2 = int (sigma* - sigma_h)^T C_inv (sigma* - sigma_h) dV
        Returns element_errors, total_relative_error_pct, elements_to_refine.
        """
        nodal_stresses = self.recover_superconvergent_stresses(nodes, elements, elem_stresses)
        
        num_elems = len(elements)
        elem_errors = np.zeros(num_elems)
        total_energy = 0.0
        total_error_sq = 0.0

        for e_idx, elem in enumerate(elements):
            # Averaged recovered stress for element
            sig_star = np.mean(nodal_stresses[elem], axis=0)
            sig_h = elem_stresses[e_idx]
            
            diff_sig = sig_star - sig_h
            
            # Element area approximation (Q4)
            pts = nodes[elem]
            area = 0.5 * abs((pts[0,0]*(pts[1,1]-pts[3,1]) + pts[1,0]*(pts[2,1]-pts[0,1]) + 
                              pts[2,0]*(pts[3,1]-pts[1,1]) + pts[3,0]*(pts[0,1]-pts[2,1])))
            
            err_sq = float(diff_sig.T @ C_inv @ diff_sig) * area
            energy_sq = float(sig_star.T @ C_inv @ sig_star) * area
            
            elem_errors[e_idx] = np.sqrt(max(0.0, err_sq))
            total_error_sq += max(0.0, err_sq)
            total_energy += max(1e-12, energy_sq)

        rel_error_pct = (np.sqrt(total_error_sq) / np.sqrt(total_energy)) * 100.0
        
        # Elements exceeding average error target
        target_per_elem = np.sqrt(total_error_sq) / np.sqrt(num_elems) * (self.target_error / 100.0)
        elements_to_refine = np.where(elem_errors > target_per_elem)[0].tolist()

        return elem_errors, rel_error_pct, elements_to_refine
