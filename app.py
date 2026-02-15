import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "supersecretkey")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["UPLOAD_FOLDER"] = "static/uploads"

db = SQLAlchemy(app)

# ================= DATABASE MODELS =================

class Visitor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    ip = db.Column(db.String(100))
    device = db.Column(db.String(300))
    time = db.Column(db.DateTime, default=datetime.utcnow)

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    bio = db.Column(db.String(500))
    profile_image = db.Column(db.String(200))
    background_image = db.Column(db.String(200))

class Gallery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(200))

# ================= INITIALIZE =================

with app.app_context():
    db.create_all()
    if not Profile.query.first():
        profile = Profile(
            name="Your Name",
            bio="Hacker Style Developer",
            profile_image="",
            background_image=""
        )
        db.session.add(profile)
        db.session.commit()

# ================= PUBLIC PAGE =================

@app.route("/", methods=["GET", "POST"])
def home():
    profile = Profile.query.first()
    gallery = Gallery.query.all()

    if request.method == "POST":
        name = request.form.get("visitor_name")
        ip = request.remote_addr
        device = request.headers.get("User-Agent")

        visitor = Visitor(name=name, ip=ip, device=device)
        db.session.add(visitor)
        db.session.commit()

        return redirect("/")

    return render_template("home.html", profile=profile, gallery=gallery)

# ================= ADMIN LOGIN =================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == os.environ.get("ADMIN_USERNAME") and password == os.environ.get("ADMIN_PASSWORD"):
            session["admin"] = True
            return redirect("/dashboard")

    return render_template("login.html")

# ================= DASHBOARD =================

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if not session.get("admin"):
        return redirect("/login")

    profile = Profile.query.first()
    visitors = Visitor.query.order_by(Visitor.time.desc()).all()
    gallery = Gallery.query.all()

    if request.method == "POST":
        profile.name = request.form.get("name")
        profile.bio = request.form.get("bio")

        # Profile image upload
        if "profile_image" in request.files:
            file = request.files["profile_image"]
            if file.filename != "":
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                profile.profile_image = filename

        # Background upload
        if "background_image" in request.files:
            file = request.files["background_image"]
            if file.filename != "":
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                profile.background_image = filename

        # Gallery upload
        if "gallery_image" in request.files:
            file = request.files["gallery_image"]
            if file.filename != "":
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                new_img = Gallery(image=filename)
                db.session.add(new_img)

        db.session.commit()

    return render_template("dashboard.html", profile=profile, visitors=visitors, gallery=gallery)

# ================= DELETE IMAGE =================

@app.route("/delete/<int:id>")
def delete_image(id):
    if not session.get("admin"):
        return redirect("/login")

    img = Gallery.query.get(id)
    if img:
        db.session.delete(img)
        db.session.commit()

    return redirect("/dashboard")

# ================= LOGOUT =================

@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/")

# ================= RUN =================

if __name__ == "__main__":
    app.run(debug=True)
