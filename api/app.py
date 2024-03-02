from flask import Flask, request, jsonify, session, redirect, url_for, render_template
# from google.oauth2 import id_token
# from google.auth.transport import requests as google_requests
from flask_dance.contrib.google import make_google_blueprint, google
import os
import requests

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "your_default_secret_key")
app.config['SESSION_COOKIE_SECURE'] = True
app.config['PREFERRED_URL_SCHEME'] = 'https'
app.url_scheme = "https"

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


@app.route("/after_login")
def after_login():
    account_info = google.get("/oauth2/v2/userinfo")
    if account_info.ok:
        account_info_json = account_info.json()
        return f"Welcome {account_info_json['name']}!"
    return "Failed to fetch user info"


@app.route("/login")
def login():
    if not google.authorized:
        return redirect(url_for("google.login"))
    return redirect(url_for("google.login"))


@app.route("/login/google", methods=["POST"])
def google_auth():
    # Extract the ID token from the request body
    id_token = request.json.get("token")

    # Verify the ID token with Google's servers
    try:
        response = requests.get(
            f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"
        )
        response.raise_for_status()
        user_info = response.json()  # Uncomment when needed
        session["user_info"] = user_info
        session["logged_in"] = True
        # Perform your authentication logic here
        # For example, check if the user exists in your database
        # If the user is authenticated successfully:

        return jsonify({"success": True, "message": "User authenticated"}), 200
    except requests.RequestException:
        return (
            jsonify(
                {"success": False, "message": "Failed to authenticate with Google"}
            ),
            400,
        )


@app.route("/")
def home():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)