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
    """Validate the email format."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None

def validate_password(password):
    """Check for a strong password. This is a basic example; adjust complexity as needed."""
    # Ensure password is at least 8 characters with one digit and one uppercase letter
    pattern = r"^(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,}$"
    return re.match(pattern, password) is not None
