import os
import tempfile

from app import app
from algorithm.coloring import greedy_graph_coloring


def test_greedy_coloring_assigns_unique_colors_to_conflicts():
    adjacency = {
        1: {2, 3},
        2: {1, 3},
        3: {1, 2, 4},
        4: {3},
    }
    result = greedy_graph_coloring(adjacency, [1, 2, 3, 4])
    assert result[1] != result[2]
    assert result[1] != result[3]
    assert result[2] != result[3]
    assert result[3] != result[4]


def test_dashboard_route_works():
    client = app.test_client()
    response = client.get('/')
    assert response.status_code == 200
    assert b'Smart Exam' in response.data


def test_graph_renders_all_subjects_and_assigns_isolated_subject(monkeypatch):
    subjects = [
        {"id": subject_id, "code": f"CSC-{200 + subject_id}", "name": f"Subject {subject_id}"}
        for subject_id in range(1, 7)
    ]
    adjacency = {
        1: {2},
        2: {1, 3},
        3: {2, 4},
        4: {3, 5},
        5: {4},
        6: set(),
    }
    subject_order = [subject["id"] for subject in subjects]
    monkeypatch.setattr("app.fetch_subjects", lambda: subjects)
    monkeypatch.setattr(
        "app.build_conflict_map",
        lambda _subjects: (adjacency, subject_order),
    )
    monkeypatch.setattr("app.fetch_enrollments", lambda: [])
    monkeypatch.setattr("app.get_conflict_pairs", lambda *_args: [])

    response = app.test_client().get("/graph")

    assert response.status_code == 200
    assert response.data.count(b'class="graph-node color-') == 6
    assert response.data.count(b'class="dot color-') == 6
    assert b'class="graph-node color-0"' in response.data
    assert b'CSC-206 : Slot 1' in response.data
