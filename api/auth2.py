import time
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request

# Configure these variables with your own values
SERVICE_ACCOUNT_FILE = '../../still-descent-414311-bfe8d7f629c7.json'

host = "https://see-project-gateway-c4vspufr.uc.gateway.dev"
endpoint_path = "/create_account"
API_URL = f"{host}{endpoint_path}"
AUDIENCE = 'https://see-project-gateway-c4vspufr.uc.gateway.dev'

def get_token():

    # Load the service account credentials and create a JWT
    credentials = service_account.IDTokenCredentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        target_audience=AUDIENCE,
    )


    # Obtain an OAuth2 access token using the JWT
    credentials.refresh(Request())
    return credentials.token

host = "https://see-project-gateway-c4vspufr.uc.gateway.dev"
endpoint_path = "/create_account"
full_url = f"{host}{endpoint_path}"

def make_jwt_request(signed_jwt, url=full_url):
    print(signed_jwt)
    """Makes an authorized request to the endpoint"""
    request = {
        "function": "create",
        "object_type": "artist",
        "identifier": "testartist21@example.com",
        "attributes": {
            "email": "testartist21@example.com",
            "username": "test21artist",
            "genre": "Jazz",
        },
    }
    headers = {
        "Authorization": f"Bearer {signed_jwt}",
        "content-type": "application/json",
    }
    response = requests.post(full_url, headers=headers, json=request)
    print(response.status_code, response.content)
    response.raise_for_status()

token = get_token()
make_jwt_request(token, full_url)