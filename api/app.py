from flask import Flask, request, session, redirect, url_for, render_template
# from google.oauth2 import id_token
# from google.auth.transport import requests as google_requests
from flask_dance.contrib.google import make_google_blueprint, google
import os
from functools import wraps
from werkzeug.middleware.proxy_fix import ProxyFix


example_events = [
    {
        "name": "Event 1",
        "date": "01/01/2020",
        "location": "Location 1",
        "description": "Example description for Event 1",
        "capacity": 100,
        "price": 10.99,
        "event_id": 1,
        "venue_id": 1,
    },
    {
        "name": "Event 2",
        "date": "01/02/2020",
        "location": "Location 2",
        "description": "Example description for Event 2",
        "capacity": 50,
        "price": 15.99,
        "event_id": 2,
        "venue_id": 2,
    },
    {
        "name": "Event 3",
        "date": "01/03/2020",
        "location": "Location 3",
        "description": "Example description for Event 3",
        "capacity": 200,
        "price": 20.99,
        "event_id": 3,
        "venue_id": 1,
    },
]

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "your_default_secret_key")
app.config['SESSION_COOKIE_SECURE'] = True
app.config['PREFERRED_URL_SCHEME'] = 'https'
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1)  # type: ignore

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")

google_blueprint = make_google_blueprint(
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    scope=[
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "openid",
    ],
    redirect_to="after_login",
)

app.register_blueprint(google_blueprint, url_prefix="/login")


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not google.authorized:
            # If the user is not logged in, redirect to the login page
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def one_user_type_allowed(user_type):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not google.authorized:
                return redirect(url_for("login", next=request.url))
            if session.get("user_type", "") != user_type:
                return redirect(url_for("home"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@app.route("/after_login")
def after_login():
    account_info = google.get("/oauth2/v2/userinfo")
    if account_info.ok:
        account_info_json = account_info.json()
        session["user_info"] = account_info_json
        if False:  # IF USER CAN BE FOUND IN DATABASE
            pass
        if True:  # IF USER CAN'T BE FOUND IN DATABASE
            pass
        session['logged_in'] = True
        return redirect(url_for("home"))
    return "Failed to fetch user info"


@app.route("/login")
def login():
    authorized = session.get("logged_in", False) and google.authorized
    if not authorized:
        return redirect(url_for("google.login"))
    return redirect(url_for("home"))


@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html")


@app.route("/logout")
def logout():
    # Clear the user's session
    session.clear()
    return redirect(url_for("home"))


@app.route("/")
def home():
    authorized = session.get("logged_in", False) and google.authorized
    return render_template("index.html", authorized=authorized)


@app.route("/events")
@login_required
def events():
    # TODO: CALL TO DATABASE TO GET EVENTS FOR USER ###
    # PLACEHOLDER FOR NOW #############################################
    events = example_events
    session["user_type"] = "customer"  # CHANGE THIS
    session["user_id"] = 1
    authorized = session.get("logged_in", False) and google.authorized
    if session["user_type"] == "venue":
        events = [e for e in events if e["venue_id"] == session.get("user_id")]
    return render_template("events.html", user_type=session["user_type"], events=events, authorized=authorized)


@app.route("/buy/<id>", methods=["GET", "POST"])
def buy_event(id):
    # TODO: CALL TO DATABASE TO GET EVENT DETAILS ###
    event = None
    authorized = session.get("logged_in", False) and google.authorized
    for e in example_events:
        if e["event_id"] == int(id):
            event = e
            break
    if event is None:
        return "Event not found"
    return render_template("buy.html", event=event, authorized=authorized)


@app.route("/checkout/<event_id>", methods=["GET", "POST"])
def checkout(event_id):
    authorized = session.get("logged_in", False) and google.authorized
    return render_template("checkout.html", event_id=event_id, authorized=authorized)


@app.route("/manage/<event_id>", methods=["GET", "POST"])
def manage_event(event_id):
    # TODO: CALL TO DATABASE TO GET EVENT DETAILS ###
    event = None
    for e in example_events:
        if e["event_id"] == int(event_id):
            event = e
            break
    if event is None:
        return "Event not found"
    authorized = session.get("logged_in", False) and google.authorized
    return render_template("manage.html", event=event, authorized=authorized)


if __name__ == "__main__":
    app.run(debug=True)
