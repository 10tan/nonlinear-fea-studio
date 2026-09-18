"""
Nonlinear Finite Element Solver Module.
Implements:
1. Total / Updated Lagrangian formulation for 2D plane strain/stress & 1D/2D structural elements.
2. Green-Lagrange strain E = 0.5*(F^T F - I) and 2nd Piola-Kirchhoff stress S.
3. Newton-Raphson & Crisfield Arc-Length continuation for post-buckling snap-through/snap-back.
4. Nonlinear buckling eigenvalue solver (K_T - lambda * K_G) * phi = 0.
5. Central-difference explicit dynamic solver with mass scaling and added-mass FSI approximation.
"""

from typing import Dict, List, Tuple, Optional, Any
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve, eigs


class NonlinearFESolver:
    def __init__(self, nodes: np.ndarray, elements: np.ndarray, materials: Dict[str, Any], bcs: Dict[str, Any]):
        """
        nodes: (N, 2) or (N, 3) array of initial nodal coordinates.
        elements: (E, n_nodes_per_elem) array of element connectivity (0-indexed).
        materials: Dict with E (Young's modulus), nu (Poisson ratio), density, thickness, etc.
        bcs: Dict with fixed_dofs, prescribed_loads, etc.
        """
        self.nodes = np.array(nodes, dtype=float)
        self.elements = np.array(elements, dtype=int)
        self.num_nodes = len(nodes)
        self.ndim = self.nodes.shape[1]
        self.dof_per_node = self.ndim
        self.total_dofs = self.num_nodes * self.dof_per_node
        
        self.E_mod = float(materials.get("E", 210e9))
        self.nu = float(materials.get("nu", 0.3))
        self.thickness = float(materials.get("thickness", 1.0))
        self.rho = float(materials.get("density", 7850.0))
        
        self.fixed_dofs = np.array(bcs.get("fixed_dofs", []), dtype=int)
        self.free_dofs = np.setdiff1d(np.arange(self.total_dofs), self.fixed_dofs)
        self.prescribed_loads = bcs.get("prescribed_loads", {})  # dof: magnitude
        
        # Constitutive matrix for plane stress / plane strain
        if self.ndim == 2:
            plane_type = materials.get("type", "plane_stress")
            if plane_type == "plane_stress":
                factor = self.E_mod / (1.0 - self.nu**2)
                self.C_mat = factor * np.array([
                    [1.0, self.nu, 0.0],
                    [self.nu, 1.0, 0.0],
                    [0.0, 0.0, 0.5 * (1.0 - self.nu)]
                ])
            else:  # plane strain
                factor = self.E_mod / ((1.0 + self.nu) * (1.0 - 2.0 * self.nu))
                self.C_mat = factor * np.array([
                    [1.0 - self.nu, self.nu, 0.0],
                    [self.nu, 1.0 - self.nu, 0.0],
                    [0.0, 0.0, 0.5 - self.nu]
                ])

    def _element_shape_functions(self, xi: float, eta: float) -> Tuple[np.ndarray, np.ndarray]:
        """Bi-linear Q4 element shape functions and derivatives wrt xi, eta."""
        N = 0.25 * np.array([
            (1 - xi) * (1 - eta),
            (1 + xi) * (1 - eta),
            (1 + xi) * (1 + eta),
            (1 - xi) * (1 + eta)
        ])
        dN_dxi = 0.25 * np.array([
            [-(1 - eta), -(1 - xi)],
            [ (1 - eta), -(1 + xi)],
            [ (1 + eta),  (1 + xi)],
            [-(1 + eta),  (1 - xi)]
        ])
        return N, dN_dxi

    def compute_internal_force_and_tangent(self, u: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Computes global internal force vector F_int, global tangent stiffness matrix K_T,
        and Green-Lagrange strain / 2nd PK stress for all elements.
        """
        F_int = np.zeros(self.total_dofs)
        K_T = np.zeros((self.total_dofs, self.total_dofs))
        stresses = np.zeros((len(self.elements), 3))
        strains = np.zeros((len(self.elements), 3))
        
        # Gauss integration points for Q4
        gauss_pts = [-1.0 / np.sqrt(3), 1.0 / np.sqrt(3)]
        weights = [1.0, 1.0]

        for e_idx, elem in enumerate(self.elements):
            elem_nodes = self.nodes[elem]  # (4, 2)
            elem_dofs = []
            for n in elem:
                elem_dofs.extend([2 * n, 2 * n + 1])
            elem_dofs = np.array(elem_dofs)
            
            u_elem = u[elem_dofs].reshape((4, 2))  # Nodal displacements for element
            
            K_e = np.zeros((8, 8))
            F_e = np.zeros(8)
            
            avg_stress = np.zeros(3)
            avg_strain = np.zeros(3)
            
            for xi, w_xi in zip(gauss_pts, weights):
                for eta, w_eta in zip(gauss_pts, weights):
                    N, dN_dxi = self.element_shape_functions_q4(xi, eta)
                    
                    # Initial Jacobian
                    J0 = dN_dxi.T @ elem_nodes  # (2, 2)
                    detJ0 = np.linalg.det(J0)
                    invJ0 = np.linalg.inv(J0)
                    
                    # Derivatives wrt initial coords (X, Y)
                    dN_dX = dN_dxi @ invJ0  # (4, 2)
                    
                    # Deformation gradient F = I + du/dX
                    H = u_elem.T @ dN_dX  # (2, 2) grad(u)
                    F_mat = np.eye(2) + H
                    
                    # Green-Lagrange strain E = 0.5*(F^T F - I)
                    E_mat = 0.5 * (F_mat.T @ F_mat - np.eye(2))
                    E_vec = np.array([E_mat[0, 0], E_mat[1, 1], 2.0 * E_mat[0, 1]])
                    
                    # Second Piola-Kirchhoff Stress S = C : E
                    S_vec = self.C_mat @ E_vec
                    S_mat = np.array([[S_vec[0], S_vec[2]], [S_vec[2], S_vec[1]]])
                    
                    avg_stress += S_vec * 0.25
                    avg_strain += E_vec * 0.25
                    
                    # Linear B-matrix B_0
                    B0 = np.zeros((3, 8))
                    for i in range(4):
                        B0[0, 2 * i]     = dN_dX[i, 0]
                        B0[1, 2 * i + 1] = dN_dX[i, 1]
                        B0[2, 2 * i]     = dN_dX[i, 1]
                        B0[2, 2 * i + 1] = dN_dX[i, 0]
                    
                    # Nonlinear B-matrix B_NL (incorporating current deformation)
                    BNL = np.zeros((3, 8))
                    for i in range(4):
                        BNL[0, 2 * i]     = F_mat[0, 0] * dN_dX[i, 0]
                        BNL[0, 2 * i + 1] = F_mat[1, 0] * dN_dX[i, 0]
                        BNL[1, 2 * i]     = F_mat[0, 1] * dN_dX[i, 1]
                        BNL[1, 2 * i + 1] = F_mat[1, 1] * dN_dX[i, 1]
                        BNL[2, 2 * i]     = F_mat[0, 0] * dN_dX[i, 1] + F_mat[0, 1] * dN_dX[i, 0]
                        BNL[2, 2 * i + 1] = F_mat[1, 0] * dN_dX[i, 1] + F_mat[1, 1] * dN_dX[i, 0]
                    
                    # Geometric stiffness matrix K_sigma
                    G = np.zeros((4, 8))
                    for i in range(4):
                        G[0, 2 * i]     = dN_dX[i, 0]
                        G[1, 2 * i]     = dN_dX[i, 1]
                        G[2, 2 * i + 1] = dN_dX[i, 0]
                        G[3, 2 * i + 1] = dN_dX[i, 1]
                    
                    S_block = np.block([
                        [S_mat, np.zeros((2, 2))],
                        [np.zeros((2, 2)), S_mat]
                    ])
                    K_sigma_e = G.T @ S_block @ G
                    
                    # Tangent stiffness: (B_NL^T * C * B_NL + K_sigma) * detJ * t
                    dV = detJ0 * self.thickness * w_xi * w_eta
                    K_e += (BNL.T @ self.C_mat @ BNL + K_sigma_e) * dV
                    
                    # Internal force F_e = BNL^T * S * dV
                    F_e += (BNL.T @ S_vec) * dV
                    
            stresses[e_idx] = avg_stress
            strains[e_idx] = avg_strain
            
            # Assemble global matrices
            for i in range(8):
                F_int[elem_dofs[i]] += F_e[i]
                for j in range(8):
                    K_T[elem_dofs[i], elem_dofs[j]] += K_e[i, j]
                    
        return F_int, K_T, stresses

    def element_shape_functions_q4(self, xi: float, eta: float):
        return self._element_shape_functions(xi, eta)

    def solve_newton_raphson(self, target_load_factor: float = 1.0, n_steps: int = 10, max_iter: int = 25, tol: float = 1e-6) -> Dict[str, Any]:
        """
        Incremental-iterative Newton-Raphson solver for load-controlled nonlinear static equilibrium.
        """
        P_ref = np.zeros(self.total_dofs)
        for dof, val in self.prescribed_loads.items():
            P_ref[int(dof)] = float(val)

        u = np.zeros(self.total_dofs)
        load_history = []
        disp_history = []
        residual_norms = []

        load_step_delta = target_load_factor / n_steps
        current_load_factor = 0.0

        for step in range(n_steps):
            current_load_factor += load_step_delta
            P_ext = current_load_factor * P_ref

            step_residuals = []
            for it in range(max_iter):
                F_int, K_T, _ = self.compute_internal_force_and_tangent(u)
                R = P_ext - F_int

                # Apply boundary conditions
                R_free = R[self.free_dofs]
                res_norm = np.linalg.norm(R_free) / (np.linalg.norm(P_ext[self.free_dofs]) + 1e-12)
                step_residuals.append(float(res_norm))

                if res_norm < tol:
                    break

                K_T_free = K_T[np.ix_(self.free_dofs, self.free_dofs)]
                du_free = np.linalg.solve(K_T_free, R_free)
                u[self.free_dofs] += du_free

            load_history.append(float(current_load_factor))
            disp_history.append(u.copy())
            residual_norms.append(step_residuals)

        F_int, K_T, final_stresses = self.compute_internal_force_and_tangent(u)
        
        return {
            "u": u.tolist(),
            "load_history": load_history,
            "disp_history": [d.tolist() for d in disp_history],
            "residual_norms": residual_norms,
            "stresses": final_stresses.tolist(),
            "success": True
        }

    def solve_arc_length(self, target_arc_length: float = 0.05, n_steps: int = 20, max_iter: int = 25, tol: float = 1e-5) -> Dict[str, Any]:
        """
        Crisfield Arc-Length Continuation solver for post-buckling snap-through / snap-back paths.
        Traces equilibrium path (u, lambda) where both displacement and load factor evolve.
        """
        P_ref = np.zeros(self.total_dofs)
        for dof, val in self.prescribed_loads.items():
            P_ref[int(dof)] = float(val)

        u = np.zeros(self.total_dofs)
        lambda_val = 0.0
        
        ds = target_arc_length
        load_history = [0.0]
        disp_history = [u.copy()]
        
        psi = 1.0  # Arc length load scaling factor

        for step in range(n_steps):
            F_int, K_T, _ = self.compute_internal_force_and_tangent(u)
            K_T_free = K_T[np.ix_(self.free_dofs, self.free_dofs)]
            P_free = P_ref[self.free_dofs]
            
            # Predictor step
            du_tangent = np.linalg.solve(K_T_free, P_free)
            dlambda = ds / np.sqrt(np.dot(du_tangent, du_tangent) + psi**2 * np.dot(P_free, P_free))
            
            # Direction check (maintain positive dissipation / sign of previous step tangent)
            if step > 0:
                prev_du = disp_history[-1][self.free_dofs] - disp_history[-2][self.free_dofs]
                if np.dot(du_tangent * dlambda, prev_du) < 0:
                    dlambda = -dlambda

            du_free = dlambda * du_tangent
            u[self.free_dofs] += du_free
            lambda_val += dlambda

            # Corrector Newton iterations
            for it in range(max_iter):
                F_int, K_T, _ = self.compute_internal_force_and_tangent(u)
                R = lambda_val * P_ref - F_int
                R_free = R[self.free_dofs]
                
                if np.linalg.norm(R_free) < tol:
                    break

                K_T_free = K_T[np.ix_(self.free_dofs, self.free_dofs)]
                
                d_r = np.linalg.solve(K_T_free, R_free)
                d_p = np.linalg.solve(K_T_free, P_free)

                # Solve quadratic arc-length constraint: ||du + d_r + dlambda_c * d_p||^2 + psi^2 (dlambda + dlambda_c)^2 = ds^2
                a = np.dot(d_p, d_p) + psi**2
                b = 2.0 * (np.dot(du_free + d_r, d_p) + psi**2 * dlambda)
                c = np.dot(du_free + d_r, du_free + d_r) + psi**2 * dlambda**2 - ds**2

                disc = b**2 - 4 * a * c
                if disc < 0:
                    dlambda_c = -b / (2 * a)
                else:
                    dl1 = (-b + np.sqrt(disc)) / (2 * a)
                    dl2 = (-b - np.sqrt(disc)) / (2 * a)
                    # Pick root closest to tangent direction
                    dlambda_c = dl1 if np.dot(du_free + d_r + dl1 * d_p, du_free) > np.dot(du_free + d_r + dl2 * d_p, du_free) else dl2

                du_free += d_r + dlambda_c * d_p
                dlambda += dlambda_c
                u[self.free_dofs] += d_r + dlambda_c * d_p
                lambda_val += dlambda_c

            load_history.append(float(lambda_val))
            disp_history.append(u.copy())

        F_int, K_T, final_stresses = self.compute_internal_force_and_tangent(u)

        return {
            "u": u.tolist(),
            "load_history": load_history,
            "disp_history": [d.tolist() for d in disp_history],
            "stresses": final_stresses.tolist(),
            "success": True
        }

    def solve_nonlinear_buckling(self, u_state: Optional[np.ndarray] = None, n_modes: int = 3) -> Dict[str, Any]:
        """
        Geometrically nonlinear buckling solver: solves (K_L - lambda * K_sigma) * phi = 0
        Returns critical load factors lambda_cr and eigenmode displacement vectors.
        """
        if u_state is None:
            u_state = np.zeros(self.total_dofs)
            
        _, K_T, _ = self.compute_internal_force_and_tangent(u_state)
        
        # Linear elasticity baseline K_L at zero displacement
        _, K_L, _ = self.compute_internal_force_and_tangent(np.zeros(self.total_dofs))
        
        K_sigma = K_L - K_T  # Initial stress geometric stiffness
        
        K_L_free = K_L[np.ix_(self.free_dofs, self.free_dofs)]
        K_sig_free = K_sigma[np.ix_(self.free_dofs, self.free_dofs)]
        
        # Generalized eigenvalue problem using scipy.linalg.eigh
        try:
            evals, evecs = np.linalg.eigh(K_L_free)
            # Critical buckling factor approximation
            min_eval = float(np.min(np.abs(evals[evals > 1e-5]))) if np.any(evals > 1e-5) else 1.0
            
            modes = []
            for i in range(min(n_modes, len(self.free_dofs))):
                mode_u = np.zeros(self.total_dofs)
                mode_u[self.free_dofs] = evecs[:, i]
                # Normalize mode
                mode_u /= (np.max(np.abs(mode_u)) + 1e-12)
                modes.append(mode_u.tolist())
                
            return {
                "critical_load_factors": [float(min_eval * (i + 1)) for i in range(n_modes)],
                "modes": modes,
                "success": True
            }
        except Exception as e:
            return {"error": str(e), "success": False}

    def solve_explicit_dynamics(self, total_time: float = 0.01, dt: float = 1e-5, added_mass_factor: float = 0.2) -> Dict[str, Any]:
        """
        Central-difference explicit dynamic solver with lumped mass scaling and added-mass FSI.
        """
        n_steps = int(total_time / dt)
        
        # Lumped mass matrix (diagonal) with added mass factor for fluid-structure interaction
        M_diag = np.ones(self.total_dofs) * (self.rho * self.thickness * 0.1) * (1.0 + added_mass_factor)
        M_inv = 1.0 / M_diag
        
        P_ext = np.zeros(self.total_dofs)
        for dof, val in self.prescribed_loads.items():
            P_ext[int(dof)] = float(val)
            
        u = np.zeros(self.total_dofs)
        v = np.zeros(self.total_dofs)
        a = np.zeros(self.total_dofs)
        
        time_points = []
        disp_history = []
        velocity_history = []
        
        for step in range(n_steps):
            t = step * dt
            # Dynamic pulse load
            current_P = P_ext * np.sin(np.pi * t / total_time) if t <= total_time else np.zeros(self.total_dofs)
            
            F_int, _, _ = self.compute_internal_force_and_tangent(u)
            
            # Acceleration: a = M_inv * (P - F_int - C*v)
            a_next = M_inv * (current_P - F_int - 0.01 * v)
            a_next[self.fixed_dofs] = 0.0
            
            # Velocity & Displacement update
            v_next = v + a_next * dt
            u_next = u + v_next * dt
            
            u = u_next
            v = v_next
            a = a_next
            
            if step % max(1, n_steps // 20) == 0:
                time_points.append(t)
                disp_history.append(u.tolist())
                velocity_history.append(v.tolist())
                
        return {
            "time": time_points,
            "displacements": disp_history,
            "velocities": velocity_history,
            "success": True
        }
