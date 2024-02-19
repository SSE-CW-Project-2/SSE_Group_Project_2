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
object_types = ['venue', 'artist', 'attendee', 'event', 'ticket']
attributes_schema = {'venue': ['user_id', 'email', 'username', 'location'],
                     'artist': ['user_id', 'email', 'username', 'genre'],
                     'attendee': ['user_id', 'email', 'username', 'city'],
                     'event': ['event_id', 'venue_id', 'event_name', 'date_time',
                               'total_tickets', 'sold_tickets', 'artist_ids'],
                     'ticket': ['ticket_id', 'event_id', 'attendee_id', 'redeemed']}
# Attribute keys are paired with true if the data is being pulled and false otherwise to limit
# size of Supabase requests.
request_template = ['function', 'object_type', 'identifier', 'attributes']


def validate_get_request(request_json):
    """
    Validates whether a JSON request directed to this API follows a valid template to prevent
        accessing information that should not be available to it and limit calls to Supabase that
        cannot be processed.

    Args:
        request_json: A JSON-format dictionary containing the type of function ('get', 'create',
            'update', or 'delete'), the object being queried ('venue', 'artist', 'attendee',
            'event', or 'ticket'), the identifier being used to query the database (an email address
            for account types, or a unique id for the tickets and events), and a list of the
            attributes that should be returned from the data request.

    Returns:
        A tuple (bool, str) indicating if the request template is valid and a message explaining why
            or why not.
    """
    # Check if function is 'get'
    if request_json.get('function') != 'get':
        return False, "Invalid function. Only 'get' is allowed."

    # Check if object_type is valid
    object_type = request_json.get('object_type')
    if object_type is None:
        return False, "Must specify an object type."
    if object_type not in object_types:
        return False, f"Invalid object_type. Must be one of {object_types}."

    # Validate identifier based on object_type
    identifier = request_json.get('identifier')
    if identifier is None:
        return False, "Invalid or missing email."
    elif object_type in ['venue', 'artist', 'attendee']:
        if not is_valid_email(identifier):
            return False, f"Identifier for {object_type} must be a valid email."

    # For 'event' and 'ticket', let's say we are using 'event_id' and 'ticket_id' as identifiers
    if object_type == 'event' and not isinstance(identifier, str):
        return False, "Identifier for event must be event_id (string)."

    if object_type == 'ticket' and not isinstance(identifier, str):
        return False, "Identifier for ticket must be ticket_id (string)."

    # Check attributes
    attributes = request_json.get('attributes')
    if not attributes:
        return False, "Attributes must be provided for querying."

    valid_attributes = attributes_schema.get(object_type)
    queried_attributes = attributes.keys()

    # At least one valid attribute must be queried
    if not any(attr in valid_attributes for attr in queried_attributes):
        return False, "At least one valid attribute must be queried."

    # No extra attributes should be present in the query
    for attr in queried_attributes:
        if attr not in valid_attributes:
            return False, f"Invalid attribute '{attr}' for object_type '{object_type}'."

    # If we reach here, the request is valid
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
        # Executing the raw SQL query, saved on Supabase as a rpc function
        # Queries all three tables without making separate api calls
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
    valid, message = validate_get_request(request)
    if not valid:
        return {'error': message}

    account_type = request.get('object_type')
    email = request['identifier']
    attributes_to_fetch = [attr for attr, include in request.get('attributes', {}).items() if include]

    # Construct the attributes string for the query
    attributes = ', '.join(attributes_to_fetch)

    try:
        data = supabase.table(account_type + "s").select(attributes).eq("email", email).execute()
        if data.data:
            return {'in_use': True, 'message': 'Email is registered with user', 'data': data.data[0]}
        else:
            return {'in_use': False, 'message': "Email is not in use."}
    except Exception as e:
        return {'error': f"An API error occurred: {str(e)}"}


# def fetch_event_info(request):
    """Fetches information on a specific event"""
    # object_type = request.get('object_type')

# def fetch_venues_events(request):
    """Fetches IDs and information for each event being hosted by a specific venue"""
    """Includes the total number of tickets and the number remaining unsold"""

# def fetch_artists_events(request):
    """Fetches IDs and information for each event an artist is performing at"""

# def fetch_ticket_info():
    """Fetches information for a specific ticket"""

# fetch_users_tickets():
    """Fetches IDs and information for all tickets owned by a """

# fetch_users_upcoming_events():
    """Fetches IDss and information for all future events a user has a ticket for"""

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
