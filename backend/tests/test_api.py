"""
Unit tests for FastAPI endpoints in fea.api.
"""

from fastapi.testclient import TestClient
import pytest
from fea.api.app import app

client = TestClient(app)


def test_root_endpoints():
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["service"] == "Nonlinear FEA Studio"
    
    res_api = client.get("/api")
    assert res_api.status_code == 200


def test_create_and_get_model():
    model_payload = {
        "id": "test_cantilever_01",
        "nodes": [[0.0, 0.0], [1.0, 0.0], [1.0, 0.5], [0.0, 0.5]],
        "elements": [[0, 1, 2, 3]],
        "materials": {"E": 210e9, "nu": 0.3, "thickness": 0.01, "density": 7850.0},
        "bcs": {"fixed_dofs": [0, 1, 6, 7], "prescribed_loads": {"3": -10000.0}}
    }
    
    res = client.post("/models", json=model_payload)
    assert res.status_code == 200
    assert res.json()["status"] == "created"
    assert res.json()["model_id"] == "test_cantilever_01"
    
    get_res = client.get("/models/test_cantilever_01")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == "test_cantilever_01"
    
    # 404 for non-existent model
    not_found = client.get("/models/non_existent_model_id")
    assert not_found.status_code == 404


def test_solve_endpoints():
    # Test solve execution for various types
    solve_types = [
        "nonlinear_static",
        "arc_length",
        "buckling",
        "explicit",
        "topopt",
        "homogenization",
        "fatigue"
    ]
    
    for stype in solve_types:
        solve_payload = {
            "model_id": "test_cantilever_01",
            "solve_type": stype,
            "params": {"n_steps": 3, "max_iter": 3, "total_time": 0.001}
        }
        res = client.post("/solves", json=solve_payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "completed"
        solve_id = data["solve_id"]
        
        # Retrieve solve result
        res_detail = client.get(f"/solves/{solve_id}/result")
        assert res_detail.status_code == 200
        assert res_detail.json()["solve_id"] == solve_id
    
    # 404 for unknown solve id
    bad_solve = client.get("/solves/unknown_solve_123/result")
    assert bad_solve.status_code == 404
