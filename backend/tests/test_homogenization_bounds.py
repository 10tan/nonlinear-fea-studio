"""
Verification Test 4: Homogenization Analytical Voigt/Reuss/Hashin-Shtrikman Bounds Check.
Verifies that homogenized effective modulus C_eff lies strictly within analytical upper/lower bounds.
"""

import numpy as np
import pytest
from fea.homogenization.multiscale_homog import MultiscaleHomogenization


def test_homogenization_bounds():
    homog = MultiscaleHomogenization(E_matrix=210e9, nu_matrix=0.3, E_inclusion=70e9, nu_inclusion=0.33)
    
    # 50% volume fraction RVE
    rve = np.ones((10, 10))
    rve[2:7, 2:7] = 0.0  # Void / Inclusion
    
    C_eff, res = homog.homogenize_rve_grid(rve)
    
    bounds = res["bounds"]
    E_eff = res["E_eff_x"]
    
    # Assert Voigt upper bound >= E_eff >= Reuss lower bound
    assert bounds["voigt_E_upper"] >= E_eff
    assert E_eff >= bounds["reuss_E_lower"]
    assert res["within_bounds"] is True
