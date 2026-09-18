"""
Rainflow Cycle Counting and Probabilistic Fatigue Reliability Module.
Implements:
1. ASTM E1049 Rainflow cycle counting algorithm.
2. Palmgren-Miner cumulative fatigue damage law & Basquin S-N curve.
3. Monte Carlo probabilistic fatigue life trajectory beta(t) & Pf(t).
"""

from typing import Dict, List, Tuple, Any
import numpy as np


class RainflowFatigueEngine:
    def __init__(self, A_basquin: float = 1e12, m_basquin: float = 3.0, sig_fatigue_limit: float = 50e6):
        """
        A_basquin, m_basquin: S-N curve parameters N * (delta_sig)^m = A
        sig_fatigue_limit: Fatigue endurance limit threshold below which damage is 0.
        """
        self.A = float(A_basquin)
        self.m = float(m_basquin)
        self.sig_fl = float(sig_fatigue_limit)

    def rainflow_count(self, stress_history: np.ndarray) -> List[Tuple[float, float, float]]:
        """
        ASTM E1049 Rainflow cycle counting algorithm.
        Returns list of (range, mean, count) tuples.
        """
        history = np.array(stress_history, dtype=float)
        if len(history) < 3:
            return []

        # Find local extrema (peaks and troughs)
        extrema = [history[0]]
        for i in range(1, len(history) - 1):
            if (history[i] - history[i-1]) * (history[i+1] - history[i]) < 0:
                extrema.append(history[i])
        extrema.append(history[-1])

        cycles = []
        stack = []
        
        for pt in extrema:
            stack.append(pt)
            while len(stack) >= 3:
                s0, s1, s2 = stack[-3], stack[-2], stack[-1]
                X = abs(s1 - s2)
                Y = abs(s0 - s1)
                
                if X >= Y:
                    # Count cycle or half-cycle
                    range_val = Y
                    mean_val = 0.5 * (s0 + s1)
                    cycles.append((float(range_val), float(mean_val), 1.0))
                    stack.pop(-2)  # Remove s1
                else:
                    break

        # Remaining unclosed residual cycles as half-cycles
        for i in range(len(stack) - 1):
            range_val = abs(stack[i+1] - stack[i])
            mean_val = 0.5 * (stack[i+1] + stack[i])
            cycles.append((float(range_val), float(mean_val), 0.5))

        return cycles

    def compute_cumulative_damage(self, cycles: List[Tuple[float, float, float]]) -> float:
        """
        Palmgren-Miner cumulative damage D = sum(n_i / N_i).
        N_i = A / (delta_sig_i)^m
        """
        total_damage = 0.0
        for range_val, mean_val, count in cycles:
            if range_val <= self.sig_fl:
                continue
            N_allowable = self.A / (range_val**self.m + 1e-12)
            total_damage += count / N_allowable
            
        return float(total_damage)

    def run_probabilistic_fatigue_simulation(self, base_stress_history: np.ndarray, 
                                             years: float = 25.0, 
                                             n_samples: int = 500) -> Dict[str, Any]:
        """
        Monte Carlo simulation introducing stochastic variability in load magnitude & S-N parameters
        to compute fatigue reliability index trajectory beta(t) and probability of failure Pf(t).
        """
        cycles_base = self.rainflow_count(base_stress_history)
        base_annual_damage = self.compute_cumulative_damage(cycles_base) * 365.0 * 100.0  # Normalized yearly blocks
        
        time_years = np.linspace(1.0, years, 25)
        beta_t = []
        Pf_t = []

        # Generate Monte Carlo realizations for Basquin A coefficient & load variability
        rng = np.random.default_rng(42)
        A_samples = rng.lognormal(mean=np.log(self.A), sigma=0.25, size=n_samples)
        load_factors = rng.normal(loc=1.0, scale=0.15, size=n_samples)

        for yr in time_years:
            # Accumulated damage for each sample at year yr
            damages = (base_annual_damage * (load_factors**self.m)) * yr / A_samples
            
            # Failure criterion: Limit state function g = 1.0 - D <= 0
            failures = np.sum(damages >= 1.0)
            pf = float(failures / n_samples)
            
            # Reliability index beta = -Phi^-1(Pf)
            if pf <= 0.0:
                beta = 4.5
            elif pf >= 1.0:
                beta = -3.0
            else:
                from scipy.stats import norm
                beta = float(-norm.ppf(pf))
                
            Pf_t.append(pf)
            beta_t.append(beta)

        return {
            "time_years": time_years.tolist(),
            "beta_t": beta_t,
            "Pf_t": Pf_t,
            "annual_base_damage": base_annual_damage,
            "success": True
        }
