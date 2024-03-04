from flask import Flask, request, session, redirect, url_for, render_template, flash
from flask_dance.contrib.google import make_google_blueprint, google
import os
from functools import wraps
from werkzeug.middleware.proxy_fix import ProxyFix
from .auth import make_authorized_request

# FLASK SETUP #
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "your_default_secret_key")
app.config['SESSION_COOKIE_SECURE'] = True
app.config['PREFERRED_URL_SCHEME'] = 'https'
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1)  # type: ignore


# GOOGLE AUTH SETUP #
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


# DECORATORS #
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


# HELPER FUNCTIONS #
def is_user_new(email):
    # Hardcoded list of existing user emails
    existing_users = ['juliusgasson@gmail.com']
    return email not in existing_users


def save_user_session_data(account_info_json):
    # Save necessary user info in the session
    session['user_email'] = account_info_json.get('email', '')
    session['user_name'] = account_info_json.get('name', '')
    session['profile_picture'] = account_info_json.get('picture', '')
    session['user_id'] = account_info_json.get('id', '')


# ROUTES #

# GENERAL ROUTES #
@app.route("/")
def home():
    authorized = session.get("logged_in", False) and google.authorized
    return render_template("index.html", authorized=authorized)


@app.route("/events")
@login_required
def events():
    user_type = session.get("user_type")
    id_ = session.get("user_id")
    if user_type == "venue":
        event_data = make_authorized_request("/get_events_for_venue", {"venue_id": id_}, "GET")
    elif user_type == "artist":
        event_data = make_authorized_request("/get_events_for_artist", {"artist_id": id_}, "GET")
    else:
        event_data = make_authorized_request("/get_events_for_attendee", {"attendee_id": id_}, "GET")
    return render_template("events.html", user_type, events=event_data.json())


# ACCOUNT MANAGEMENT #
@app.route("/login")
def login():
    authorized = session.get("logged_in", False) and google.authorized
    if not authorized:
        return redirect(url_for("google.login"))
    return redirect(url_for("home"))


@app.route("/after_login")
def after_login():
    account_info = google.get("/oauth2/v2/userinfo")
    if account_info.ok:
        account_info_json = account_info.json()
        session['logged_in'] = True
        email = account_info_json.get("email")
        headers = {
            "email": email,
        }
        response = make_authorized_request("/check_email_in_use", request=headers)
        if response.status_code == 404:
            print(response.json())
            # Save minimal info and redirect to location capture page
            save_user_session_data(account_info_json)  # Save or update session data
            return redirect(url_for("set_profile"))
        elif response.status_code == 200:
            session["user_type"] = response.json()["object_type"]
            # User exists, proceed to save or update session data and redirect home
            save_user_session_data(account_info_json)
            headers = {
                "identifier": session.get("user_id"),
                "attributes": {
                    "object_type": True,
                }
            }
            return redirect(url_for("home"))
        else:
            print(response.json())
            return "Failed to create account. Please try again later."
    return "Failed to fetch user info"


@app.route("/profile")
@login_required
def profile():
    user_info = session.get("user_info", {})
    if not user_info:
        user_info = google.get("/oauth2/v2/userinfo").json()
        session["user_info"] = user_info
    profile_picture = session.get("profile_picture", "")
    account_info = session["user_info"]
    return render_template("profile.html",
                           user_info=user_info,
                           profile_picture=profile_picture,
                           account_info=account_info)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/set_profile", methods=["GET", "POST"])
@login_required
def set_profile(function="create"):
    if request.method == "POST":
        user_type = request.form.get("user_type")
        session["user_type"] = user_type
        account_info_json = google.get("/oauth2/v2/userinfo").json()
        identifier = account_info_json.get('id')
        create_request = {
            "function": "create",
            "object_type": user_type,
            "identifier": identifier,
            "attributes": {
                "user_id": identifier,
                "email": request.form.get("email"),
                "street_address": request.form.get("street_address"),
                "city": request.form.get("city"),
                "postcode": request.form.get("postcode")
            }
        }
        if user_type == "venue":
            create_request["attributes"]["venue_name"] = request.form.get("venue_name")
        elif user_type == "artist":
            create_request["attributes"]["artist_name"] = request.form.get("artist_name")
            create_request["attributes"]["genres"] = request.form.get("genres")
            create_request["attributes"]["spotify_artist_id"] = request.form.get("spotify_artist_id")
        elif user_type == "customer":
            create_request["attributes"]["first_name"] = request.form.get("user_name")
            create_request["attributes"]["last_name"] = request.form.get("last_name")
        response = make_authorized_request("/create_account", create_request)
        if response.status_code == 200:
            session["user_id"] = identifier
            flash("Account created", "success")
            return redirect(url_for("home"))
        else:
            flash("Failed to create account", "error")
            print(response.json())
            return redirect(url_for("set_profile"))
    return render_template("set_profile.html")


