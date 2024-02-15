####################################################################################################
# Project Name: Motive Event Management System
# File: event_manager.py
# Description: This file defines the population of the Firestore when events are created, updated
#              and deleted.
#
# Authors:
# Date: 2024-02-14
# Version: 1.0
#
# Notes: Venue authentication should be added to this file under each method. Make more robust with
#        fixed JSON templates and error handling.
####################################################################################################

import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin import auth
from flask import abort, jsonify

# Initialize the Firebase Admin SDK
if not firebase_admin._apps:
    firebase_admin.initialize_app()

db = firestore.client()


def create_event(venue_id, event_data):
    """
    Creates a new event in the specified venue's subcollection and top-level Events collection.

    Parameters:
    - venue_id (str): The ID of the venue hosting the event.
    - event_data (dict): A dictionary containing data for the new event.
    """
    # Add to the venue's subcollection of events
    venue_events_ref = db.collection('Venues').document(venue_id).collection('Events')
    venue_event_ref = venue_events_ref.add(event_data)

    # Also add to the top-level Events collection for direct access
    event_data['venueId'] = venue_id  # Ensure linkage back to the venue
    top_level_event_ref = db.collection('Events').document(venue_event_ref[1].id).set(event_data)

    return venue_event_ref[1].id  # Return the newly created Event ID


def update_event(venue_id, event_id, update_data):
    """
    Updates an existing event's details in both the venue's subcollection and the top-level Events collection.

    Parameters:
    - venue_id (str): The ID of the venue hosting the event.
    - event_id (str): The ID of the event to update.
    - update_data (dict): A dictionary of fields to update.
    """
    # Update in the venue's subcollection of events
    venue_event_ref = db.collection('Venues').document(venue_id).collection('Events').document(event_id)
    venue_event_ref.update(update_data)

    # Update in the top-level Events collection
    db.collection('Events').document(event_id).update(update_data)


def delete_event(venue_id, event_id):
    """
    Deletes an event from both the venue's subcollection and the top-level Events collection.

    Parameters:
    - venue_id (str): The ID of the venue hosting the event.
    - event_id (str): The ID of the event to delete.
    """
    # Delete from the venue's subcollection of events
    venue_event_ref = db.collection('Venues').document(venue_id).collection('Events').document(event_id)
    venue_event_ref.delete()

    # Delete from the top-level Events collection
    db.collection('Events').document(event_id).delete()

