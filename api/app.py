from flask import Flask, request, session, redirect, url_for, render_template, flash
from flask_dance.contrib.google import make_google_blueprint, google  # type: ignore
import os
from functools import wraps
from werkzeug.middleware.proxy_fix import ProxyFix
from .auth import make_authorized_request
from .countries import countries_list as countries
from datetime import datetime
import bleach  # type: ignore

# FLASK SETUP #
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "klasdnaslkdalaklsdnasfjao")
app.config["SESSION_COOKIE_SECURE"] = True
app.config["PREFERRED_URL_SCHEME"] = "https"
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
        if session.get("status") == "Inactive":
            return redirect(url_for("deactivated"))
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
    session["profile_picture"] = account_info_json.get("picture", "")


# ROUTES #


# GENERAL ROUTES #
@app.route("/")
def home():
    authorized = session.get("logged_in", False) and google.authorized
    return render_template("index.html", authorized=authorized)


@one_user_type_allowed("attendee")
@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "POST":
        country = request.form.get("country")
        city = request.form.get("city")
        if city:
            # Clean the city input and store it in the session
            city = bleach.clean(city)
            session["city"] = city

            # Logic to handle fetching events based on the city
            req = {"function": "get", "object_type": "event", "identifier": city}
            status_code, resp_content = make_authorized_request(
                "/get_events_in_city", req
            )
            if status_code != 200:
                return "Failed to fetch events", status_code
            events = resp_content.get("message").get("data")

            # Convert timestamps to date and time
            events.sort(key=lambda event: datetime.fromisoformat(event["date_time"]))
            for event in events:
                dt_object = datetime.fromisoformat(event["date_time"])
                event["date"] = dt_object.date()
                event["time"] = dt_object.strftime("%H:%M")
            return render_template("events.html", events=events)
        elif country:
            # Clean the country input and store it in the session
            country = bleach.clean(country)
            session["country"] = country

            # Logic to handle fetching cities based on the country
            req = {"function": "get", "object_type": "city", "identifier": country}
            status_code, resp_content = make_authorized_request(
                "/get_cities_by_country", req
            )
            if status_code != 200:
                return "Failed to fetch cities", status_code
            cities = resp_content.get("message").get("data")

            # Render the search template with the list of cities and the selected country
            return render_template(
                "search.html",
                cities=cities,
                countries=countries,
                selected_country=country,
            )

    # For a GET request or if no country is selected yet, show the initial country selection form
    selected_country = session.get("country", "")
    return render_template(
        "search.html", countries=countries, selected_country=selected_country, cities=[]
    )


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
        if status_code != 200:
            flash("Failed to fetch events", "error")
            return redirect(url_for("home"))
        user_events = event_data.get("message").get("data")
        session["user_events"] = [event for event in user_events if event.get("status") != "Cancelled"]
    elif user_type == "artist":
        status_code, event_data = make_authorized_request("/get_events_for_artist", req)
    elif user_type == "attendee":
        city = session.get("city")
        if city:
            req = {"function": "get", "object_type": "event", "identifier": city}
            status_code, resp_content = make_authorized_request(
                "/get_events_in_city", req
            )
            if status_code != 200:
                return "Failed to fetch events"
            events = resp_content.get("message").get("data")
            events = [event for event in events if event.get("status") != "Cancelled"]
            events.sort(key=lambda event: datetime.fromisoformat(event["date_time"]))
            for event in events:
                timestamp = event["date_time"]
                dt_object = datetime.fromisoformat(timestamp)
                date = dt_object.date()
                time = dt_object.strftime("%H:%M")
                event["date"] = date
                event["time"] = time
            return render_template("events.html", events=events)
        return redirect(url_for("search"))
    else:
        session.clear()
        flash("You are not logged in", "error")
        return redirect(url_for("home"))
    if status_code != 200:
        flash("Failed to fetch events", "error")
        return redirect(url_for("home"))
    data = event_data.get("message").get("data")
    data = session.get("user_events") if user_type == "venue" else data
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
        session["logged_in"] = True
        id_ = account_info_json.get("id")
        headers = {
            "id": id_,
        }
        session["user_id"] = id_
        status_code, resp_content = make_authorized_request(
            "/check_email_in_use", request=headers
        )
        if resp_content.get("status") == "Inactive":
            session["status"] = "Inactive"
            return redirect(url_for("deactivated"))
        if status_code == 200:
            if resp_content.get("message") == "Account does not exist.":
                # Save minimal info and redirect to location capture page
                save_user_session_data(account_info_json)  # Save or update session data
                return redirect(url_for("set_profile"))
            session.update(resp_content)
            user_type = resp_content["account_type"]
            session["user_type"] = user_type
            if user_type == "venue":
                session["name"] = resp_content["venue_name"]
            elif user_type == "artist":
                session["name"] = resp_content["artist_name"]
            elif user_type == "attendee":
                session["name"] = resp_content["first_name"]
            # User exists, proceed to save or update session data and redirect home
            save_user_session_data(resp_content)
            return redirect(url_for("home"))
        else:
            flash("Failed to create account. Please try again later.", "error")
            return redirect(url_for("home"))
    return "Failed to fetch user info"


