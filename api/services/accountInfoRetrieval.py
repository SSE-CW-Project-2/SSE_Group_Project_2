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
from postgrest import APIError
from supabase import create_client, Client
from dotenv import load_dotenv
import os, re

app = Flask(__name__)

# Create a Supabase client
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_PRIVATE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def validate_request(request):
    """
    Checks that a JSON information request is in a valid format, allowing for additional fields that are not required.

    Args:
        request: a dictionary following one of the venue, artist, or attendee templates.

    Returns:
        Tuple[bool, str]: A tuple containing a boolean indicating if the template forms a valid
        request and a string message. If extra fields are included, the message specifies
        which fields will not be used.
    """
    templates = {
        'venue': {'account type', 'email', 'user_id', 'username', 'location'},
        'artist': {'account type', 'email', 'user_id', 'username', 'genre'},
        'attendee': {'account type', 'email', 'user_id', 'username', 'city'}
    }

    account_type = request.get('account type')
    if account_type not in templates:
        return False, "Invalid account type specified."

    required_keys = templates[account_type]
    missing_keys = required_keys - set(request.keys())
    if missing_keys:
        return False, f"Request is missing required keys: {', '.join(missing_keys)}."

    extra_keys = set(request.keys()) - required_keys
    if extra_keys:
        return True, (f"Request is valid. Note: The following fields "
                      f"are not required and will not be used: {', '.join(extra_keys)}.")

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

    # Constructing the SQL query
    sql_query = f"""
    SELECT 'venue' as account_type, user_id FROM venues WHERE email = '{email}'
    UNION
    SELECT 'artist', user_id FROM artists WHERE email = '{email}'
    UNION
    SELECT 'attendee', user_id FROM attendees WHERE email = '{email}';
    """

    try:
        # Executing the raw SQL query
        data = supabase.rpc("sql", {"query": sql_query}).execute()

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
    Retrieves account information based on a validated request.

    Args:
        request: A dictionary containing the validated request with 'account type', 'email', and
            other keys.

    Returns:
        A dictionary containing the requested account information if the email address is
            registered, else a string with an error message.
    """
    valid, message = validate_request(request)
    if not valid:
        # Return the error message from validate_request if the request is invalid
        return {'error': message}

    account_type = request['account type']
    email = request['email']
    # Create a string of attributes to select based on the request, excluding 'account type'
    attributes = ', '.join([key for key in request.keys() if key != 'account type'])

    # Fetch the account from the specified table using the email
    try:
        data = supabase.table(account_type + "s").select(attributes).eq("email", email).execute()
    except Exception as e:
        # Handle any exception that might occur during the API call
        return {'error': f"An API error occurred: {str(e)}"}

    # Check if the query was successful and if any account was found
    if data.data:
        # Return the requested account information
        return {'in_use': True, 'message': f"Email is already registered with user: {data.data[0]}."}
    else:
        # Return a descriptive error message if no account is found
        return {'in_use': False, 'message': "Email is not in use and account creation can proceed."}


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
