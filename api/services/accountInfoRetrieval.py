####################################################################################################
# Project Name: Motive Event Management System
# Course: COMP70025 - Software Systems Engineering
# File: accountInfoRetrieval.py
# Description: This file defines functions used to check whether an email is already registered and
#              retrieve account information from the user information database.
#
# Authors: James Hartley, Ankur Desai, Patrick Borman, Julius Gasson, and Vadim Dunaevskiy
# Date: 2024-02-17
# Version: 2.0
#
# Notes: Migrated to SQL Supabase database. App routes need to be updated.
####################################################################################################


from flask import Flask, request, jsonify
from supabase import create_client, Client
from dotenv import load_dotenv
import os, re

app = Flask(__name__)

# Create a Supabase client
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_PRIVATE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# Schema for request validation
account_types = ['venue', 'artist', 'attendee']
account_type_schema = {'venue': ['email', 'username', 'user_id', 'location'],
                       'artist': ['email', 'username', 'user_id', 'genre'],
                       'attendee': ['email', 'username', 'user_id', 'city']}


def validate_request(request, account_type_schema, account_type):
    """
    Validate the request against the account type schema.

    Args:
        request: A dictionary with 'email' and 'attributes'.
        account_type_schema: A dictionary representing valid fields for an account type.
        account_type: A string corresponding to one of the rows in the account_type_schema

    Returns:
        A tuple (bool, str) indicating if the request is valid and a message.
    """
    email = request.get('email')
    if not email or not is_valid_email(email):
        return False, "Invalid or missing email."

    if account_type not in account_types:
        return False, "Invalid account type specified."

    requested_attributes = request.get('attributes', {})
    invalid_attrs = [attr for attr in requested_attributes if attr not in account_type_schema[account_type]]
    if invalid_attrs:
        return False, f"Invalid attributes requested: {', '.join(invalid_attrs)}."

    return True, "Request is valid."


def is_valid_email(email):
    """
    Basic email format validation to help protect against injection attacks.

    Args:
        A string containing the email address being checked.

    Returns:
        True if the string is a valid email address, else false.
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def check_email_in_use(email):
    """
    Checks if an email is registered in any of the 'venues', 'artists', or 'attendees' tables with a
        single SQL query.

    Args:
        email: A string containing the email address being checked.

    Returns:
        A dictionary with either the user_id if found, a not-in-use message if not found, or an
            error message.
    """
    # Guard against injection attacks in case third party authentication not implemented properly
    if not is_valid_email(email):
        return {'error': "Invalid email format."}

    try:
        # Executing the raw SQL query
        data = supabase.rpc("check_email_in_use", {"input_email": email}).execute()

        # Check if any data was returned
        if data.data:
            # Assuming user_id is unique across all tables and found an entry
            return {'account_type': data.data[0]['account_type'], 'user_id': data.data[0]['user_id']}
        else:
            # If no data is found, the email is not in use
            return {'message': "Email is not in use."}
    except Exception as e:
        # Handle any exception that might occur during the API call
        return {'error': f"An error occurred: {str(e)}"}


def fetch_account_info(request):
    """
    Fetches specified account information based on a validated request.

    Args:
        request: A dictionary containing 'email' and 'attributes' where each attribute is a boolean.

    Returns:
        A dictionary with requested data or an error message.
    """
    account_type = request.get('account type')
    email = request['email']
    attributes_to_fetch = [attr for attr, include in request.get('attributes', {}).items() if include]

    valid, message = validate_request(request, account_type_schema, account_type)
    if not valid:
        return {'error': message}

    # Construct the attributes string for the query
    attributes = ', '.join(attributes_to_fetch)

    try:
        data = supabase.table(account_type + "s").select(attributes).eq("email", email).execute()
        if data.data:
            return {'in_use': True, 'message': 'Email is already registered with user', 'data': data.data[0]}
        else:
            return {'in_use': False, 'message': "Email is not in use."}
    except Exception as e:
        return {'error': f"An API error occurred: {str(e)}"}


@app.route('/fetch_account_info', methods=['POST'])
def api_fetch_account_info():
    req_data = request.get_json()

    # Check a valid payload was received
    if not req_data:
        return jsonify({'error': 'Invalid or missing JSON payload'}), 400

    # Call function
    result = fetch_account_info(req_data)

    # Handle outcomes
    if 'error' in result:
        # Return 404 if account not found, or 500 for all other errors in reaching the database
        return (jsonify(result), 404 if result['error'] ==
                                        "No account found for the provided email." else 500)

    return jsonify(result)


@app.route('/check_email_in_use', methods=['POST'])
def api_check_email_in_use():
    req_data = request.get_json()

    # Check that an email string has been received
    if not req_data or 'email' not in req_data:
        return jsonify({'error': 'Invalid or missing email in JSON payload'}), 400

    # Function call
    email = req_data['email']
    result = check_email_in_use(email)

    # Handle the possible outcomes
    if 'error' in result:
        # Return 500 status code (internal server error)
        return jsonify(result), 500
    else:
        # Return result of the email check
        return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True)
