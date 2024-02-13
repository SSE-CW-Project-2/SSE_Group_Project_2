from flask import Flask, render_template, request, redirect, url_for, session
from functools import wraps

app = Flask(__name__)

app.secret_key = '3w45768j6565t6879m0'

example_events = [{
            'name': 'Event 1',
            'date': '01/01/2020',
            'location': 'Location 1',
            'description': 'Example description for Event 1',
            'capacity': 100,
            'price': 10.99
},
{
    'name': 'Event 2',
    'date': '01/02/2020',
    'location': 'Location 2',
    'description': 'Example description for Event 2',
    'capacity': 50,
    'price': 15.99
},
{
    'name': 'Event 3',
    'date': '01/03/2020',
    'location': 'Location 3',
    'description': 'Example description for Event 3',
    'capacity': 200,
    'price': 20.99
}]

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
        if username == 'admin' and password == 'password':
            # Log the user in by setting a session variable
            session['logged_in'] = True
            session['user type'] = 'customer'
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

if __name__ == '__main__':
    app.run(debug=True)