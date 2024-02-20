####################################################################################################
# Project Name: Motive Event Management System
# Course: COMP70025 - Software Systems Engineering
# File: testTicketManager.py
# Description: This file contains unit tests for each function in the ticketManager.py file.
#
# Authors: James Hartley, Ankur Desai, Patrick Borman, Julius Gasson, and Vadim Dunaevskiy
# Date: 2024-02-20
# Version: 1.1
#
# Notes:
####################################################################################################


import unittest
from unittest.mock import patch, MagicMock
from ticketManager import (create_tickets, assign_tickets_to_attendee, get_tickets_info,
                           get_tickets_info_for_users)


class TestCreateTicketsForEvent(unittest.TestCase):
    @patch('ticketManager.supabase')
    def test_create_tickets_success(self, mock_supabase):
        mock_result = MagicMock()
        mock_result.error = None
        mock_supabase.table().insert().execute.return_value = mock_result

        event_id = 'test-event-id'
        price = 10.0
        n_tickets = 5

        success, message = create_tickets(event_id, price, n_tickets)

        self.assertTrue(success)
        self.assertEqual(message, f"{n_tickets} tickets successfully created for event {event_id}.")

    @patch('ticketManager.supabase')
    def test_create_tickets_for_event_failure(self, mock_supabase):
        mock_result = MagicMock()
        mock_result.error = "Database error"
        mock_supabase.table().insert().execute.return_value = mock_result

        event_id = 'test-event-id'
        price = 10.0
        n_tickets = 5

        success, message = create_tickets(event_id, price, n_tickets)

        self.assertFalse(success)
        self.assertIn("An error occurred while creating tickets", message)


class TestAssignTicketsToAttendee(unittest.TestCase):
    @patch('ticketManager.supabase')
    def test_assign_tickets_to_attendee_success(self, mock_supabase):
        # Setup mock Supabase response for a successful update operation
        mock_result = MagicMock()
        mock_result.error = None
        mock_supabase.table().update().in_().execute.return_value = mock_result

        ticket_ids = ['ticket-id-1', 'ticket-id-2']
        attendee_id = 'attendee-id'

        success, message = assign_tickets_to_attendee(ticket_ids, attendee_id)

        self.assertTrue(success)
        self.assertIn("Tickets successfully assigned", message)

    @patch('ticketManager.supabase')
    def test_assign_tickets_to_attendee_failure(self, mock_supabase):
        # Setup mock Supabase response for a failed update operation
        mock_result = MagicMock()
        mock_result.error = "An error occurred"
        mock_supabase.table().update().in_().execute.return_value = mock_result

        ticket_ids = ['ticket-id-1', 'ticket-id-2']
        attendee_id = 'attendee-id'

        success, message = assign_tickets_to_attendee(ticket_ids, attendee_id)

        self.assertFalse(success)
        self.assertIn("An error occurred while assigning the tickets", message)

    @patch('ticketManager.supabase')
    def test_assign_tickets_to_attendee_exception(self, mock_supabase):
        # Setup mock Supabase to raise an exception during the update operation
        mock_supabase.table().update().in_().execute.side_effect = Exception("Database error")

        ticket_ids = ['ticket-id-1', 'ticket-id-2']
        attendee_id = 'attendee-id'

        success, message = assign_tickets_to_attendee(ticket_ids, attendee_id)

        self.assertFalse(success)
        self.assertIn("An exception occurred", message)


