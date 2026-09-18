"""
J2 Elastoplasticity and Continuum Damage Mechanics Module.
Implements:
1. Von Mises J2 yield surface with radial return mapping.
2. Isotropic and kinematic hardening modules.
3. Lemaitre continuum damage mechanics model dD/dt driving stiffness degradation.
"""

from typing import Dict, Tuple, Any
import numpy as np


class J2PlasticityDamageModel:
    def __init__(self, E: float = 210e9, nu: float = 0.3, sig_y0: float = 250e6, 
                 H_iso: float = 1e9, H_kin: float = 0.0, 
                 S_damage: float = 2.0e6, s_exponent: float = 1.0, D_crit: float = 0.99):
        """
        E: Young's Modulus
        nu: Poisson ratio
        sig_y0: Initial yield stress
        H_iso: Isotropic hardening modulus
        H_kin: Kinematic hardening modulus
        S_damage, s_exponent: Lemaitre damage parameters
        D_crit: Critical damage threshold
        """
        self.E0 = float(E)
        self.nu = float(nu)
        self.sig_y0 = float(sig_y0)
        self.H_iso = float(H_iso)
        self.H_kin = float(H_kin)
        self.S_damage = float(S_damage)
        self.s_exponent = float(s_exponent)
        self.D_crit = float(D_crit)

        # Lame constants
        self.mu = self.E0 / (2.0 * (1.0 + self.nu))
        self.K_bulk = self.E0 / (3.0 * (1.0 - 2.0 * self.nu))

    def return_mapping_2d(self, strain_inc: np.ndarray, state_var: Dict[str, Any]) -> Tuple[np.ndarray, Dict[str, Any], np.ndarray]:
        """
        Radial return algorithm for 2D plane strain / plane stress.
        strain_inc: [deps_xx, deps_yy, dgamma_xy]
        state_var: Dict with 'eps_p' (eff plastic strain), 'alpha' (backstress), 'damage' (D)
        Returns: updated stress [sig_xx, sig_yy, sig_xy], updated state_var, consistent elastoplastic tangent Cep
        """
        eps_p = float(state_var.get("eps_p", 0.0))
        alpha = np.array(state_var.get("alpha", [0.0, 0.0, 0.0]))
        D = float(state_var.get("damage", 0.0))

        # Damaged elastic modulus
        E_eff = (1.0 - D) * self.E0
        mu_eff = E_eff / (2.0 * (1.0 + self.nu))

        # Elastic trial stress
        factor = E_eff / (1.0 - self.nu**2)
        C_e = factor * np.array([
            [1.0, self.nu, 0.0],
            [self.nu, 1.0, 0.0],
            [0.0, 0.0, 0.5 * (1.0 - self.nu)]
        ])

        prev_stress = np.array(state_var.get("stress", [0.0, 0.0, 0.0]))
        trial_stress = prev_stress + C_e @ strain_inc

        # Deviatoric trial stress
        sig_m = (trial_stress[0] + trial_stress[1]) / 3.0
        s_trial = np.array([
            trial_stress[0] - sig_m - alpha[0],
            trial_stress[1] - sig_m - alpha[1],
            trial_stress[2] - alpha[2]
        ])

        # Equivalent von Mises trial stress
        s_norm = np.sqrt(s_trial[0]**2 + s_trial[1]**2 + 2.0 * s_trial[2]**2)
        seq_trial = np.sqrt(1.5) * s_norm

        # Yield criterion: f = seq_trial - (sig_y0 + H_iso * eps_p)
        current_sig_y = self.sig_y0 + self.H_iso * eps_p
        f_trial = seq_trial - current_sig_y

        if f_trial <= 0.0:
            # Purely elastic step
            updated_stress = trial_stress
            updated_eps_p = eps_p
            updated_alpha = alpha
            C_ep = C_e
        else:
            # Plastic return mapping
            d_gamma = f_trial / (3.0 * mu_eff + self.H_iso + self.H_kin)
            
            # Flow direction N = s_trial / s_norm
            N_flow = s_trial / (s_norm + 1e-12)
            
            # Stress correction
            updated_stress = trial_stress - 2.0 * mu_eff * d_gamma * np.array([N_flow[0], N_flow[1], N_flow[2]])
            
            # Update internal variables
            updated_eps_p = eps_p + np.sqrt(2.0 / 3.0) * d_gamma
            updated_alpha = alpha + self.H_kin * d_gamma * N_flow
            
            # Algorithmic tangent C_ep
            beta_factor = 2.0 * mu_eff * d_gamma / (s_norm + 1e-12)
            gamma_factor = (3.0 * mu_eff) / (3.0 * mu_eff + self.H_iso + self.H_kin) - beta_factor
            
            C_ep = C_e - (2.0 * mu_eff * gamma_factor) * np.outer(N_flow, N_flow)

        # Lemaitre Continuum Damage Evolution dD = ((Y / S)^s) * deps_p
        # Y = strain energy release rate = seq^2 / (2 * E0 * (1-D)^2)
        seq_curr = np.sqrt(updated_stress[0]**2 - updated_stress[0]*updated_stress[1] + updated_stress[1]**2 + 3.0*updated_stress[2]**2)
        Y_energy = (seq_curr**2) / (2.0 * self.E0 * max(1.0 - D, 0.05)**2 + 1e-12)
        
        dD = ((Y_energy / self.S_damage)**self.s_exponent) * (updated_eps_p - eps_p)
        updated_D = min(self.D_crit, D + dD)

        new_state = {
            "stress": updated_stress.tolist(),
            "eps_p": updated_eps_p,
            "alpha": updated_alpha.tolist(),
            "damage": updated_D,
            "yielded": bool(f_trial > 0.0)
        }

        return updated_stress, new_state, C_ep
