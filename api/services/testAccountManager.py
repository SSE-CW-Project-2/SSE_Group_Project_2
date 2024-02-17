import unittest
from unittest.mock import patch, MagicMock
from api.services.accountManager import create_account, update_account_details, delete_account

class TestCreateAccount(unittest.TestCase):

    @patch('accountManager.supabase')
    def test_account_creation(self, mock_supabase):
        # Mock the database response to simulate successful account creation
        mock_response = MagicMock()
        mock_response.data = [{'user_id': '123'}]
        mock_response.error = None
        mock_supabase.table().insert().execute.return_value = mock_response

        # Call the function
        result = create_account("newemail@example.com", "venue", "New Venue")

        # Assert the expected outcome
        self.assertEqual(result, '123', "The function should return the new account ID.")

    @patch('accountManager.check_email_registered')
    @patch('accountManager.supabase')
    def test_account_already_registered(self, mock_supabase, mock_check_email_registered):
        # Simulate that the email is already registered
        mock_check_email_registered.return_value = 'existing-id'

        # Call the function
        result = create_account("existingemail@example.com", "venue", "Existing Venue")

        # Assert that None is returned when the email is already in use
        self.assertIsNone(result, "The function should return None if the email is already in use.")

    @patch('accountManager.supabase')
    def test_account_creation_error(self, mock_supabase):
        # Mock the database response to simulate an insertion failure
        mock_response = MagicMock()
        mock_response.data = None
        mock_response.error = {'message': 'Insertion failed'}
        mock_supabase.table().insert().execute.return_value = mock_response

        # Call the function
        result = create_account("failinsert@example.com", "venue", "Fail Insert")

        # Assert the expected outcome
        self.assertIsNone(result, "The function should return None on insertion failure.")


class TestUpdateAccountDetails(unittest.TestCase):

    def setUp(self):
        self.current_email = 'existing@example.com'
        self.account_type = 'venue'
        self.new_email = 'new@example.com'
        self.new_name = 'New Name'

    @patch('accountManager.supabase')
    @patch('accountManager.check_email_registered', return_value='123')  # Assuming '123' is a placeholder user ID
    def test_account_updated(self, mock_check_email, mock_supabase):
        mock_response = MagicMock()
        mock_response.data = True
        mock_supabase.table().update().eq().execute.return_value = mock_response

        result = update_account_details(self.current_email, self.account_type, self.new_email, self.new_name)
        self.assertTrue(result, "The function should return True on successful update.")

    @patch('accountManager.check_email_registered', return_value=None)
    def test_account_does_not_exist(self, mock_check_email):
        result = update_account_details(self.current_email, self.account_type, self.new_email, self.new_name)
        self.assertIsNone(result, "The function should return None if the account does not exist.")

    @patch('accountManager.supabase')
    @patch('accountManager.check_email_registered', return_value='123')
    def test_no_updates_specified(self, mock_check_email, mock_supabase):
        result = update_account_details(self.current_email, self.account_type)
        self.assertFalse(result, "The function should return False if no updates are specified.")

    @patch('accountManager.supabase')
    @patch('accountManager.check_email_registered', return_value='123')
    def test_database_update_fails(self, mock_check_email, mock_supabase):
        mock_response = MagicMock()
        mock_response.data = None
        mock_response.error = {'message': 'Database error'}
        mock_supabase.table().update().eq().execute.return_value = mock_response

        result = update_account_details(self.current_email, self.account_type, self.new_email, self.new_name)
        self.assertFalse(result, "The function should return False on database error.")


class TestDeleteAccount(unittest.TestCase):

    def setUp(self):
        self.email = 'test@example.com'
        self.account_type = 'venue'

    @patch('accountManager.supabase')
    def test_account_deleted(self, mock_supabase):
        mock_response = MagicMock()
        mock_response.data = [{'id': '123'}]  # Simulate deletion response
        mock_supabase.table().delete().eq().execute.return_value = mock_response

        result = delete_account(self.email, self.account_type)
        self.assertTrue(result, "The function should return True when an account is successfully deleted.")

    @patch('accountManager.supabase')
    def test_deleting_nonexistant_account(self, mock_supabase):
        mock_response = MagicMock()
        mock_response.data = []  # Simulate no account found
        mock_supabase.table().delete().eq().execute.return_value = mock_response

        result = delete_account(self.email, self.account_type)
        self.assertFalse(result, "The function should return False if no account is found or already deleted.")

    @patch('accountManager.supabase')
    def test_account_deletion_failure(self, mock_supabase):
        mock_response = MagicMock()
        mock_response.data = None  # Simulate a failure or error case
        mock_response.error = {'message': 'Database error'}  # Including an error attribute for the sake of demonstration
        mock_supabase.table().delete().eq().execute.return_value = mock_response

        result = delete_account(self.email, self.account_type)
        self.assertFalse(result, "The function should return False on database error.")
        

if __name__ == '__main__':
    unittest.main()
