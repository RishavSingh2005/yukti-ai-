import json
import os
from pathlib import Path

from flask import Flask, jsonify, redirect, request, send_from_directory, session
from werkzeug.security import check_password_hash, generate_password_hash

from reume_parser import extract_text
from scoring import analyze_resume, calculate_score

app = Flask(__name__)
app.secret_key = os.environ.get("YUKTI_SECRET_KEY", "yukti-ai-dev-secret")
USERS_FILE = Path(__file__).with_name("users.json")


@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin")

    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
    else:
        response.headers["Access-Control-Allow-Origin"] = "*"

    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


def load_users():
    if not USERS_FILE.exists():
        return {}

    with USERS_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_users(users):
    with USERS_FILE.open("w", encoding="utf-8") as file:
        json.dump(users, file, indent=2)


def normalize_username(username):
    return username.strip().lower()


def current_user():
    return session.get("username")


def candidate_level(score):
    if score >= 80:
        return "Strong Candidate"
    if score >= 50:
        return "Average Candidate"
    return "Weak Candidate"


@app.route("/")
def home():
    if current_user() is None:
        return redirect("/login")

    return send_from_directory(".", "dashboard.html")


@app.route("/upload")
@app.route("/index.html")
def upload():
    if current_user() is None:
        return redirect("/login")

    return send_from_directory(".", "index.html")


@app.route("/dashboard")
@app.route("/dashboard.html")
def dashboard():
    if current_user() is None:
        return redirect("/login")

    return send_from_directory(".", "dashboard.html")


@app.route("/login")
@app.route("/login.html")
def login_page():
    return send_from_directory(".", "login.html")


@app.route("/signup")
@app.route("/signup.html")
def signup_page():
    return send_from_directory(".", "signup.html")


@app.route("/style.css")
def styles():
    return send_from_directory(".", "style.css")


@app.route("/script.js")
def script():
    return send_from_directory(".", "script.js")


@app.get("/auth/status")
def auth_status():
    username = current_user()
    return jsonify({"authenticated": username is not None, "username": username})


@app.post("/auth/signup")
def signup():
    data = request.get_json(silent=True) or {}
    username = normalize_username(data.get("username", ""))
    password = data.get("password", "")

    if len(username) < 3:
        return jsonify({"error": "Username must be at least 3 characters."}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters."}), 400

    users = load_users()

    if username in users:
        return jsonify({"error": "This username already exists."}), 400

    users[username] = {"password": generate_password_hash(password)}
    save_users(users)
    session["username"] = username

    return jsonify({"message": "Signup successful.", "username": username})


@app.post("/auth/login")
def login():
    data = request.get_json(silent=True) or {}
    username = normalize_username(data.get("username", ""))
    password = data.get("password", "")
    users = load_users()
    user = users.get(username)

    if user is None or not check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid username or password."}), 401

    session["username"] = username

    return jsonify({"message": "Login successful.", "username": username})


@app.post("/logout")
def logout():
    session.pop("username", None)
    return jsonify({"message": "Logged out."})


@app.post("/score")
def score_resume():
    uploaded_file = request.files.get("resume")

    if uploaded_file is None or uploaded_file.filename == "":
        return jsonify({"error": "Please upload a PDF resume."}), 400

    try:
        text = extract_text(uploaded_file.stream)
        analysis = analyze_resume(text)
        score = analysis["score"]
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    return jsonify(
        {
            "score": score,
            "candidateLevel": candidate_level(score),
            "skillsMatch": f"{score}%",
            "analysis": analysis,
        }
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
