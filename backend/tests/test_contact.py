"""
Unit tests for Augmented-Lagrangian and Penalty Contact Mechanics.
"""

import numpy as np
import pytest
from fea.contact.contact_solver import ContactSolver


def test_contact_gap_detection():
    solver = ContactSolver(penalty_stiffness=1e9, friction_coeff=0.25)
    
    slave_nodes = np.array([
        [0.5, 0.05],  # Penetrating master segment
        [0.5, 0.20],  # No contact
        [1.5, 0.05]   # Outside horizontal span
    ])
    
    # Master segment along y = 0.1 from x = 0 to x = 1.0
    master_segments = np.array([
        [[0.0, 0.1], [1.0, 0.1]]
    ])
    
    u = np.zeros(6)
    active_pairs = solver.detect_active_set_2d(slave_nodes, master_segments, u)
    
    assert len(active_pairs) == 1
    assert active_pairs[0]["slave_node"] == 0
    assert active_pairs[0]["gap_n"] < 0.0
    assert active_pairs[0]["penetration"] > 0.0


def test_augmented_lagrangian_forces():
    solver = ContactSolver(penalty_stiffness=1e8)
    
    active_pairs = [
        {
            "slave_node": 0,
            "master_segment": 0,
            "gap_n": -0.01,
            "normal": [0.0, 1.0],
            "tangent": [1.0, 0.0],
            "penetration": 0.01
        }
    ]
    
    F_contact, multipliers = solver.compute_augmented_lagrangian_contact(active_pairs, dof_per_node=2)
    
    assert len(multipliers) == 1
    assert multipliers[0] > 0.0
    assert F_contact[1] > 0.0  # Upward normal force on y-dof
