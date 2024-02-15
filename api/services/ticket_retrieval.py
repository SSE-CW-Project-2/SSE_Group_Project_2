####################################################################################################
# Project Name: Motive Event Management System
# File: ticket_generation.py
# Description: This file defines the behaviour of the ticket generation api. When called, it creates
#              the specified number of tickets in the database at a specified price, each with a
#              unique hash acting as the identifier. Retrieving information about any ticket(s) is
#              handled by the ticket_retrieve.py api and ticket sales are handled by the
#              ticket_sales.py api.
#
# Authors:
# Date: 2024-02-14
# Version: 1.0
#
# Notes: This will need to be updated to match the database schemas once they are set up, and then
#        it should be containerised and integrated into the application. Currently, all references
#        to the database and expected JSON requests are placeholders.
#           This is separate from the generation and sales functionality as we anticipate very
#        smoother load/traffic patterns for the data retrieval functions and therefore different
#        scaling/cost approaches.
####################################################################################################

import azure.functions as func
import pyodbc
import os
import json


def main(req: func.HttpRequest) -> func.HttpResponse:
    operation = req.params.get('operation')

    if operation == 'getUserTickets':
        user_id = req.params.get('userId')
        if not user_id:
            return func.HttpResponse("User ID is required for getting user tickets.", status_code=400)
        return get_user_tickets(user_id)
    elif operation == 'getEventAvailability':
        event_id = req.params.get('eventId')
        if not event_id:
            return func.HttpResponse("Event ID is required for getting event ticket availability.", status_code=400)
        return get_event_availability(event_id)
    else:
        return func.HttpResponse("Invalid operation specified.", status_code=400)


def get_user_tickets(cursor, user_id):
    """
    Allows applications to query which tickets a specific user owns for upcoming events.

    Args:
        cursor: The object being used to execute SQL commands to perform CRUD operations.
        user_id: The unique id assigned to the user being queried, found in the user table.

    Returns:
        A func.HttpResponse object containing the JSON representation of the user's tickets
        or an error message if no tickets are found or a database error occurs.
    """
    query = """
    SELECT t.TicketId, t.EventId, t.Redeemed, e.EventName, e.Date, v.VenueName, b.BandName
    FROM Tickets t
    JOIN Events e ON t.EventId = e.EventId
    JOIN Venues v ON e.VenueId = v.VenueId
    JOIN EventBands eb ON e.EventId = eb.EventId
    JOIN Bands b ON eb.BandId = b.BandId
    WHERE t.UserId = ?
    """

    try:
        cursor.execute(query, user_id)
        tickets = cursor.fetchall()

        if not tickets:
            return func.HttpResponse(json.dumps({"error": "No tickets found for the given user ID."}),
                                     status_code=404,
                                     mimetype="application/json")

        tickets_info = aggregate_ticket_info(tickets)
        return func.HttpResponse(json.dumps(tickets_info), status_code=200, mimetype="application/json")

    except Exception as e:
        # Log the error for debugging purposes
        logging.error(f"Database error: {e}")
        return func.HttpResponse(json.dumps({"error": "Failed to retrieve tickets due to a database error."}),
                                 status_code=500,
                                 mimetype="application/json")


def aggregate_ticket_info(tickets):
    """
    Aggregates ticket information, particularly focusing on grouping multiple bands associated with each ticket.

    Args:
        tickets (list of tuples): A list where each tuple contains information about a ticket and associated event and band.
            Each tuple is expected to have the following structure:
            (TicketId, EventId, Redeemed, EventName, Date, VenueName, BandName)

    Returns:
        list of dicts: Returns a list of dictionaries, where each dictionary contains detailed information about a ticket,
        including the event name, date, venue, redemption status, and a list of band names associated with the event.
        If a ticket is associated with multiple bands, all band names are aggregated into a single list under that ticket's entry.
    """
    tickets_info = []
    for ticket in tickets:
        ticket_id, event_id, redeemed, event_name, date, venue_name, band_name = ticket
        existing_ticket = next((item for item in tickets_info if item["TicketId"] == ticket_id), None)
        if existing_ticket:
            existing_ticket["BandNames"].append(band_name)
        else:
            tickets_info.append({
                "TicketId": ticket_id,
                "EventId": event_id,
                "Redeemed": redeemed,
                "EventName": event_name,
                "Date": date.strftime("%Y-%m-%d"),
                "VenueName": venue_name,
                "BandNames": [band_name]
            })
    return tickets_info


def get_event_availability(cursor, event_id):
    """
    Allows applications to query the number of sold and unsold tickets for an existing
        event. The tickets are stored in the "tickets" table.

    Args:
        cursor: The object being used to execute SQL commands to perform CRUD operations
            (e.g. pyodbc).
        event_id: The unique hash/identifier assigned to the event whose tickets are being queried.

    Returns:
         A func.HttpResponse object containing the JSON representation of the event_id, and the
            numbers of sold and unsold tickets with status code 200, OR an error message with status
            code 404 if the event is not found in the database.
    """
    query = """
    SELECT 
        (SELECT COUNT(*) FROM Tickets WHERE EventId = ? AND UserId IS NOT NULL) AS SoldTickets,
        (SELECT COUNT(*) FROM Tickets WHERE EventId = ? AND UserId IS NULL) AS UnsoldTickets
    """
    cursor.execute(query, (event_id, event_id))
    result = cursor.fetchone()

    if result:
        availability_info = {
            "EventId": event_id,
            "SoldTickets": result[0],
            "UnsoldTickets": result[1]
        }
        return func.HttpResponse(json.dumps(availability_info), status_code=200, mimetype="application/json")
    else:
        return func.HttpResponse(f"No ticket information found for EventId {event_id}.", status_code=404)
