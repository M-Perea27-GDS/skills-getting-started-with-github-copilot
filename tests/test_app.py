import copy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app

client = TestClient(app)
original_activities = copy.deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the shared activity state before each test."""
    activities.clear()
    activities.update(copy.deepcopy(original_activities))


def test_root_redirects_to_static_index():
    # Arrange: no additional setup beyond the test client
    # Act: request the root endpoint without following redirects
    response = client.get("/", allow_redirects=False)

    # Assert: the API returns a redirect to the index page
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_map():
    # Arrange: expected activity names are taken from the original state
    expected_activity_names = set(original_activities.keys())

    # Act: request the activities endpoint
    response = client.get("/activities")

    # Assert: the full activity map is returned successfully
    assert response.status_code == 200
    assert set(response.json().keys()) == expected_activity_names


def test_signup_for_activity_success():
    # Arrange: select an activity and an email that is not already registered
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"

    # Act: submit a signup request for the chosen activity
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert: the signup succeeds and the participant is added
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for {activity_name}"
    assert email in activities[activity_name]["participants"]


def test_signup_already_signed_up_returns_400():
    # Arrange: choose an activity and an existing participant email
    activity_name = "Chess Club"
    email = original_activities[activity_name]["participants"][0]

    # Act: attempt to sign up the same email again
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert: the API rejects duplicate signups
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"


def test_signup_missing_activity_returns_404():
    # Arrange: choose a non-existing activity name
    activity_name = "Nonexistent Club"
    email = "missingstudent@mergington.edu"

    # Act: attempt to sign up for a missing activity
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert: the API returns a 404 activity not found error
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_participant_success():
    # Arrange: select an activity and an existing participant email
    activity_name = "Chess Club"
    email = original_activities[activity_name]["participants"][0]

    # Act: remove the participant from the activity
    response = client.delete(f"/activities/{activity_name}/participants", params={"email": email})

    # Assert: removal succeeds and the participant is removed from state
    assert response.status_code == 200
    assert response.json()["message"] == f"Removed {email} from {activity_name}"
    assert email not in activities[activity_name]["participants"]


def test_remove_missing_participant_returns_404():
    # Arrange: choose an activity and an email that is not signed up
    activity_name = "Chess Club"
    email = "noone@mergington.edu"

    # Act: attempt to remove a participant that does not exist
    response = client.delete(f"/activities/{activity_name}/participants", params={"email": email})

    # Assert: the API returns a participant not found error
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"


def test_remove_unknown_activity_returns_404():
    # Arrange: choose a non-existing activity name
    activity_name = "No Club"
    email = "student@mergington.edu"

    # Act: attempt to remove a participant from a missing activity
    response = client.delete(f"/activities/{activity_name}/participants", params={"email": email})

    # Assert: the API returns an activity not found error
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
