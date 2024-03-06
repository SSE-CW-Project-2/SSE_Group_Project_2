from flask import Flask, request, session, redirect, url_for, render_template, flash
from flask_dance.contrib.google import make_google_blueprint, google
import os
from functools import wraps
from werkzeug.middleware.proxy_fix import ProxyFix
from .auth import make_authorized_request
from .countries import countries_list as countries
from datetime import datetime
import bleach

# FLASK SETUP #
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "klasdnaslkdalaklsdnasfjao")
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


def save_user_session_data(account_info_json):
    session['profile_picture'] = account_info_json.get('picture', '')


# ROUTES #

# GENERAL ROUTES #
@app.route("/")
def home():
    authorized = session.get("logged_in", False) and google.authorized
    return render_template("index.html", authorized=authorized)


@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "GET":
        return render_template("search.html", cities=[], countries=countries)
    elif request.method == "POST":
        form_city = bleach.clean(request.form.get("city"))
        if form_city:
            city = form_city
            req = {
                "function": "get",
                "object_type": "event",
                "identifier": city
            }
            status_code, resp_content = make_authorized_request("/get_events_in_city", req)
            if status_code != 200:
                return "Failed to fetch events"
            events = resp_content.get("message").get("data")
            for event in events:
                timestamp = event["date_time"]
                dt_object = datetime.fromisoformat(timestamp)
                date = dt_object.date()
                time = dt_object.strftime("%H:%M")
                event["date"] = date
                event["time"] = time
            return render_template("events.html", events=events)
        country = bleach.clean(request.form.get("country"))
        req = {
            "function": "get",
            "object_type": "city",
            "identifier": country
        }
        status_code, resp_content = make_authorized_request("/get_cities_by_country", req)
        if status_code != 200:
            print(status_code, resp_content)
            return "Failed to fetch cities"
        cities = resp_content.get("message").get("data")
        return render_template("search.html", cities=cities, countries=[])


@app.route("/events", methods=["GET", "POST"])
@login_required
def events():
    user_type = session.get("user_type")
    id_ = session.get("user_id", None)
    req = {
        "function": "get",
        "object_type": "event",
        "identifier": id_,
    }
    if user_type == "venue":
        status_code, event_data = make_authorized_request("/get_events_for_venue", req)
    elif user_type == "artist":
        status_code, event_data = make_authorized_request("/get_events_for_artist", req)
    elif user_type == "attendee":
        return redirect(url_for("search"))
    if status_code != 200:
        print(status_code, event_data)
        return "Failed to fetch events"
    data = event_data.get("message").get("data")
    for event in data:
        timestamp = event["date_time"]
        dt_object = datetime.fromisoformat(timestamp)
        date = dt_object.date()
        time = dt_object.strftime("%H:%M")
        event["date"] = date
        event["time"] = time
        event.pop("date_time")
    return render_template("events.html", user_type=user_type, events=data)


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
        id_ = account_info_json.get("id")
        headers = {
            "id": id_,
        }
        session["user_id"] = id_
        status_code, resp_content = make_authorized_request("/check_email_in_use", request=headers)
        if status_code == 200:
            if resp_content.get("message") == "Account does not exist.":
                # Save minimal info and redirect to location capture page
                save_user_session_data(account_info_json)  # Save or update session data
                return redirect(url_for("set_profile"))
            session.update(resp_content)
            print(resp_content)
            user_type = resp_content["account_type"]
            session["user_type"] = user_type
            if user_type == "venue":
                session["name"] = resp_content["venue_name"]
            elif user_type == "artist":
                session["name"] = resp_content["artist_name"]
            elif user_type == "attendee":
                session["name"] = resp_content["first_name"]
            else:
                print("User type not recognized")
            # User exists, proceed to save or update session data and redirect home
            save_user_session_data(resp_content)
            return redirect(url_for("home"))
        else:
            print(resp_content)
            flash("Failed to create account. Please try again later.", "error")
            return redirect(url_for("home"))
    return "Failed to fetch user info"


@app.route("/profile/<user_id>")
@login_required
def profile(user_id, account_type="venue"):
    user_info = session.get("user_info", {})
    user_info["user_type"] = session.get("user_type")
    if not session.get("user_info"):
        user_info = google.get("/oauth2/v2/userinfo").json()
        session["user_info"] = user_info
    if session["user_id"] != user_id:
        req = {
            "function": "get",
            "object_type": account_type,
            "identifier": user_id
        }
        print(req)
        status_code, resp_content = make_authorized_request("/get_account_info", req)
        if status_code != 200:
            print(status_code, resp_content)
            return "Failed to fetch user info"
        else:leach.clean(ure,
                           account_info=account_info,
                           user_type=session["user_type"])


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/set_profile", methods=["GET", "POST"])
@login_required
def set_profile(function="create"):
    if request.method == "POST":
        user_type = bleach.clean(request.form.get("user_type"))
        session["user_type"] = user_type
        account_info_json = google.get("/oauth2/v2/userinfo").json()
        identifier = account_info_json.get('id')
        create_request = {
            "function": "create",
            "object_type": user_type,
            "identifier": identifier,
            "attributes": {
                "user_id": identifier,
                "email": bleach.clean(request.form.get("email")),
                "street_address": bleach.clean(request.form.get("street_address")),
                "city": bleach.clean(request.form.get("city")),
                "postcode": bleach.clean(request.form.get("postcode")),
                "bio": bleach.clean(request.form.get("bio")),
            }
        }

        if user_type == "venue":
            create_request["attributes"]["venue_name"] = bleach.clean(request.form.get("venue_name"))
        elif user_type == "artist":
            create_request["attributes"]["artist_name"] = bleach.clean(request.form.get("artist_name"))
            create_request["attributes"]["genres"] = bleach.clean(request.form.get("genres"))
            create_request["attributes"]["spotify_artist_id"] = bleach.clean(request.form.get("spotify_artist_id"))
        elif user_type == "attendee":
            create_request["attributes"]["first_name"] = bleach.clean(request.form.get("user_name"))
            create_request["attributes"]["last_name"] = bleach.clean(request.form.get("last_name"))
        print(create_request)
        status_code, resp_content = make_authorized_request("/create_account", create_request)
        session.update(create_request["attributes"])
        if status_code == 200:
            session["user_id"] = identifier
            flash("Account created", "success")
            return redirect(url_for("home"))
        else:
            flash("Failed to create account", "error")
            print(status_code, resp_content)
            return redirect(url_for("set_profile"))
    return render_template("set_profile.html", countries=countries)


