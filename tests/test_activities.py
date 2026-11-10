from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    original_activities = deepcopy(activities)
    try:
        with TestClient(app, follow_redirects=False) as test_client:
            yield test_client
    finally:
        activities.clear()
        activities.update(original_activities)


def test_get_activities_returns_data_without_cache(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert "Chess Club" in response.json()
    assert response.headers["cache-control"] == "no-store"


def test_signup_adds_participant(client):
    activity_name = "Art Club"
    email = "new-student@example.com"

    response = client.post(
        f"/activities/{activity_name}/signup", params={"email": email}
    )

    assert response.status_code == 200
    assert email in client.get("/activities").json()[activity_name]["participants"]


def test_signup_returns_404_for_unknown_activity(client):
    response = client.post(
        "/activities/Unknown%20Club/signup", params={"email": "student@example.com"}
    )

    assert response.status_code == 404


def test_signup_returns_400_for_duplicate_participant(client):
    activity_name = "Art Club"
    email = "new-student@example.com"
    url = f"/activities/{activity_name}/signup"

    first_response = client.post(url, params={"email": email})
    duplicate_response = client.post(url, params={"email": email})

    assert first_response.status_code == 200
    assert duplicate_response.status_code == 400


def test_unregister_removes_participant(client):
    activity_name = "Art Club"
    email = "new-student@example.com"
    signup_url = f"/activities/{activity_name}/signup"

    client.post(signup_url, params={"email": email})
    response = client.delete(signup_url, params={"email": email})

    assert response.status_code == 200
    assert email not in client.get("/activities").json()[activity_name]["participants"]


def test_unregister_returns_404_for_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown%20Club/signup", params={"email": "student@example.com"}
    )

    assert response.status_code == 404


def test_unregister_returns_404_for_unregistered_participant(client):
    response = client.delete(
        "/activities/Art%20Club/signup", params={"email": "student@example.com"}
    )

    assert response.status_code == 404


def test_root_redirects_to_frontend(client):
    response = client.get("/")

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"