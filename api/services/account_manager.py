####################################################################################################
# Project Name: Motive Event Management System
# File: account_manager.py
# Description: This file defines the population of the Firestore when accounts are created, updated
#              and deleted.
#
# Authors:
# Date: 2024-02-14
# Version: 1.0
#
# Notes: This will need to be updated to match the database schemas once they are set up, and then
#        it should be containerised and integrated into the application. Currently, all references
#        to the database and expected JSON requests are placeholders.
####################################################################################################

import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin import auth
from flask import abort, jsonify

# Initialize the Firebase Admin SDK
if not firebase_admin._apps:
    firebase_admin.initialize_app()

db = firestore.client()


required_fields = {
    'venue': ['name', 'location', 'email'],
    'artist': ['name', 'genre', 'email'],
    'customer': ['name', 'email']
}


def create_account(request):
    """
    Creates a new account document in the Firestore if the POST request corresponds to a
    valid account schema.
    """
    # Ensure the request is a POST request with a JSON payload
    if request.method != 'POST':
        return abort(405, description="Method Not Allowed")

    request_json = request.get_json(silent=True)
    if not request_json or 'account_type' not in request_json:
        return abort(400, description="Missing or invalid JSON payload")

    account_type = request_json['account_type']
    valid_account_types = ['venue', 'artist', 'customer']

    # Validate account type
    if account_type not in valid_account_types:
        return abort(400, description="Invalid account type")

    # Validate that account does not already exist for this email
    email = request_json['email']
    if check_account_exists(email):
        return jsonify({'success': False, 'message': 'Account with this email already exists'}), 409

    # Validate payload based on account type
    if not validate_payload(request_json, account_type):
        return abort(400, description="Invalid payload for account type")

    # Create account in Firestore
    try:
        account_data = {key: value for key, value in request_json.items() if key != 'account_type'}
        doc_ref = db.collection(account_type + 's').add(account_data)  # e.g., 'venues', 'artists', 'customers'
        return jsonify({'success': True, 'id': doc_ref[1].id}), 200
    except Exception as e:
        return abort(500, description=f"Failed to create account: {e}")


def delete_account(request):
    """
    Removes account details from the Firestore database.
    """
    user_uid = authenticate_request(request)
    if not user_uid:
        return abort(403, description="Unauthorized: No valid ID token provided.")

    request_json = request.get_json(silent=True)
    if not request_json or 'email' not in request_json or 'account_type' not in request_json:
        return abort(400, description="Missing required fields in JSON payload")

    email = request_json['email']
    account_type = request_json['account_type']

    account_ref = check_account_exists(email)
    if not account_ref or account_ref.parent.id != account_type + 's':
        return jsonify({'success': False, 'message': 'No matching account found'}), 404

    account_ref.delete()
    return jsonify({'success': True, 'email': email}), 200


def update_account(request):
    """
    Modifies one or more fields in an existing account, but cannot add new fields
    """
    user_uid = authenticate_request(request)
    if not user_uid:
        return abort(403, description="Unauthorized: No valid ID token provided.")

    request_json = request.get_json(silent=True)
    if not request_json or 'email' not in request_json or 'account_type' not in request_json:
        return abort(400, description="Missing required fields in JSON payload")

    email = request_json['email']
    account_type = request_json['account_type']
    update_data = {k: v for k, v in request_json.items() if k in required_fields[account_type]}

    account_ref = check_account_exists(email)
    if not account_ref or account_ref.parent.id != account_type + 's':
        return jsonify({'success': False, 'message': 'No matching account found'}), 404

    account_ref.update(update_data)
    return jsonify({'success': True, 'email': email}), 200


def validate_payload(payload, account_type):
    """
    Checks whether the JSON in the received POST request corresponds to a valid account type.
    """
    # Check for missing fields
    for field in required_fields[account_type]:
        if field not in payload:
            return False
    return True


def check_account_exists(email):
    """
    Before performing an account management operation, checks to see that data is not being
    incorrectly ignored or overwritten.
    """
    collections = ['venues', 'artists', 'customers']
    for collection_name in collections:
        docs = db.collection(collection_name).where('email', '==', email).limit(1).get()
        if docs:
            return True  # Account found
    return False  # No account found


def authenticate_request(request):
    """
    Verify a user's access token before allowing them to make major changes to an account
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None  # No token found, unauthenticated request

    id_token = auth_header.split('Bearer ')[1]
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token['uid']  # Return the user's UID for further use
    except auth.InvalidIdTokenError:
        return None