@login_required
@app.route("/delete_account", methods=["GET", "POST"])
def delete_account():
    if request.method == "POST":
        delete_request = {
            "function": "delete",
            "object_type": session.get("user_type"),
            "identifier": session.get("user_id"),
        }
        status_code, resp_content = make_authorized_request("/delete_account", delete_request)
        if status_code == 200:
            session.clear()
            flash("Account deleted", "success")
            return redirect(url_for("home"))
        else:
            flash("Failed to delete account", "error")
            print(status_code, resp_content)
            return redirect(url_for("delete_account"))
    return render_template("delete_account.html")


@login_required
@app.route("/update_account", methods=["GET", "POST"])
def update_account():
    if request.method == "POST":
        update_attrs = request.form.to_dict()
        sanitised_attrs = {key: bleach.clean(value) for key, value in update_attrs.items()}
        headers = {
            "function": "update",
            "object_type": session.get("user_type"),
            "identifier": session.get("user_id"),
            "attributes": sanitised_attrs,
        }
        make_authorized_request("/update_account", request=headers)
        session.update(sanitised_attrs)
        return redirect(url_for("profile", user_id=session.get("user_id")))
    return render_template("update_account.html", user_type=session["user_type"])


# ATTENDEE SPECIFIC ROUTES #
@one_user_type_allowed("attendee")
@app.route("/buy/<event_id>", methods=["POST"])
def buy_event(event_id):
    event_data = {}
    update_attrs = request.form.to_dict()
    sanitised_attrs = {key: bleach.clean(value) for key, value in update_attrs.items()}
    event_data.update(sanitised_attrs)
    session["event_info"] = event_data
    print(session.get("event_info"))
    return render_template("buy.html", event=event_data, event_id=event_id)


@app.route("/checkout/<event_id>", methods=["GET", "POST"])
def checkout(event_id):
    if session.get("event_info") and session.get("event_info").get("event_event_id") == event_id:
        event = session.get("event_info")
    else:
        event = make_authorized_request("/get_event_info", {
                                        "identifier": event_id,
                                        "function": "get",
                                        "object_type": "event"
                                        })
        session["event_info"] = event
    return render_template("checkout.html", event=event, event_id=event_id)


@one_user_type_allowed("attendee")
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
        event = make_authorized_request("/get_event_info", {
                                            "identifier": event_id,
                                            "function": "get",
                                            "object_type": "event"
                                            })
    return render_template("purchase_ticket.html", event=event, event_id=event_id)


# VENUE SPECIFIC ROUTES #
@one_user_type_allowed("venue")
@app.route("/manage/<event_id>", methods=["GET", "POST"])
def manage_event(event_id):
    if event_id not in session.get("user_events"):
        flash("You are not authorized to delete this event", "error")
        return redirect(url_for("events"))
    event_data = make_authorized_request("/get_event_info", {
                                            "identifier": event_id,
                                            "function": "get",
                                            "object_type": "event"
                                         })
    session["event_info"] = event_data
    return render_template("manage.html", event=event_data)


@one_user_type_allowed("venue")
@app.route("/delete/<event_id>")
def delete_event(event_id):
    if event_id not in session.get("user_events"):
        flash("You are not authorized to delete this event", "error")
        return redirect(url_for("events"))
    make_authorized_request("/delete_event", {"identifier": event_id, "function": "get", "object_type": "event"})
    flash("Event deleted", "success")
    return redirect(url_for("events"))


@one_user_type_allowed("venue")
@app.route("/create_event", methods=["GET", "POST"])
def create_event():
    if request.method == "POST":
        event_name = bleach.clean(request.form.get("event_name"))
        event_date = bleach.clean(request.form.get("event_date"))
        # event_address = session.get("street_address")
        # event_postcode = session.get("postcode")
        # event_city = session.get("city")
        event_description = bleach.clean(equest.form.get("event_description"))
        event_capacity = bleach.clean(request.form.get("event_capacity"))
        event_price = bleach.clean(request.form.get("event_price"))
        create_request = {
            "function": "create",
            "object_type": "event",
            "attributes": {
                "event_name": event_name,
                "event_date": event_date,
                # "event_location": event_location,
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
@app.route("/update/<event_id>", methods=["GET", "POST"])
def update_event(event_id):
    if event_id not in session.get("user_events"):
        flash("You are not authorized to update this event", "error")
        return redirect(url_for("events"))
    if request.method == "POST":
        update_attrs = request.form.to_dict()
        sanitised_attrs = {key: bleach.clean(value) for key, value in update_attrs.items()}
        make_authorized_request("/update_event", {"event_id": event_id, "update_attrs": sanitised_attrss})
    flash("Event updated", "success")
    return redirect(url_for("manage_event", event_id=event_id))


if __name__ == "__main__":
    app.run(debug=True)