@app.route("/deactivated")
def deactivated():
    return render_template("deactivated.html")


@app.route("/profile/<user_id>")
@login_required
def profile(user_id, account_type="venue"):
    user_info = session.get("user_info", {})
    user_info["user_type"] = session.get("user_type")
    if not session.get("user_info"):
        user_info = google.get("/oauth2/v2/userinfo").json()
        session["user_info"] = user_info

    if session["user_id"] != user_id:
        attributes = {
                "bio": True,
            }
        if account_type == "venue":
            attributes.update({
                "venue_name": True,
                "street_address": True,
                "postcode": True,
                "city": True,
            })
        elif account_type == "artist":
            attributes.update({
                "artist_name": True,
                "genres": True,
                "spotify_artist_id": True,
            })
        elif account_type == "attendee":
            attributes.update({
                "first_name": True,
                "last_name": True,
            })
        req = {
            "function": "get",
            "object_type": account_type,
            "identifier": user_id,
            "attributes": attributes,
        }
        status_code, resp_content = make_authorized_request("/get_account_info", req)
        if status_code != 200:
            flash("Failed to fetch user info")
            return redirect(url_for("events"))
        else:
            profile_picture = resp_content.get("profile_picture", "")
            return render_template(
                "other_profile.html",
                user_info=resp_content['data'],
                profile_picture=profile_picture,
                account_type=account_type,
            )

    profile_picture = session.get("profile_picture", "")
    account_info = session["user_info"]
    return render_template(
        "profile.html",
        user_info=user_info,
        profile_picture=profile_picture,
        account_info=account_info,
        user_type=session["user_type"],
    )


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
        identifier = account_info_json.get("id")
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
            },
        }
        if user_type == "venue":
            create_request["attributes"]["venue_name"] = bleach.clean(
                request.form.get("venue_name")
            )
        elif user_type == "artist":
            create_request["attributes"]["artist_name"] = bleach.clean(
                request.form.get("artist_name")
            )
            create_request["attributes"]["genres"] = bleach.clean(
                request.form.get("genres")
            )
            create_request["attributes"]["spotify_artist_id"] = bleach.clean(
                request.form.get("spotify_artist_id")
            )
        elif user_type == "attendee":
            create_request["attributes"]["first_name"] = bleach.clean(
                request.form.get("user_name")
            )
            create_request["attributes"]["last_name"] = bleach.clean(
                request.form.get("last_name")
            )
        status_code, resp_content = make_authorized_request(
            "/create_account", create_request
        )
        if status_code == 400:
            session.clear()
            error_data = resp_content
            if "duplicate key value violates unique constraint" in error_data:
                flash("Email already in use", "error")
            return redirect(url_for("home"))
        if status_code == 200:
            session.update(create_request["attributes"])
            session["user_id"] = identifier
            flash("Account created", "success")
            return redirect(url_for("home"))
        else:
            flash("Failed to create account", "error")
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
        status_code, resp_content = make_authorized_request(
            "/delete_account", delete_request
        )
        if status_code == 200:
            session.clear()
            session["status"] = "Inactive"
            flash("Account deleted", "success")
            return redirect(url_for("home"))
        else:
            flash("Failed to delete account", "error")
            return redirect(url_for("delete_account"))
    return render_template("delete_account.html")


@login_required
@app.route("/update_account", methods=["GET", "POST"])
def update_account():
    if request.method == "POST":
        update_attrs = request.form.to_dict()
        sanitised_attrs = {
            key: bleach.clean(value) for key, value in update_attrs.items()
        }
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
    return render_template("buy.html", event=event_data, event_id=event_id)


@app.route("/checkout/<event_id>", methods=["GET", "POST"])
def checkout(event_id):
    total_tickets = int(session["event_info"]["event_total_tickets"])
    sold_tickets = int(session["event_info"]["event_sold_tickets"])
    tickets_left = total_tickets - sold_tickets
    if int(request.form.get("quantity")) > tickets_left:
        flash("Not enough tickets left", "error")
        session.pop("event_info")
        return redirect(url_for("events", id=event_id))
    reserve_request = {
        "identifier": event_id,
        "n_tickets": request.form.get("quantity"),
    }
    status_code, resp_content = make_authorized_request(
        "/reserve_tickets", reserve_request
    )
    if status_code == 400:
        flash("Tickets are sold out", "error")
        return redirect(url_for("events", id=event_id))
    elif status_code != 200:
        flash("Failed to reserve tickets", "error")
        return redirect(url_for("events", id=event_id))
    ticket_ids = resp_content["data"]
    session["ticket_ids"] = ticket_ids
    return render_template("checkout.html", event_id=event_id)


