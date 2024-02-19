####################################################################################################
# Project Name: Motive Event Management System
# File: ticketManager.py
# Description:
#
# Authors: James Hartley, Ankur Desai, Patrick Borman, Julius Gasson, and Vadim Dunaevskiy
# Date: 2024-02-19
# Version: 1.0
#
# Notes:
####################################################################################################


from flask import Flask
from supabase import create_client, Client
from dotenv import load_dotenv
import os

app = Flask(__name__)

# Create a Supabase client
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_PRIVATE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def create_tickets_for_event(event_id, price, n_tickets):
    """
    Creates a batch of N tickets for a specified event and inserts them into the database.

    Args:
        event_id (str): The unique identifier for the event to which the tickets belong.
        price (float): The price of each ticket in GBP.
        n_tickets (int): The number of tickets to create.

    Returns:
        A tuple containing a boolean indicating success, and either a success message or an error message.
    """
    tickets_data = [{
        'event_id': event_id,
        'attendee_id': None,  # No attendee_id since tickets have not been bought yet
        'price': price,
        'redeemed': False
    } for _ in range(n_tickets)]  # Generate N tickets

    try:
        result = supabase.table('tickets').insert(tickets_data).execute()

        if result.error:
            return False, f"An error occurred while creating tickets: {result.error}"
        else:
            return True, f"{n_tickets} tickets successfully created for event {event_id}."
    except Exception as e:
        return False, f"An exception occurred: {str(e)}"


# # def update_ticket(request):


# # def delete_ticket(request):


# # def fetch_ticket_info():
#     """Fetches information for a specific ticket"""


# # def fetch_users_tickets():
#     """Fetches IDs and information for all tickets owned by a particular user"""


# def buy_ticket():
#       "" assigns attendee UUID to ticket after payment is validated """

# def redeem_ticket():
#       """ Mark boolean redemption status as true, meaning it cannot be used again """
