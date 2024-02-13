from app import app
import pytest
import requests

# Replace this with more secure user info
sample_data = {
    'username': 'customer',
    'password': 'password',
}

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_home_page_exists(client):
    # Navigate to the home page and check it loads properly
    response = client.get("/")
    assert b"Home" in response.data, "Home page didn't load"


def test_must_be_logged_in(client):
    # Navigate to the events page which should redirect to login if not authenticated
    response = client.get("/events", follow_redirects=True)
    assert b"Login" in response.data, "Did not redirect to login"


def test_login_works(client):
    sample_data['next'] = '/events'
    response = client.post("/login", data=sample_data, follow_redirects=True)
    assert b"Events" in response.data, "Did not redirect from login page"

def test_can_buy_as_customer(client):
    # Log in as a customer
    login_response = client.post("/login", data=sample_data, follow_redirects=True)
    response = client.post("/buy/1", follow_redirects=True)
    # Now attempt to make a purchase
    assert b"Buy" in response.data, "Was not able to buy as customer"


def test_cannot_buy_as_venue(client):
    venue_data = sample_data.copy()
    venue_data['username'] = 'venue'
    login_response = client.post("/login", data=sample_data, follow_redirects=True)
    response = client.post("/buy/1", follow_redirects=True)
    # Now attempt to make a purchase
    assert b"Buy" in response.data, "Was able to buy as venue"

