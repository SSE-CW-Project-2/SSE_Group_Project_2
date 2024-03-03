import time
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request
import os
import json

# Load the service account JSON string from environment variables
service_account_json_string = os.environ.get('SERVICE_ACCOUNT_JSON')

# If the environment variable is not found, this will be None
if service_account_json_string is None:
    raise ValueError("SERVICE_ACCOUNT_JSON environment variable is not set")

# Convert the JSON string to a dictionary
service_account_info = json.loads(service_account_json_string)

# Configure these variables with your own values
host = "https://see-project-gateway-c4vspufr.uc.gateway.dev"
endpoint_path = "/create_account"
API_URL = f"{host}{endpoint_path}"
AUDIENCE = 'https://see-project-gateway-c4vspufr.uc.gateway.dev'

def get_token():
    # Use the already loaded service account info to create ID token credentials
    credentials = service_account.IDTokenCredentials.from_service_account_info(
        service_account_info,
        target_audience=AUDIENCE,
    )

    # Obtain an OAuth2 access token using the JWT
    credentials.refresh(Request())
    return credentials.token

def make_jwt_request(signed_jwt, url=API_URL):
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
    response = requests.post(url, headers=headers, json=request)
    print(response.status_code, response.content)
    response.raise_for_status()

# Obtain token
token = get_token()

# Make authorized JWT request
make_jwt_request(token)