@login_required
@app.route("/delete_account", methods=["GET", "POST"])
def delete_account():
    if request.method == "POST":
        delete_request = {
            "function": "delete",
            "object_type": session.get("user_type"),
            "identifier": session.get("user_id")
        }
        response = make_authorized_request("/delete_account", delete_request, "DELETE")
        if response.status_code == 200:
            session.clear()
            flash("Account deleted", "success")
            return redirect(url_for("home"))
        else:
            flash("Failed to delete account", "error")
            print(response.json())
            return redirect(url_for("delete_account"))
    return render_template("delete_account.html")


@login_required
@app.route("/update_account", methods=["GET", "POST"])
def update_account():
    if request.method == "POST":
        update_attrs = {k: v for k, v in request.form.to_dict().items() if v != ""}
        headers = {
            "function": "update",
            "object_type": session.get("user_type"),
            "identifier": session.get("user_id"),
            "attributes": update_attrs,
        }
        make_authorized_request("/update_account", request=headers)
    return render_template("update_account.html", user_type=session.get("user_type"))


# CUSTOMER SPECIFIC ROUTES #
@one_user_type_allowed("customer")
@app.route("/buy/<id>", methods=["GET", "POST"])
def buy_event(id):
    # TODO: CALL TO DATABASE TO GET EVENT DETAILS ###
    event_data = make_authorized_request("/get_event_info", {"event_id": id})
    session["event_info"] = event_data.json()
    return render_template("buy.html", event=event_data.json())


@one_user_type_allowed("customer")
@app.route("/checkout/<event_id>", methods=["GET", "POST"])
def checkout(event_id):
    if session.get("event_info") and session.get("event_info").get("event_id") == event_id:
        event = session.get("event_info")
    else:
        event = make_authorized_request("/get_event_info", {"event_id": event_id}).json()
        session["event_info"] = event
    return render_template("checkout.html", event=event)


@one_user_type_allowed("customer")
@app.route("/purchase_ticket/<event_id>", methods=["GET", "POST"])
def purchase_ticket(event_id):
    if request.method == "POST":
        ticket_request = {
            "function": "create",
            "object_type": "ticket",
            "attributes": {
                "event_id": event_id,
                "attendee_id": session.get("user_id"),
            }
        }
        response = make_authorized_request("/purchase_ticket", ticket_request)
        if response.status_code == 200:
            flash("Ticket(s) purchased", "success")
            return redirect(url_for("events"))
        else:
            flash("Failed to purchase ticket", "error")
            print(response.json())
            return redirect(url_for("buy_event", id=event_id))
    if session.get("event_info") and session.get("event_info").get("event_id") == event_id:
        event = session.get("event_info")
    else:
        event = make_authorized_request("/get_event_info", {"event_id": event_id}, "GET").json()
    return render_template("purchase_ticket.html", event=event)


# VENUE SPECIFIC ROUTES #
@one_user_type_allowed("venue")
@app.route("/manage/<event_id>", methods=["GET", "POST"])
def manage_event(event_id):
    if event_id not in session.get("user_events"):
        flash("You are not authorized to delete this event", "error")
        return redirect(url_for("events"))
    event_data = make_authorized_request("/get_event_info", {"event_id": event_id}, "GET").json()
    session["event_info"] = event_data
    return render_template("manage.html", event=event_data)


@one_user_type_allowed("venue")
@app.route("/delete/<event_id>")
def delete_event(event_id):
    if event_id not in session.get("user_events"):
        flash("You are not authorized to delete this event", "error")
        return redirect(url_for("events"))
    make_authorized_request("/delete_event", {"event_id": event_id}, "DELETE")
    flash("Event deleted", "success")
    return redirect(url_for("events"))


@one_user_type_allowed("venue")
@app.route("/create_event", methods=["GET", "POST"])
def create_event():
    if request.method == "POST":
        event_name = request.form.get("event_name")
        event_date = request.form.get("event_date")
        event_location = request.form.get("event_location")
        event_description = request.form.get("event_description")
        event_capacity = request.form.get("event_capacity")
        event_price = request.form.get("event_price")
        create_request = {
            "function": "create",
            "object_type": "event",
            "attributes": {
                "event_name": event_name,
                "event_date": event_date,
                "event_location": event_location,
                "event_description": event_description,
                "event_capacity": event_capacity,
                "event_price": event_price,
                "venue_id": session.get("user_id")
            }
        }
        response = make_authorized_request("/create_event", create_request)
        if response.status_code == 200:
            flash("Event created", "success")
            return redirect(url_for("events"))
        else:
            flash("Failed to create event", "error")
            print(response.json())
            return redirect(url_for("create_event"))
    return render_template("create_event.html")


@one_user_type_allowed("venue")
@app.route("/update/<event_id>")
def update_event(event_id, methods=["GET", "POST"]):
    if event_id not in session.get("user_events"):
        flash("You are not authorized to update this event", "error")
        return redirect(url_for("events"))
    if request.method == "POST":
        update_attrs = request.form.to_dict()
        make_authorized_request("/update_event", {"event_id": event_id, "update_attrs": update_attrs})
    flash("Event updated", "success")
    return redirect(url_for("manage_event", event_id=event_id))


if __name__ == "__main__":
    app.run(debug=True)
