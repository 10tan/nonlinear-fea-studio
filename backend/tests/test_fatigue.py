"""
Unit tests for ASTM E1049 Rainflow Cycle Counting and Fatigue Reliability.
"""

import numpy as np
import pytest
from fea.fatigue.fatigue_engine import RainflowFatigueEngine


def test_rainflow_cycle_counting():
    engine = RainflowFatigueEngine(A_basquin=1e12, m_basquin=3.0, sig_fatigue_limit=10.0)
    
    # Stress history with known reversals
    stress_history = np.array([0.0, 100.0, -50.0, 150.0, -100.0, 50.0, 0.0])
    cycles = engine.rainflow_count(stress_history)
    
    assert len(cycles) > 0
    # Every cycle should have range, mean, count
    for rng, mean, count in cycles:
        assert rng >= 0.0
        assert count in (0.5, 1.0)


def test_palmgren_miner_damage():
    engine = RainflowFatigueEngine(A_basquin=1e12, m_basquin=3.0, sig_fatigue_limit=20.0)
    
    cycles = [
        (100.0, 0.0, 1.0),
        (50.0, 10.0, 1.0),
        (15.0, 0.0, 1.0)  # Below endurance limit
    ]
    
    damage = engine.compute_cumulative_damage(cycles)
    assert damage > 0.0
    # Expected damage = 1.0 / (1e12 / 100^3) + 1.0 / (1e12 / 50^3)
    expected_d = (100.0**3) / 1e12 + (50.0**3) / 1e12
    assert np.isclose(damage, expected_d)


def test_probabilistic_fatigue_simulation():
    engine = RainflowFatigueEngine(A_basquin=1e12, m_basquin=3.0, sig_fatigue_limit=10.0)
    stress_history = np.sin(np.linspace(0, 10 * np.pi, 100)) * 120.0
    
    res = engine.run_probabilistic_fatigue_simulation(stress_history, years=10.0, n_samples=100)
    
    assert "time_years" in res
    assert "beta_t" in res
    assert "Pf_t" in res
    assert len(res["time_years"]) == 25
    assert len(res["beta_t"]) == 25
