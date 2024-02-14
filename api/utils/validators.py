####################################################################################################
# Project Name: Motive Event Management System
# File: validators.py
# Description: This file contains utility functions for validating user input across the Event
#              Management System. It includes functions to validate email formats and password
#              strength, ensuring that user inputs meet the application's requirements for
#              security and data integrity. These validators are used throughout the application,
#              particularly in user registration and profile update operations, to prevent
#              invalid data from being processed or stored.
#
# Authors:
# Date: 2024-02-14
# Version: 1.0
#
# Notes: Validation criteria and functions may be expanded or adjusted as needed based on
#        evolving requirements or security practices. Ensure that validation logic remains
#        consistent with the application's overall data handling and privacy policies.
####################################################################################################

import re


def validate_email(email):
    """
    Validates an email address using a regular expression pattern.

    This function checks if the provided email address conforms to a standard pattern
    that includes characters before and after an "@" symbol, followed by a domain name
    with a valid top-level domain.

    Parameters:
    - email (str): The email address to validate.

    Returns:
    - bool: True if the email matches the pattern, False otherwise.

    Example Usage:
    >>> validate_email("user@example.com")
    True
    >>> validate_email("user@example")
    False
    >>> validate_email("user@.com")
    False
    """
    pattern = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
    return re.match(pattern, email) is not None


def validate_password(password):
    """
    Validates a password based on specified complexity requirements and length.

    Ensures the password is at least 8 characters long, but no more than 32 characters.
    It must contain at least one uppercase letter, one lowercase letter, one digit,
    and one special character. This function is designed to accept passwords generated
    by password managers, allowing for a wide range of special characters.

    Parameters:
    - password (str): The password string to validate.

    Returns:
    - bool: True if the password meets the complexity and length requirements, False otherwise.

    Example Usage:
    >>> validate_password("VeryComplexPassword1!")
    True
    >>> validate_password("short")
    False
    >>> validate_password("ThisIsAVeryLongPasswordThatGoesOnForeverAndEverAndEverAndItIsTooLong")
    False
    >>> validate_password("ValidPassword1@")
    True
    """
    # Updated pattern to include a broader set of special characters and a length check
    pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z\d])[A-Za-z\d\W\S]{8,32}$"
    return re.match(pattern, password) is not None

