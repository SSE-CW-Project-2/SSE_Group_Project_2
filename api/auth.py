import requests
from google.oauth2 import service_account  # type: ignore
from google.auth.transport.requests import Request  # type: ignore
import os
import json


def get_token():
    service_account_json_string = os.environ.get("SERVICE_ACCOUNT_JSON")
    if service_account_json_string is None:
        sa_dict = {
            "type": "service_account",
            "project_id": os.environ.get("PROJECT_ID"),
            "private_key_id": os.environ.get("PRIVATE_KEY_ID"),
            "private_key": os.environ.get("PRIVATE_KEY"),
            "client_email": os.environ.get("CLIENT_EMAIL"),
            "client_id": os.environ.get("CLIENT_ID"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": os.environ.get("CLIENT_X509_CERT_URL"),
            "universe_domain": "googleapis.com",
        }
        private_key = sa_dict["private_key"]
        private_key = private_key.replace("\\n", "\n")
        sa_dict["private_key"] = private_key
        service_account_json_string = json.dumps(sa_dict)
        print(sa_dict)
    service_account_info = json.loads(service_account_json_string)
    credentials = service_account.IDTokenCredentials.from_service_account_info(
        service_account_info,
        target_audience=os.environ.get("GATEWAY_HOST"),
    )
    credentials.refresh(Request())
    return credentials.token


def make_jwt_request(signed_jwt, endpoint_path, request, request_type="POST", raise_for_status=False):
    host = os.environ.get("GATEWAY_HOST")
    """Makes an authorized request to the endpoint"""

    headers = {
        "Authorization": f"Bearer {signed_jwt}",
        "content-type": "application/json",
    }
    url = f"{host}{endpoint_path}"
    if request_type == "GET":
        response = requests.get(url, headers=headers, params=request)
    elif request_type == "POST":
        response = requests.post(url, headers=headers, json=request)
    elif request_type == "PUT":
        response = requests.put(url, headers=headers, json=request)
    elif request_type == "DELETE":
        response = requests.delete(url, headers=headers, json=request)
    else:
        raise ValueError(f"Unsupported request_type: {request_type}")
    if raise_for_status:
        response.raise_for_status()
    else:
        if response.status_code != 200:
            return response.status_code, response.text
    return response.status_code, response.json()


def make_authorized_request(endpoint_path, request, request_type="POST", raise_for_status=False):
    token = get_token()
    return make_jwt_request(token, endpoint_path, request, request_type, raise_for_status=raise_for_status)


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
