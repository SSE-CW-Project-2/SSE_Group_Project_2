####################################################################################################
# Project Name: Motion Event Management System
# File: user_routes.py
# Description: Defines the Flask routes for handling user-related operations within the Event
#              Management System. This includes endpoints for user registration, authentication
#              (login), and profile updates. The routes serve as the interface between the
#              frontend and the service layer, processing incoming HTTP requests, utilizing
#              validators for input validation, and invoking the appropriate services to
#              execute business logic.
#
#              The file leverages Flask Blueprints to organize and manage these routes, offering
#              a modular and scalable approach to route management. Authentication and session
#              management are integral to securing these routes and ensuring that users can only
#              access and modify their own data.
#
# Authors:
# Date: 2024-02-14
# Version: 1.0
#
# Notes: Future enhancements may include more complex user interactions or integration with
#        third-party authentication services.
####################################################################################################

from flask import Blueprint, request, jsonify
from services.user_service import create_user, authenticate_user, update_user
from utils.validators import validate_email, validate_password

user_bp = Blueprint('user_bp', __name__)


@user_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    # Basic validation
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
    if not validate_email(email):
        return jsonify({'error': 'Invalid email format'}), 400
    if not validate_password(password):
        return jsonify({'error': 'Password does not meet complexity requirements'}), 400

    # Attempt to create a new user
    result = create_user(data)
    if result.get('error'):
        return jsonify(result), 400

    return jsonify({'message': 'User registered successfully'}), 201


@user_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    auth_result = authenticate_user(email, password)
    if auth_result.get('error'):
        return jsonify(auth_result), 401

    return jsonify({'message': 'Login successful', 'token': auth_result.get('token')}), 200


@user_bp.route('/update-profile', methods=['POST'])
def update_profile():
    # This would require authentication to get the user_id
    user_id = request.headers.get('user_id')  # Simplified example
    data = request.get_json()

    update_result = update_user(user_id, data)
    if update_result.get('error'):
        return jsonify(update_result), 400

    return jsonify({'message': 'Profile updated successfully'}), 200

# Remember to register user_bp in your app.py or where we initialize the Flask app
# app.register_blueprint(user_bp, url_prefix='/user')
