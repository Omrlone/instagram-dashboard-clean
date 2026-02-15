import os
from datetime import datetime
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Secret key (use environment variable on Render)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "dev-secret-key")

# SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# =========================
# Database Models
# =========================

class Visitor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(100))
    visit_time = db.Column(db.DateTime, default=datetime.utcnow)


# =========================
# Routes
# =========================

@app.route("/")
def home():
    # Save visitor info
    visitor = Visitor(
        ip_address=request.remote_addr
    )
    db.session.add(visitor)
    db.session.commit()

    total_visits = Visitor.query.count()

    return f"""
    <h1>Instagram Dashboard</h1>
    <p>Total Visits: {total_visits}</p>
    """


# =========================
# Create Tables Automatically
# =========================

def init_db():
    with app.app_context():
        db.create_all()

init_ab()

# =========================
# Run App
# =========================

if __name__ == "__main__":
    app.run(debug=True)
