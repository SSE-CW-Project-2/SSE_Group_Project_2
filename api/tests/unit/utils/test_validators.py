####################################################################################################
# Project Name: Motive Event Management System
# File: test_user_model.py
# Description: This file contains the unit tests for the email and password validator functions
#              defined in validators.py
#
# Authors:
# Date: 2024-02-14
# Version: 1.0
#
# Notes:
####################################################################################################

import unittest
from utils.validators import validate_email, validate_password


class TestValidateEmail(unittest.TestCase):

    def test_valid_email(self):
        self.assertTrue(validate_email("email@example.com"))
        self.assertTrue(validate_email("firstname.lastname@example.com"))
        self.assertTrue(validate_email("email@subdomain.example.com"))

    def test_invalid_email(self):
        self.assertFalse(validate_email("plainaddress"))
        self.assertFalse(validate_email("@no-local-part.com"))
        self.assertFalse(validate_email("Outlook User<outlookuser@example.com>"))
        self.assertFalse(validate_email("email@example.com (Joe Smith)"))
        self.assertFalse(validate_email("email@-example.com"))

    def test_email_edge_cases(self):
        # Edge case: Email is exactly at the domain limit
        self.assertTrue(validate_email("a" * 64 + "@example.com"))
        # Edge case: Local part is too long
        self.assertFalse(validate_email("a" * 65 + "@example.com"))
        # Edge case: Domain part is too long
        self.assertFalse(validate_email("email@" + "a" * 256 + ".com"))


class TestValidatePassword(unittest.TestCase):

    def test_valid_password(self):
        # Likely valid passwords
        self.assertTrue(validate_password("ValidPassword1@"))
        self.assertTrue(validate_password("Another$Valid1"))
        self.assertTrue(validate_password("YetAnotherValidPassword1!"))

    def test_invalid_password(self):
        # Test comprehensive list of password violations
        self.assertFalse(validate_password("short1A@"))  # Too short
        self.assertFalse(validate_password("nouppercase1@"))  # No uppercase letter
        self.assertFalse(validate_password("NOLOWERCASE1@"))  # No lowercase letter
        self.assertFalse(validate_password("NoNumber!"))  # No digit
        self.assertFalse(
            validate_password("NoSpecialCharacter1")
        )  # No special character

    def test_password_edge_cases(self):
        # Edge case: Password is exactly at the maximum limit
        self.assertTrue(validate_password("A" + "a" * 10 + "1" * 10 + "@" * 42))
        # Edge case: Password exceeds the maximum length
        self.assertFalse(validate_password("A" + "a" * 10 + "1" * 10 + "@" * 43))
        # Edge case: Password includes a wide variety of special characters
        self.assertTrue(validate_password("Valid1@!#$%^&*()"))


if __name__ == "__main__":
    unittest.main()
