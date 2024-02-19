####################################################################################################
# Project Name: Motive Event Management System
# File: eventManager.py
# Description: Defines CRUD functionality for events.
#
# Authors: James Hartley, Ankur Desai, Patrick Borman, Julius Gasson, and Vadim Dunaevskiy
# Date: 2024-02-19
# Version: 1.0
#
# Notes: Currently, all functions rely on the unique event_id assigned by Supabase to pull
#        information, which may not be ideal for the front end. Also need to complete the api
#        routes at the end of this file to be deployed.
####################################################################################################


from flask import Flask, request, jsonify
from supabase import create_client, Client
from dotenv import load_dotenv
import os
import re

app = Flask(__name__)

# Create a Supabase client
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_PRIVATE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# Schema for request validation
object_types = ['venue', 'artist', 'attendee', 'event', 'ticket']
account_types = [ot for ot in object_types if ot not in ['event', 'ticket']]
non_account_types = [ot for ot in object_types if ot not in account_types]
attributes_schema = {'venue': ['user_id', 'email', 'username', 'location'],
                     'artist': ['user_id', 'email', 'username', 'genre'],
                     'attendee': ['user_id', 'email', 'username', 'city'],
                     'event': ['event_id', 'venue_id', 'event_name', 'date_time',
                               'total_tickets', 'sold_tickets', 'artist_ids'],
                     'ticket': ['ticket_id', 'event_id', 'attendee_id', 'price', 'redeemed']}
# Attribute keys are paired with boolean values for get requests, or the value to be added to the
# database otherwise.
request_template = ['function', 'object_type', 'identifier', 'attributes']
# Event identifier is the venue for create requests


# # def validate_request(request):


def create_event(attributes):
    """
    Inserts an event into the Supabase 'events' table.

    Args:
        attributes (dict): The attributes of the event to be created.

    Returns:
        tuple: (bool, dict or str) indicating success and the data returned by the database or an
            error message.
    """
    try:
        result = supabase.table('events').insert(attributes).execute()

        if result.error:
            return False, f"An error occurred: {result.error}"
        return True, result.data
    except Exception as e:
        return False, f"An exception occurred: {str(e)}"


def update_event(event_id, update_attributes):
    """
    Updates an event in the 'events' table in the Supabase database.

    Args:
        event_id (str): The unique identifier for the event to be updated.
        update_attributes (dict): A dictionary of attributes to update with their new values.

    Returns:
        A tuple containing a boolean indicating success and a message or data.
    """
    try:
        result = supabase.table('events').update(update_attributes).eq('event_id', event_id).execute()

        if result.error:
            return False, f"An error occurred during the update: {result.error}"
        else:
            return True, "Event update was successful."
    except Exception as e:
        return False, f"An exception occurred: {str(e)}"


def delete_event(event_id):
    """
    Deletes an event from the 'events' table in the Supabase database.

    Args:
        event_id (str): The unique identifier for the event to be deleted.

    Returns:
        A tuple containing a boolean indicating success and a message.
    """
    try:
        result = supabase.table('events').delete().eq('event_id', event_id).execute()

        if result.error:
            return False, f"An error occurred during the deletion: {result.error}"
        else:
            return True, "Event deletion was successful."
    except Exception as e:
        return False, f"An exception occurred: {str(e)}"


def get_event_info(event_id, requested_attributes):
    """
    Retrieves information for a specific event from the 'events' table in the Supabase database.

    Args:
        event_id (str): The unique identifier for the event.
        requested_attributes (list): A list of attributes to return for each event.

    Returns:
        A tuple containing a boolean indicating success, and either the event data or an error message.
    """
    try:
        select_query = ", ".join(requested_attributes) if requested_attributes else "*"
        result = supabase.table('events').select(select_query).eq('event_id', event_id).execute()

        if result.error:
            return False, f"An error occurred while fetching the event: {result.error}"
        elif len(result.data) == 0:
            return False, "No event found with the provided ID."
        else:
            return True, result.data[0]
    except Exception as e:
        return False, f"An exception occurred: {str(e)}"


