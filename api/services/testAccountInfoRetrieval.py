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
from accountInfoRetrieval import (validate_get_request, is_valid_email,
                                  check_email_in_use, fetch_account_info)

class TestValidateRequest(unittest.TestCase):

    def test_email_validation(self):
        self.assertTrue(is_valid_email('test@example.com'))
        self.assertFalse(is_valid_email('invalid-email'))

    def test_valid_requests_with_attributes(self):
        request = {
            'function': 'get', 
            'object_type': 'venue', 
            'identifier': 'venue@example.com', 
            'attributes': {
                'user_id': True,
                'location': True
            }
        }
        self.assertEqual(validate_get_request(request), (True, "Request is valid."))

    def test_request_with_nonexistant_attributes(self):
        request = {
            'function': 'get', 
            'object_type': 'artist', 
            'identifier': 'artist@example.com', 
            'attributes': {
                'user_id': True,
                'genre': True,
                'extra_field': False
            }
        }
        valid, message = validate_get_request(request)
        self.assertFalse(valid)
        self.assertIn('extra_field', message)

    def test_invalid_email_in_request(self):
        request = {
            'function': 'get', 
            'object_type': 'artist', 
            'identifier': 'invalid-email', 
            'attributes': {
                'user_id': True,
                'genre': True
            }
        }
        self.assertEqual(validate_get_request(request),
                         (False, "Identifier for artist must be a valid email."))

    def test_missing_email(self):
        request = {
            'function': 'get',
            'object_type': 'artist',
            'identifier': 'invalid-email',
            'attributes': {
                'user_id': True,
                'email': False,
                'username': False,
                'genre': False
            }
        }
        self.assertEqual(validate_get_request(request),
                         (False, "Identifier for artist must be a valid email."))

    def test_invalid_account_type(self):
        request = {
            'function': 'get',
            'object_type': 'non-defined_account_type',
            'identifier': 'invalid-email',
            'attributes': {
                'user_id': True,
                'genre': True
            }
        }
        self.assertEqual(validate_get_request(request),
                         (False, "Invalid object_type. Must be one of "
                                 "['venue', 'artist', 'attendee', 'event', 'ticket']."))

    def test_missing_account_type(self):
        request = {
            'function': 'get',
            'identifier': 'invalid-email',
            'attributes': {
                'user_id': True,
                'genre': True
            }
        }
        self.assertEqual(validate_get_request(request), (False, "Must specify an object type."))

    def test_request_with_all_false_attributes(self):
        request = {
            'function': 'get',
            'object_type': 'artist',
            'identifier': 'example@example.com',
            'attributes': {
                'user_id': False,
                'email': False,
                'username': False,
                'genre': False
            }
        }
        self.assertEqual(validate_get_request(request), (True, "Request is valid."))


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
    @patch('accountInfoRetrieval.validate_get_request')
    def test_valid_request_with_account_found(self, mock_validate, mock_supabase):
        # Mock validate_get_request to return valid
        mock_validate.return_value = (True, "Request is valid.")
        # Mock Supabase response
        mock_supabase.table().select().eq().execute.return_value.data = [{'user_id': '123'}]

        request = {
            'function': 'get',
            'object_type': 'venue',
            'identifier': 'new@example.com',
            'attributes': {
                'user_id': True,
                'username': True
            }
        }
        result = fetch_account_info(request)
        self.assertTrue(result['in_use'])
        self.assertIn('Email is registered with user', result['message'])

    @patch('accountInfoRetrieval.supabase')
    @patch('accountInfoRetrieval.validate_get_request')
    def test_valid_request_no_account_found(self, mock_validate, mock_supabase):
        mock_validate.return_value = (True, "Request is valid.")
        mock_supabase.table().select().eq().execute.return_value.data = []

        request = {
            'function': 'get',
            'object_type': 'venue',
            'identifier': 'new@example.com',
            'attributes': {
                'user_id': True,
                'username': True
            }
        }
        result = fetch_account_info(request)
        self.assertFalse(result['in_use'])
        self.assertEqual(result['message'], "Email is not in use.")

    @patch('accountInfoRetrieval.validate_get_request')
    def test_invalid_request(self, mock_validate):
        mock_validate.return_value = (False, "Invalid request.")

        request = {
            'function': 'undefined',
            'object_type': 'unknown',
            'identifier': 'new@example.com',
        }
        result = fetch_account_info(request)
        self.assertEqual(result, {'error': 'Invalid request.'})

    @patch('accountInfoRetrieval.supabase')
    @patch('accountInfoRetrieval.validate_get_request')
    def test_api_error(self, mock_validate, mock_supabase):
        mock_validate.return_value = (True, "Request is valid.")
        mock_supabase.table().select().eq().execute.side_effect = Exception("API error")

        request = {
            'function': 'get',
            'object_type': 'unknown',
            'identifier': 'new@example.com',
            'attributes': {
                'user_id': True,
                'username': True
            }
        }
        result = fetch_account_info(request)
        self.assertTrue('error' in result)
        self.assertEqual(result['error'], "An API error occurred: API error")


if __name__ == '__main__':
    unittest.main()
