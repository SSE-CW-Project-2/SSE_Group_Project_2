Project Structure
-----------------

/api
__init__.py: Initializes the Python package and often contains Flask app initialization code.
app.py: The entry point to the Flask application. Defines the Flask app and its routes.
app_test.py: Contains tests for the application's main functionality and routes.

/models
__init__.py: Makes the models directory a Python package.
user_model.py: Defines the User database model, including fields and methods related to user data.

/services
__init__.py: Makes the services directory a Python package.
user_service.py: Contains business logic for user-related operations, such as creating and validating users.

/routes
__init__.py: Makes the routes directory a Python package.
user_routes.py: Defines routes/endpoints related to user actions (e.g., sign-up, login).

/tests
Structured into unit and integration tests for thorough testing of models, services, and routes.
	/unit
	__init__.py: Makes the unit tests directory a Python package.
	test_user_model.py: Unit tests for the User model.
	/integration
	__init__.py: Makes the integration tests directory a Python package.
	test_user_routes.py: Integration tests for user-related routes.


