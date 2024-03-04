import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request
import os
import json


def get_token():
    service_account_json_string = os.environ.get('SERVICE_ACCOUNT_JSON')
    if service_account_json_string is None:
        raise ValueError("SERVICE_ACCOUNT_JSON environment variable is not set")
    service_account_info = json.loads(service_account_json_string)
    credentials = service_account.IDTokenCredentials.from_service_account_info(
        service_account_info,
        target_audience=os.environ.get('GATEWAY_HOST'),
    )

    credentials.refresh(Request())
    return credentials.token


def make_jwt_request(signed_jwt, endpoint_path, request, request_type="POST"):
    host = os.environ.get('GATEWAY_HOST')
    """Makes an authorized request to the endpoint"""

    headers = {
        "Authorization": f"Bearer {signed_jwt}",
        "content-type": "application/json",
    }
    url = f"{host}{endpoint_path}"
    if request_type == "GET":
        response = requests.get(url, headers=headers)
    elif request_type == "POST":
        response = requests.post(url, headers=headers, json=request)
    elif request_type == "PUT":
        response = requests.put(url, headers=headers, json=request)
    elif request_type == "DELETE":
        response = requests.delete(url, headers=headers, json=request)
    else:
        raise ValueError(f"Unsupported request_type: {request_type}")
    print(response.status_code, response.content)
    response.raise_for_status()
    return response.json()


def make_authorized_request(endpoint_path, request, request_type="POST"):
    token = get_token()
    return make_jwt_request(token, endpoint_path, request, request_type)


if __name__ == "__main__":
    endpoint_path = "/create_account"
    identifier = "127409124712490421790"
    request = {
        "function": "create",
        "object_type": "artist",
        "identifier": identifier,
        "attributes": {
            "user_id": identifier,
            "artist_name": "Test Artist 21",
            "email": "testartist21@example.com",
            # "username": "test21artist",
            "genres": "Jazz",
            "spotify_artist_id": "12345acbabssadl",
            "street_address": "1234 Main St",
            "city": "San Francisco",
            "postcode": "94111",
        },
    }
    result = make_authorized_request(endpoint_path, request)
    print(result)
