from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps

app = Flask(__name__)

app.secret_key = '3w45768j6565t6879m0'

example_events = [{
            'name': 'Event 1',
            'date': '01/01/2020',
            'location': 'Location 1',
            'description': 'Example description for Event 1',
            'capacity': 100,
            'price': 10.99,
            'id': 1
},
{
    'name': 'Event 2',
    'date': '01/02/2020',
    'location': 'Location 2',
    'description': 'Example description for Event 2',
    'capacity': 50,
    'price': 15.99,
    'id': 2
},
{
    'name': 'Event 3',
    'date': '01/03/2020',
    'location': 'Location 3',
    'description': 'Example description for Event 3',
    'capacity': 200,
    'price': 20.99,
    'id': 3
}]

### TODO: Make sure the venue is the correct one ######################
def venue_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in', False):
            return redirect(url_for('login', next=request.url))
        if session.get('user type', False) != 'venue':
            # If the user is not a customer, redirect to the home page
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function


def customer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in', False):
            return redirect(url_for('login', next=request.url))
        if session.get('user type', False) != 'customer':
            # If the user is not a customer, redirect to the home page
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function


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
    return render_template('index.html', logged_in=session.get('logged_in', False))

@app.route('/login', methods=['GET', 'POST'])
def login():
    session['logged_in'] = False
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        ### TODO: CALL TO DATABASE TO CHECK IF USER EXISTS AND PASSWORD IS CORRECT

        ### IF SO, GET THE USER TYPE #############################################
        if username == 'customer' and password == 'password':
            # Log the user in by setting a session variable
            session['logged_in'] = True
            session['user type'] = 'customer'
            next_page = request.form.get('next') or url_for('home')
            return redirect(next_page)
        elif username == 'venue' and password == 'password':
            # Log the user in by setting a session variable
            session['logged_in'] = True
            session['user type'] = 'venue'
            next_page = request.form.get('next') or url_for('home')
            return redirect(next_page)
        else:
            # If login fails, return to login page with an error
            return render_template('login.html', error=True, next=request.form.get('next'))

    # Handle the GET request
    next_page = request.args.get('next', url_for('home'))
    return render_template('login.html', next=next_page)

@app.route('/logout')
def logout():
    session['logged_in'] = False
    return redirect(url_for('home'))

@app.route('/events')
@login_required
def events():
    ### TODO: CALL TO DATABASE TO GET EVENTS FOR USER ###

    ### PLACEHOLDER FOR NOW #############################################
    events = example_events
    return render_template('events.html', user_type=session['user type'], events=events)


@app.route('/buy/<id>', methods=['GET', 'POST'])
@customer_required
def buy_event(id):
    ### TODO: CALL TO DATABASE TO GET EVENT DETAILS ###
    event = None
    for e in example_events:
        if e['id'] == int(id):
            event = e
            break
    if event is None:
        return "Event not found"
    return render_template('buy.html', event=event)


@app.route('/checkout/<id>', methods=['GET', 'POST'])
@customer_required
def checkout(id):
    return render_template('checkout.html', event_id=id)


@app.route('/manage/<id>', methods=['GET', 'POST'])
@venue_required
def manage_event(id):
    ### TODO: CALL TO DATABASE TO GET EVENT DETAILS ###
    event = None
    for e in example_events:
        if e['id'] == int(id):
            event = e
            break
    if event is None:
        return "Event not found"
    return render_template('manage.html', event=event)


@app.route('/delete/<id>', methods=['GET', 'POST'])
@venue_required
def delete_event(id):
    ### TODO: Functionality to delete an event
    ### This does nothing ############################################
    flash('Event deleted', 'success')
    return redirect(url_for('events'))


if __name__ == '__main__':
    app.run(debug=True)