class TestGetTicketsInfo(unittest.TestCase):
    @patch('ticketManager.supabase')
    def test_get_tickets_info_success(self, mock_supabase):
        # Setup mock Supabase response for successful ticket info retrieval
        mock_result = MagicMock()
        mock_result.error = None
        mock_result.data = [
            {'ticket_id': 'ticket-id-1', 'price': 20.0, 'redeemed': False},
            {'ticket_id': 'ticket-id-2', 'price': 25.0, 'redeemed': True}
        ]
        mock_supabase.table().select().in_().execute.return_value = mock_result

        ticket_ids = ['ticket-id-1', 'ticket-id-2']
        requested_attributes = {'price': True, 'redeemed': True}

        success, data = get_tickets_info(ticket_ids, requested_attributes)

        self.assertTrue(success)
        self.assertEqual(len(data), 2)  # Verify that two tickets' info was returned
        self.assertIn('ticket-id-1', [ticket['ticket_id'] for ticket in data])
        self.assertIn('ticket-id-2', [ticket['ticket_id'] for ticket in data])

    @patch('ticketManager.supabase')
    def test_get_tickets_info_failure(self, mock_supabase):
        # Setup mock Supabase response for a failed ticket info retrieval
        mock_result = MagicMock()
        mock_result.error = "Database error"
        mock_result.data = []
        mock_supabase.table().select().in_().execute.return_value = mock_result

        ticket_ids = ['ticket-id-1', 'ticket-id-2']
        requested_attributes = {'price': True, 'redeemed': True}

        success, error_message = get_tickets_info(ticket_ids, requested_attributes)

        self.assertFalse(success)
        self.assertIn("An error occurred while fetching ticket info", error_message)

    @patch('ticketManager.supabase')
    def test_get_tickets_info_exception(self, mock_supabase):
        # Setup mock Supabase to raise an exception during ticket info retrieval
        mock_supabase.table().select().in_().execute.side_effect = Exception("Unexpected error")

        ticket_ids = ['ticket-id-1', 'ticket-id-2']
        requested_attributes = {'price': True, 'redeemed': True}

        success, error_message = get_tickets_info(ticket_ids, requested_attributes)

        self.assertFalse(success)
        self.assertIn("An exception occurred", error_message)


class TestGetTicketsInfoForUsers(unittest.TestCase):
    @patch('ticketManager.supabase')
    def test_get_tickets_info_for_users_success(self, mock_supabase):
        # Mock Supabase response for successful ticket info retrieval
        mock_result = MagicMock()
        mock_result.error = None
        mock_result.data = [
            {'ticket_id': 'ticket-1', 'attendee_id': 'user-id-1', 'price': 20.0},
            {'ticket_id': 'ticket-2', 'attendee_id': 'user-id-2', 'price': 25.0}
        ]
        mock_supabase.table().select().in_().execute.return_value = mock_result

        attendee_ids = ['user-id-1', 'user-id-2']
        requested_attributes = {'price': True}

        success, data = get_tickets_info_for_users(attendee_ids, requested_attributes)

        self.assertTrue(success)
        self.assertIn('user-id-1', data)
        self.assertIn('user-id-2', data)
        self.assertEqual(data['user-id-1'][0]['price'], 20.0)
        self.assertEqual(data['user-id-2'][0]['price'], 25.0)

    @patch('ticketManager.supabase')
    def test_get_tickets_info_for_users_failure(self, mock_supabase):
        # Setup mock Supabase response for a failed ticket info retrieval
        mock_result = MagicMock()
        mock_result.error = "Database error"
        mock_result.data = []
        mock_supabase.table().select().in_().execute.return_value = mock_result

        attendee_ids = ['user-id-1', 'user-id-2']
        requested_attributes = {'price': True}

        success, error_message = get_tickets_info_for_users(attendee_ids, requested_attributes)

        self.assertFalse(success)
        self.assertIn("An error occurred while fetching tickets for users", error_message)

    @patch('ticketManager.supabase')
    def test_get_tickets_info_for_users_exception(self, mock_supabase):
        # Setup mock Supabase to raise an exception during ticket info retrieval
        mock_supabase.table().select().in_().execute.side_effect = Exception("Unexpected error")

        attendee_ids = ['user-id-1', 'user-id-2']
        requested_attributes = {'price': True}

        success, error_message = get_tickets_info_for_users(attendee_ids, requested_attributes)

        self.assertFalse(success)
        self.assertIn("An exception occurred", error_message)


if __name__ == '__main__':
    unittest.main()