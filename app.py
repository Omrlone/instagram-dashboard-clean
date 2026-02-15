import os
import requests
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# ========================
# CONFIGURATION
# ========================

app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///database.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ========================
# DATABASE MODELS
# ========================

class Visitor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    ip = db.Column(db.String(100))
    country = db.Column(db.String(100))
    device = db.Column(db.String(300))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password_hash = db.Column(db.String(200))

# ========================
# HELPER FUNCTIONS
# ========================

def get_country(ip):
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}").json()
        return response.get("country", "Unknown")
    except:
        return "Unknown"

def is_admin_logged_in():
    return session.get("admin_logged_in")

# ========================
# PUBLIC ROUTES
# ========================

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        captcha_answer = request.form["captcha"]

        if captcha_answer != "7":
            return "Captcha incorrect."

        ip = request.remote_addr
        country = get_country(ip)
        device = request.user_agent.string

        visitor = Visitor(
            name=name,
            email=email,
            ip=ip,
            country=country,
            device=device
        )

        db.session.add(visitor)
        db.session.commit()

        session["access_granted"] = True
        return redirect(url_for("advanced"))

    return render_template("signup.html")

@app.route("/advanced")
def advanced():
    if not session.get("access_granted"):
        return redirect(url_for("signup"))
    return render_template("advanced.html")

# ========================
# ADMIN AUTH
# ========================

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        admin = Admin.query.filter_by(username=username).first()

        if admin and check_password_hash(admin.password_hash, password):
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid credentials")

    return render_template("admin_login.html")

@app.route("/admin-dashboard")
def admin_dashboard():
    if not is_admin_logged_in():
        return redirect(url_for("admin_login"))

    visitors = Visitor.query.order_by(Visitor.timestamp.desc()).all()
    total = Visitor.query.count()

    return render_template("admin_dashboard.html",
                           visitors=visitors,
                           total=total)

@app.route("/admin-logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_login"))

# ========================
# INITIAL SETUP
# ========================

with app.app_context():
    db.create_all()

    if not Admin.query.filter_by(username="admin").first():
        secure_password = generate_password_hash("ChangeThisPassword123")
        admin = Admin(username="admin", password_hash=secure_password)
        db.session.add(admin)
        db.session.commit()

# ========================
# RUN
# ========================

if __name__ == "__main__":
    app.run(debug=True)
