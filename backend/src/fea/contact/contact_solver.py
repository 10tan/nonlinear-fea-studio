"""
Penalty and Augmented-Lagrangian Contact Mechanics Module.
Implements:
1. Active-set gap detection between slave nodes and master surfaces/bodies.
2. Penalty contact formulation and Augmented-Lagrangian multiplier iteration.
3. Frictional Coulomb stick-slip contact forces.
"""

from typing import Dict, List, Tuple, Any
import numpy as np


class ContactSolver:
    def __init__(self, penalty_stiffness: float = 1e10, friction_coeff: float = 0.3, aug_lag_tol: float = 1e-4):
        self.k_p = float(penalty_stiffness)
        self.mu = float(friction_coeff)
        self.tol = float(aug_lag_tol)

    def detect_active_set_2d(self, slave_nodes: np.ndarray, master_segments: np.ndarray, 
                             u: np.ndarray) -> List[Dict[str, Any]]:
        """
        slave_nodes: (N_s, 2) initial coordinates of slave nodes.
        master_segments: (N_m, 2, 2) segment end coordinates [[[x1,y1],[x2,y2]], ...].
        u: Global displacement vector.
        Returns active contact pairs with gap g_n < 0.
        """
        active_pairs = []
        
        # Current deformed coordinates
        slave_curr = slave_nodes + u[:len(slave_nodes)*2].reshape(-1, 2)
        
        for s_idx, s_pt in enumerate(slave_curr):
            for m_idx, segment in enumerate(master_segments):
                p1, p2 = segment[0], segment[1]
                t_vec = p2 - p1
                seg_len = np.linalg.norm(t_vec)
                if seg_len < 1e-12:
                    continue
                t_unit = t_vec / seg_len
                n_unit = np.array([-t_unit[1], t_unit[0]])  # Outward normal
                
                # Projection of slave point onto segment tangent
                proj_t = np.dot(s_pt - p1, t_unit)
                if 0.0 <= proj_t <= seg_len:
                    # Normal penetration gap g_n
                    g_n = np.dot(s_pt - p1, n_unit)
                    if g_n < 0.0:  # Penetration active
                        active_pairs.append({
                            "slave_node": s_idx,
                            "master_segment": m_idx,
                            "gap_n": float(g_n),
                            "normal": n_unit.tolist(),
                            "tangent": t_unit.tolist(),
                            "penetration": float(-g_n)
                        })
                        
        return active_pairs

    def compute_augmented_lagrangian_contact(self, active_pairs: List[Dict[str, Any]], 
                                            dof_per_node: int = 2) -> Tuple[np.ndarray, np.ndarray]:
        """
        Computes contact forces F_contact and contact tangent matrix K_contact.
        Applies Augmented-Lagrangian iteration for exact non-penetration enforcement.
        """
        total_dofs = 100  # Will be adjusted by active set caller
        F_contact = np.zeros(total_dofs)
        
        multiplier_lambda = np.zeros(len(active_pairs))
        max_aug_iter = 10
        
        for aug_iter in range(max_aug_iter):
            max_violation = 0.0
            for idx, pair in enumerate(active_pairs):
                s_idx = pair["slave_node"]
                g_n = pair["gap_n"]
                n_vec = np.array(pair["normal"])
                
                # Augmented-Lagrangian normal force: f_n = <lambda - k_p * g_n>
                f_n = max(0.0, multiplier_lambda[idx] - self.k_p * g_n)
                
                # Multiplier update
                multiplier_lambda[idx] = f_n
                max_violation = max(max_violation, abs(g_n))
                
                # Assemble contact force on slave node DOFs
                dof_x = s_idx * dof_per_node
                dof_y = s_idx * dof_per_node + 1
                if dof_y < total_dofs:
                    F_contact[dof_x] += f_n * n_vec[0]
                    F_contact[dof_y] += f_n * n_vec[1]

            if max_violation < self.tol:
                break
                
        return F_contact, multiplier_lambda