def get_events_for_venue(venue_id, requested_attributes):
    """
    Queries events for a given venue from the 'events' table in the Supabase database.

    Args:
        venue_id (str): The user_id for the venue.
        requested_attributes (list): A list of attributes to return for each event.

    Returns:
        A tuple containing a boolean indicating success, and either the list of events or an error message.
    """
    try:
        # Constructing the select query string
        select_query = ", ".join(requested_attributes) if requested_attributes else "*"

        result = supabase.table('events').select(select_query).eq('venue_id', venue_id).execute()

        if result.error:
            return False, f"An error occurred while fetching events: {result.error}"
        else:
            return True, result.data
    except Exception as e:
        return False, f"An exception occurred: {str(e)}"


def get_events_for_artist(artist_ids):
    """
    Queries events for given artists from the 'events' table in the Supabase database.

    Args:
        artist_ids (list of str): A list of artist_id values, each a UUID string.

    Returns:
        A tuple containing a boolean indicating success, and either the list of events or an error
            message.
    """
    try:
        # artist_ids is stored as an array of UUIDs in the database
        result = supabase.table('events').select("*").filter('artist_ids', 'cs',
                                                             artist_ids).execute()

        if result.error:
            return False, f"An error occurred while fetching events for artists: {result.error}"
        else:
            return True, result.data
    except Exception as e:
        return False, f"An exception occurred: {str(e)}"


def get_events_for_attendee(attendee_id):
    """
    Queries events for a given attendee from the 'events' table in the Supabase database,
    based on the tickets they have bought.

    Args:
        attendee_id (str): The unique identifier for the attendee.

    Returns:
        A tuple containing a boolean indicating success, and either the list of events or an error message.
    """
    try:
        # Fetch ticket IDs for the attendee
        tickets_result = supabase.table('tickets').select("event_id").eq('attendee_id', attendee_id).execute()

        if tickets_result.error:
            return False, f"An error occurred while fetching tickets for the attendee: {tickets_result.error}"

        # Extract event IDs from tickets
        event_ids = [ticket['event_id'] for ticket in tickets_result.data]

        # Fetch events based on the event IDs
        events_result = supabase.table('events').select("*").in_('event_id', event_ids).execute()

        if events_result.error:
            return False, f"An error occurred while fetching events for the attendee: {events_result.error}"
        else:
            return True, events_result.data
    except Exception as e:
        return False, f"An exception occurred: {str(e)}"


# def fetch_events_near_postcode(postcode, max_distance)
#       Use an API, e.g. Google Maps, to identify which events are near the user


@app.route('/create_event', methods=['POST'])
def api_create_event():
    request_data = request.json
    success, message = create_event(request_data)
    if success:
        return jsonify({'message': message}), 200
    else:
        return jsonify({'error': message}), 400


@app.route('/update_event', methods=['POST'])
def api_update_account():
    request_data = request.json

    event_id = request_data.get('event_id')
    update_attributes = request_data.get('update_attributes')

    success, message = update_event(event_id, update_attributes)
    if success:
        return jsonify({'message': message}), 200
    else:
        return jsonify({'error': message}), 400


@app.route('/delete_event', methods=['POST'])
def api_delete_account():
    request_data = request.json
    success, message = delete_event(request_data)
    if success:
        return jsonify({'message': message}), 200
    else:
        return jsonify({'error': message}), 400


@app.route('/get_event_info', methods=['POST'])
def api_get_event_info():
    request_data = request.get_json()

    # Check a valid payload was received
    if not request_data:
        return jsonify({'error': 'Invalid or missing JSON payload'}), 400

    event_id = request_data.get('event_id')
    attributes = request_data.get('attributes')

    # Call function
    result = get_event_info(event_id, attributes)

    # Handle outcomes
    if 'error' in result:
        # Return 404 if account not found, or 500 for all other errors in reaching the database
        return (jsonify(result), 404 if result['error'] ==
                                        "No account found for the provided email." else 500)

    return jsonify(result), 200


if __name__ == '__main__':
    app.run(debug=True)