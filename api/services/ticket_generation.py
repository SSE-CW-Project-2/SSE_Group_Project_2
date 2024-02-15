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
####################################################################################################

import azure.functions as func
import pyodbc
import os
import json


def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            "Invalid JSON in request body.",
            status_code=400
        )

    event_id = req_body.get('EventId')
    ticket_count = req_body.get('TicketCount')

    if not event_id or ticket_count <= 0:
        return func.HttpResponse(
            "Please provide valid event details.",
            status_code=400
        )

    connection_string = os.environ['SqlConnectionString']

    try:
        with pyodbc.connect(connection_string) as conn:
            with conn.cursor() as cursor:
                for _ in range(ticket_count):
                    ticket_id = str(uuid.uuid4())
                    cursor.execute("INSERT INTO Tickets (TicketId, EventId, Status) VALUES (?, ?, 'Available')",
                                   (ticket_id, event_id))
                conn.commit()

        return func.HttpResponse(
            "Tickets generated successfully.",
            status_code=200
        )
    except Exception as e:
        return func.HttpResponse(
            f"Failed to generate tickets. Error: {str(e)}",
            status_code=500
        )
