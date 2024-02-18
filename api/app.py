from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash
)
from authlib.integrations.flask_client import OAuth
from functools import wraps
import os
import google.oauth2.id_token
import google.auth.transport.requests

app = Flask(__name__)

# Load sensitive information from environment variables for security
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'optional_default_key')

# Configure Authlib OAuth registry
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id='950999785047-1csqo80m63b1ppeiv4dcc12ol7t8phuf.apps.googleusercontent.com',
    client_secret='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',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',
    client_kwargs={'scope': 'openid email profile'},
)



# app.secret_key = '3w45768j6565t6879m0'  # I mashed the keyboard here

example_events = [{
            'name': 'Event 1',
            'date': '01/01/2020',
            'location': 'Location 1',
            'description': 'Example description for Event 1',
            'capacity': 100,
            'price': 10.99,
            'event_id': 1,
            'venue_id': 1
    },
    {
        'name': 'Event 2',
        'date': '01/02/2020',
        'location': 'Location 2',
        'description': 'Example description for Event 2',
        'capacity': 50,
        'price': 15.99,
        'event_id': 2,
        'venue_id': 2
    },
    {
        'name': 'Event 3',
        'date': '01/03/2020',
        'location': 'Location 3',
        'description': 'Example description for Event 3',
        'capacity': 200,
        'price': 20.99,
        'event_id': 3,
        'venue_id': 1
    }
]


# TODO: Make sure the venue is the correct one ######################


def requires_correct_venue_id(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # TODO: REPLACE THIS WITH A CALL TO THE DATABASE TO GET THE USER ID
        event = example_events[int(kwargs['event_id']) - 1]
        event_venue_id = event['venue_id']
        current_user_id = session.get('user_id')
        if current_user_id is None or \
                str(current_user_id) != str(event_venue_id):
            flash('Unauthorized access.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function


def one_user_type_allowed(user_type):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('logged_in', False):
                return redirect(url_for('login', next=request.url))
            if session.get('user_type', '') != user_type:
                return redirect(url_for('home'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in', False):
            # If the user is not logged in, redirect to the login page
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/register')
def register():
    return render_template('register.html')


@app.route('/add-user', methods=['POST'])
def add_user():
    user = request.form.get('username')
    password = request.form.get('password')
    password  # Added so flake8 doesn't complain
    user_type = request.form.get('user_type')
    # TODO: Check username is not already taken and add user to database
    # Also assign a user ID to the user and store it in the session

    if True:  # For now, all users are successfully added
        session['logged_in'] = True
        session['username'] = user
        # Assuming 'customer' as a default user type, modify as necessary
        session['user_type'] = user_type
        return redirect(url_for('home'))
    if False:
        # Use a more specific error message
        flash('Error adding user', 'error')
        return render_template('register.html', error=True)


@app.route('/login', methods=['GET', 'POST'])
def login():
    session['logged_in'] = False
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # TODO: CALL TO DATABASE TO CHECK IF LOGIN INFO IS CORRECT ###

        # IF SO, GET THE USER TYPE ##################################
        if password == 'password' and (
           username in ['customer', 'venue', 'performer']):
            session['logged_in'] = True
            session['user_type'] = username  # GET FROM DATABASE
            session['username'] = username
            session['user_id'] = 1  # GET FROM DATABASE
            next_page = request.form.get('next') or url_for('home')
            return redirect(next_page)
        else:
            return render_template('login.html',
                                   error=True,
                                   next=request.form.get('next'))
    if request.method == 'GET':
        next_page = request.args.get('next', url_for('home'))
        return render_template('login.html', next=next_page)


@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')


@app.route('/logout')
def logout():
    session['logged_in'] = False
    session['user_type'] = None
    session['username'] = None
    return redirect(url_for('home'))


@app.route('/events')
@login_required
def events():
    # TODO: CALL TO DATABASE TO GET EVENTS FOR USER ###
    # PLACEHOLDER FOR NOW #############################################
    events = example_events
    if session['user_type'] == 'venue':
        events = [e for e in events if e['venue_id'] == session.get('user_id')]
    return render_template('events.html',
                           user_type=session['user_type'],
                           events=events)


@app.route('/buy/<id>', methods=['GET', 'POST'])
@one_user_type_allowed(user_type='customer')
def buy_event(id):
    # TODO: CALL TO DATABASE TO GET EVENT DETAILS ###
    event = None
    for e in example_events:
        if e['event_id'] == int(id):
            event = e
            break
    if event is None:
        return "Event not found"
    return render_template('buy.html', event=event)


@app.route('/checkout/<event_id>', methods=['GET', 'POST'])
@one_user_type_allowed(user_type='customer')
def checkout(event_id):
    return render_template('checkout.html', event_id=event_id)


@app.route('/manage/<event_id>', methods=['GET', 'POST'])
@requires_correct_venue_id
def manage_event(event_id):
    # TODO: CALL TO DATABASE TO GET EVENT DETAILS ###
    event = None
    for e in example_events:
        if e['event_id'] == int(event_id):
            event = e
            break
    if event is None:
        return "Event not found"
    return render_template('manage.html', event=event)


@app.route('/delete/<event_id>', methods=['GET', 'POST'])
@requires_correct_venue_id
def delete_event(event_id):

    # TODO: Functionality to delete an event
    # This does nothing ############################################
    flash('Event deleted', 'success')
    return redirect(url_for('events'))


@app.route('/google-login', methods=['POST'])
def google_login():
    # Extract the token from the request
    token = request.json.get('token')
    
    # Verify the token using Google's verifier
    try:
        idinfo = google.oauth2.id_token.verify_oauth2_token(token, google.auth.transport.requests.Request())
        
        # ID token is valid. Get the user's Google Account ID from the decoded token.
        userid = idinfo['sub']
        
        # Here, you could look up or create a user in your database, start a session, etc.
        # For now, let's just return a success message.
        return jsonify({'message': 'Google login successful', 'userid': userid}), 200
    except ValueError:
        # Invalid token
        return jsonify({'error': 'Invalid token'}), 403


if __name__ == '__main__':
    app.run(debug=True)
