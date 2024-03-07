from .app import app
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
