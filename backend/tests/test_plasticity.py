"""
Unit tests for J2 Plasticity and Lemaitre Continuum Damage Mechanics.
"""

import numpy as np
import pytest
from fea.plasticity.j2_plasticity import J2PlasticityDamageModel


def test_elastic_trial_state():
    model = J2PlasticityDamageModel(E=200e9, nu=0.3, sig_y0=250e6)
    
    # Very small elastic strain increment
    strain_inc = np.array([1e-5, 0.0, 0.0])
    state_var = {"eps_p": 0.0, "alpha": [0.0, 0.0, 0.0], "damage": 0.0, "stress": [0.0, 0.0, 0.0]}
    
    stress, new_state, C_ep = model.return_mapping_2d(strain_inc, state_var)
    
    assert not new_state["yielded"]
    assert new_state["eps_p"] == 0.0
    assert new_state["damage"] == 0.0
    assert stress[0] > 0.0
    assert C_ep.shape == (3, 3)


def test_plastic_yielding_and_hardening():
    model = J2PlasticityDamageModel(
        E=200e9, nu=0.3, sig_y0=250e6, 
        H_iso=2e9, H_kin=1e9, 
        S_damage=5e6, s_exponent=1.0
    )
    
    # Large strain increment driving substantial plastic yield
    strain_inc = np.array([5e-3, -1.5e-3, 0.0])
    state_var = {"eps_p": 0.0, "alpha": [0.0, 0.0, 0.0], "damage": 0.0, "stress": [0.0, 0.0, 0.0]}
    
    stress, new_state, C_ep = model.return_mapping_2d(strain_inc, state_var)
    
    assert new_state["yielded"]
    assert new_state["eps_p"] > 0.0
    assert new_state["damage"] > 0.0
    assert np.any(np.array(new_state["alpha"]) != 0.0)
    assert C_ep.shape == (3, 3)
    
    # Check that consecutive plastic step accumulates hardening and damage
    strain_inc_2 = np.array([2e-3, -0.6e-3, 0.0])
    stress_2, new_state_2, _ = model.return_mapping_2d(strain_inc_2, new_state)
    assert new_state_2["eps_p"] > new_state["eps_p"]
    assert new_state_2["damage"] >= new_state["damage"]