@one_user_type_allowed("attendee")
@app.route("/purchase_ticket/<event_id>", methods=["POST"])
def purchase_ticket(event_id):
    if (
        session.get("event_info") is None
        or session.get("event_info").get("event_event_id") != event_id
        or not session.get("ticket_ids")
    ):
        flash("You are not authorized to purchase tickets for this event", "error")
        return redirect(url_for("events"))
    ticket_request = {
        "function": "create",
        "object_type": "ticket",
        "identifier": session["user_id"],
        "ticket_ids": session.get("ticket_ids"),
    }
    status_code, resp_content = make_authorized_request(
        "/purchase_tickets", ticket_request
    )
    if status_code == 200:
        flash(
            "Ticket(s) purchased! You should receive the tickets in your email.",
            "success",
        )
        session.pop("ticket_ids")
        return redirect(url_for("events"))
    else:
        flash("Failed to purchase ticket", "error")
        return redirect(url_for("events"))
    return redirect(url_for("events"))


# VENUE SPECIFIC ROUTES #
@one_user_type_allowed("venue")
@app.route("/manage/<event_id>", methods=["GET", "POST"])
def manage_event(event_id):
    user_events = session.get("user_events", [])
    this_event = None
    for event in user_events:
        if event.get("event_id") == event_id:
            this_event = event
            break
    if this_event is None:
        flash("You are not authorized to manage this event", "error")
        return redirect(url_for("events"))
    print(this_event)
    session["event_info"] = this_event
    return render_template("manage.html", event=this_event)


@one_user_type_allowed("venue")
@app.route("/delete/<event_id>", methods=["POST"])
def delete_event(event_id):
    user_events = session.get("user_events", [])
    this_event = None
    for event in user_events:
        if event.get("event_id") == event_id:
            this_event = event
            break
    if this_event is None:
        flash("You are not authorized to delete this event", "error")
        return redirect(url_for("events"))
    req = {
        "identifier": event_id,
        "function": "delete",
        "object_type": "event",
        "attributes": {},
    }
    status_code, resp_content = make_authorized_request(
        "/delete_event", req
    )
    if status_code != 200:
        flash("Failed to delete event", "error")
        return redirect(url_for("events"))
    else:
        session["user_events"].remove(this_event)
        flash("Event deleted", "success")
        return redirect(url_for("events"))


@one_user_type_allowed("venue")
@app.route("/create_event", methods=["GET", "POST"])
def create_event():
    if request.method == "POST":
        event_date = bleach.clean(request.form.get("event_date"))
        event_time = bleach.clean(request.form.get("event_time"))
        event_artist = [bleach.clean(request.form.get("artist"))]
        date_and_time = datetime.strptime(f"{event_date} {event_time}", "%Y-%m-%d %H:%M").isoformat()
        event_name = bleach.clean(request.form.get("event_name"))
        event_price = bleach.clean(request.form.get("event_price"))
        event_capacity = bleach.clean(request.form.get("event_capacity"))
        create_request = {
            "function": "create",
            "object_type": "event",
            "attributes": {
                "event_name": event_name,
                "date_time": date_and_time,
                "total_tickets": event_capacity,
                "sold_tickets": 2,
                "venue_id": session.get("user_id", None),
                "artist_ids": event_artist,
            },
        }
        status_code, response = make_authorized_request("/create_event", create_request)
        if status_code == 200:
            event_id = response["data"]
            ticket_request = {
                "function": "create",
                "object_type": "ticket",
                "n_tickets": int(event_capacity),
                "price": event_price,
                "identifier": event_id,
            }
            status_code, response = make_authorized_request(
                "/create_tickets", ticket_request
            )
            if status_code == 200:
                flash("Event created", "success")
                return redirect(url_for("events"))
            else:
                flash("Failed to create tickets", "error")
                return redirect(url_for("create_event"))
        else:
            flash("Failed to create event", "error")
            return redirect(url_for("create_event"))
    return render_template("create_event.html")


@one_user_type_allowed("venue")
@app.route("/update/<event_id>", methods=["GET", "POST"])
def update_event(event_id):
    user_events = session.get("user_events", [])
    this_event = None
    for event in user_events:
        if event.get("event_id") == event_id:
            this_event = event
            break
    if this_event is None:
        flash("You are not authorized to update this event", "error")
        return redirect(url_for("events"))
    if request.method == "POST":
        update_attrs = request.form.to_dict()
        sanitised_attrs = {
            key: bleach.clean(value) for key, value in update_attrs.items()
        }
        status_code, resp_content = make_authorized_request(
            "/update_event",
            {"event_id": this_event["event_id"], "update_attrs": sanitised_attrs},
        )
        if status_code != 200:
            flash("Failed to update event", "error")
            return redirect(url_for("manage_event", event_id=this_event["event_id"]))
        flash("Event updated", "success")
        return redirect(url_for("manage_event", event_id=this_event["event_id"]))
    else:
        date_format = "%a, %d %b %Y %H:%M:%S %Z"
        date_obj = datetime.strptime(this_event["date"], date_format)
        event_date = date_obj.strftime("%Y-%m-%d")
        event_time = date_obj.strftime("%H:%M")
        return render_template(
            "update_event.html", event=this_event, date=event_date, time=event_time
        )


if __name__ == "__main__":
    app.run(debug=True)
