import os
import requests
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "dev-secret")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ======================
# Database Model
# ======================

class Visitor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    ip = db.Column(db.String(100))
    country = db.Column(db.String(100))
    device = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# ======================
# Helper: Get Country from IP
# ======================

def get_country(ip):
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}").json()
        return response.get("country", "Unknown")
    except:
        return "Unknown"

# ======================
# Routes
# ======================

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
            return "Captcha incorrect. Go back and try again."

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

@app.route("/admin")
def admin():
    visitors = Visitor.query.order_by(Visitor.timestamp.desc()).all()
    total = Visitor.query.count()
    return render_template("admin.html", visitors=visitors, total=total)

# ======================
# Initialize Database
# ======================

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
