from app import app
import pytest

# Replace these with more secure user info
sample_venue_data = {
    "username": "venue",
    "password": "password",
    "user_id": 1,
}

sample_customer_data = {
    "username": "customer",
    "password": "password",
    "user_id": 1,
}


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_home_page_exists(client):
    # Navigate to the home page and check it loads properly
    response = client.get("/")
    assert b"Home" in response.data, "Home page didn't load"


def test_must_be_logged_in_to_see_events(client):
    # Events page which should redirect to login if not logged in
    response = client.get("/events", follow_redirects=True)
    assert b"Login" in response.data, "Did not redirect to login"


def test_login_works(client):
    sample_venue_data["next"] = "/events"
    response = client.post("/login", data=sample_venue_data, follow_redirects=True)
    assert b"Events" in response.data, "Did not redirect from login page"


def test_can_buy_as_customer(client):
    # Log in as a customer
    client.post("/login", data=sample_customer_data, follow_redirects=True)
    response = client.post("/buy/1", follow_redirects=True)
    # Now attempt to make a purchase
    assert b"Buy" in response.data, "Was not able to buy as customer"


def test_cannot_buy_as_venue(client):
    client.post("/login", data=sample_venue_data, follow_redirects=True)
    response = client.post("/buy/1", follow_redirects=True)
    # Now attempt to make a purchase
    assert b"Buy" not in response.data, "Was able to buy as venue"


# Note: The sample venue data user owns events 1 and 3
def test_can_manage_event_as_venue_with_correct_id(client):
    client.post("/login", data=sample_venue_data, follow_redirects=True)
    response = client.post("/manage/1", follow_redirects=True)
    assert b"Manage" in response.data, "Was not able to manage with correct id"


# Note: The sample venue data user owns events 1 and 3
def test_cannot_manage_event_with_incorrect_id(client):
    client.post("/login", data=sample_venue_data, follow_redirects=True)
    response = client.post("/manage/2", follow_redirects=True)
    assert b"Manage" not in response.data, "Was able to manage with incorrect id"


# Note: The sample venue data user owns events 1 and 3
def test_can_delete_event_with_correct_id(client):
    client.post("/login", data=sample_venue_data, follow_redirects=True)
    response = client.post("/delete/1", follow_redirects=True)
    assert b"Date" in response.data, "Was not able to delete with correct id"


# Note: The sample venue data user owns events 1 and 3
def test_cannot_delete_event_with_incorrect_id(client):
    client.post("/login", data=sample_venue_data, follow_redirects=True)
    response = client.post("/delete/2", follow_redirects=True)
    assert b"Date" not in response.data, "Was able to delete with incorrect id"
