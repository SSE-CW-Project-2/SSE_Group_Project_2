####################################################################################################
# Project Name: Motive Event Management System
# Course: COMP70025 - Software Systems Engineering
# File: testAccountInfoRetrieval.py
# Description: This file contains unit tests for the validate_requst, is_valid_email,
#              check_email_in_use and fetch_account_info functions, used in the account information
#              query API.
#
# Authors: James Hartley, Ankur Desai, Patrick Borman, Julius Gasson, and Vadim Dunaevskiy
# Date: 2024-02-17
# Version: 2.0
#
# Notes: Supabase interactions tested using patch and MagicMock from unittest.mock
####################################################################################################


import unittest
from unittest.mock import patch, MagicMock
from accountInfoRetrieval import (validate_request, is_valid_email,
                                  check_email_in_use, fetch_account_info)

class TestValidateRequest(unittest.TestCase):
    def test_valid_venue_request(self):
        request = {'account type': 'venue', 'email': 'venue@example.com', 'user_id': '1',
                   'username': 'Venue Name', 'location': 'Venue Location'}
        self.assertEqual(validate_request(request), (True, "Request is valid."))

    def test_valid_artist_request(self):
        request = {'account type': 'artist', 'email': 'artist@example.com', 'user_id': '2',
                   'username': 'Artist Name', 'genre': 'Artist Genre'}
        self.assertEqual(validate_request(request), (True, "Request is valid."))

    def test_valid_attendee_request(self):
        request = {'account type': 'attendee', 'email': 'attendee@example.com',
                   'user_id': '3', 'username': 'Attendee Name', 'city': 'Attendee City'}
        self.assertEqual(validate_request(request), (True, "Request is valid."))

    def test_invalid_account_type(self):
        request = {'account type': 'unknown', 'email': 'user@example.com',
                   'user_id': '4', 'username': 'User Name'}
        self.assertEqual(validate_request(request), (False, "Invalid account type specified."))

    def test_missing_key_venue(self):
        request = {'account type': 'venue', 'email': 'venue@example.com',
                   'username': 'Venue Name', 'location': 'Venue Location'}
        self.assertEqual(validate_request(request),
                         (False, "Request is missing required keys: user_id."))

    def test_extra_keys(self):
        request = {'account type': 'venue', 'email': 'venue@example.com', 'user_id': '1', 'username':
            'Venue Name', 'location': 'Venue Location', 'extra': 'Extra Info'}
        self.assertEqual(validate_request(request), (True, "Request is valid. Note: "
                                                           "The following fields "
                      f"are not required and will not be used: extra."))
    def test_empty_request(self):
        request = {}
        self.assertEqual(validate_request(request), (False, "Invalid account type specified."))

    def test_missing_account_type(self):
        request = {'email': 'user@example.com', 'user_id': '5', 'username': 'User Name'}
        self.assertEqual(validate_request(request), (False, "Invalid account type specified."))


class TestEmailValidation(unittest.TestCase):
    def test_valid_email(self):
        self.assertTrue(is_valid_email('test@example.com'))

    def test_missing_domain(self):
        self.assertFalse(is_valid_email('test@'))

    def test_missing_at_symbol(self):
        self.assertFalse(is_valid_email('testexample.com'))

    def test_invalid_characters(self):
        self.assertFalse(is_valid_email('test@exa$mple.com'))

    def test_invalid_domain(self):
        self.assertFalse(is_valid_email('test@example'))

    def test_empty_string(self):
        self.assertFalse(is_valid_email(''))


class TestCheckEmailInUse(unittest.TestCase):

    @patch('accountInfoRetrieval.supabase')
    def test_email_in_use(self, mock_supabase):
        # Mock the response from Supabase
        mock_supabase.rpc.return_value.execute.return_value.data = \
            [{'account_type': 'venue', 'user_id': '123'}]

        result = check_email_in_use('test@example.com')
        self.assertEqual(result, {'account_type': 'venue', 'user_id': '123'})

    @patch('accountInfoRetrieval.supabase')
    def test_email_not_in_use(self, mock_supabase):
        # Mock the response to indicate no data found
        mock_supabase.rpc.return_value.execute.return_value.data = []

        result = check_email_in_use('new@example.com')
        self.assertEqual(result, {'message': 'Email is not in use.'})

    @patch('accountInfoRetrieval.supabase')
    def test_invalid_email_format(self, mock_supabase):
        # Test for invalid email format, which should not even attempt to query Supabase
        result = check_email_in_use('invalid-email')
        self.assertEqual(result, {'error': 'Invalid email format.'})

    @patch('accountInfoRetrieval.supabase')
    def test_supabase_error(self, mock_supabase):
        # Mock an exception being raised during the Supabase call
        mock_supabase.rpc.side_effect = Exception("Supabase query failed")

        result = check_email_in_use('error@example.com')
        self.assertEqual(result, {'error': 'An error occurred: Supabase query failed'})


class TestFetchAccountInfo(unittest.TestCase):

    @patch('accountInfoRetrieval.supabase')
    @patch('accountInfoRetrieval.validate_request')
    def test_valid_request_with_account_found(self, mock_validate, mock_supabase):
        # Mock validate_request to return valid
        mock_validate.return_value = (True, "Request is valid.")
        # Mock Supabase response
        mock_supabase.table().select().eq().execute.return_value.data = [{'user_id': '123'}]

        request = {'account type': 'venue', 'email': 'test@example.com', 'username': 'Test Venue'}
        result = fetch_account_info(request)
        self.assertTrue(result['in_use'])
        self.assertIn('Email is already registered with user', result['message'])

    @patch('accountInfoRetrieval.supabase')
    @patch('accountInfoRetrieval.validate_request')
    def test_valid_request_no_account_found(self, mock_validate, mock_supabase):
        mock_validate.return_value = (True, "Request is valid.")
        mock_supabase.table().select().eq().execute.return_value.data = []

        request = {'account type': 'venue', 'email': 'new@example.com', 'username': 'New Venue'}
        result = fetch_account_info(request)
        self.assertFalse(result['in_use'])
        self.assertEqual(result['message'], "Email is not in use and account creation can proceed.")

    @patch('accountInfoRetrieval.validate_request')
    def test_invalid_request(self, mock_validate):
        mock_validate.return_value = (False, "Invalid request.")

        request = {'account type': 'unknown', 'email': 'test@example.com'}
        result = fetch_account_info(request)
        self.assertEqual(result, {'error': 'Invalid request.'})

    @patch('accountInfoRetrieval.supabase')
    @patch('accountInfoRetrieval.validate_request')
    def test_api_error(self, mock_validate, mock_supabase):
        mock_validate.return_value = (True, "Request is valid.")
        mock_supabase.table().select().eq().execute.side_effect = Exception("API error")

        request = {'account type': 'venue', 'email': 'test@example.com'}
        result = fetch_account_info(request)
        self.assertTrue('error' in result)
        self.assertEqual(result['error'], "An API error occurred: API error")


if __name__ == '__main__':
    unittest.main()
