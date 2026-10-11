"""
Unit tests for Zienkiewicz-Zhu Adaptive Mesh Refinement (AMR).
"""

import numpy as np
import pytest
from fea.amr.adaptive_mesh import AdaptiveMeshRefinement


def test_superconvergent_patch_recovery():
    amr = AdaptiveMeshRefinement(target_error_pct=5.0)
    
    # 2-element mesh sharing nodes 1 and 4
    # 0---1---2
    # |   |   |
    # 3---4---5
    nodes = np.array([
        [0.0, 1.0], [1.0, 1.0], [2.0, 1.0],
        [0.0, 0.0], [1.0, 0.0], [2.0, 0.0]
    ])
    elements = np.array([
        [3, 4, 1, 0],
        [4, 5, 2, 1]
    ])
    elem_stresses = np.array([
        [100.0, 20.0, 5.0],
        [120.0, 30.0, 8.0]
    ])
    
    nodal_stresses = amr.recover_superconvergent_stresses(nodes, elements, elem_stresses)
    
    assert nodal_stresses.shape == (6, 3)
    # Shared nodes 1 and 4 should be average of element stresses
    expected_shared_sig_xx = 0.5 * (100.0 + 120.0)
    assert np.isclose(nodal_stresses[1, 0], expected_shared_sig_xx)
    assert np.isclose(nodal_stresses[4, 0], expected_shared_sig_xx)


def test_energy_error_estimation():
    amr = AdaptiveMeshRefinement(target_error_pct=5.0)
    
    nodes = np.array([
        [0.0, 1.0], [1.0, 1.0], [2.0, 1.0],
        [0.0, 0.0], [1.0, 0.0], [2.0, 0.0]
    ])
    elements = np.array([
        [3, 4, 1, 0],
        [4, 5, 2, 1]
    ])
    elem_stresses = np.array([
        [80.0, 10.0, 0.0],
        [200.0, 50.0, 20.0]
    ])
    
    C_inv = np.diag([1e-9, 1e-9, 2e-9])
    
    elem_errors, rel_error_pct, to_refine = amr.estimate_energy_error(nodes, elements, elem_stresses, C_inv)
    
    assert len(elem_errors) == 2
    assert rel_error_pct > 0.0
    assert isinstance(to_refine, list)
