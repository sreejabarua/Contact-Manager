import sqlite3
from flask import Flask, render_template, request, redirect, session
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "super_secret_key"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "static")
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


# ---------- DATABASE SETUP ----------
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            phone TEXT,
            email TEXT,
            address TEXT,
            birthday TEXT,
            age INTEGER,
            notes TEXT,
            profile_pic TEXT
        )
    """)

    conn.commit()
    conn.close()

init_db()

@app.route("/")
def home():
    user_id = session.get("user_id")

    if not user_id:
        return redirect("/login")

    search = request.args.get("search")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    if search:
        c.execute("""
            SELECT * FROM contacts
            WHERE user_id = ?
            AND (
                name LIKE ?
                OR phone LIKE ?
                OR email LIKE ?
            )
            ORDER BY name ASC
        """, (
            user_id,
            f"%{search}%",
            f"%{search}%",
            f"%{search}%"
        ))

    else:
        c.execute("""
            SELECT * FROM contacts
            WHERE user_id = ?
            ORDER BY name ASC
        """, (user_id,))

    rows = c.fetchall()
    conn.close()

    contacts = []

    for row in rows:
        contacts.append({
            "id": row[0],
            "user_id": row[1],
            "name": row[2],
            "phone": row[3],
            "email": row[4],
            "address": row[5],
            "birthday": row[6],
            "age": row[7],
            "notes": row[8],
            "profile_pic": row[9]
        })

    return render_template("index.html", contacts=contacts)

@app.route("/contact/<int:contact_id>")
def contactDetail(contact_id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    user_id = session.get("user_id")

    if not user_id:
        conn.close()
        return redirect("/login")

    c.execute(
        "SELECT * FROM contacts WHERE id = ? AND user_id = ?",
        (contact_id, user_id)
    )

    row = c.fetchone()

    conn.close()

    if not row:
        return "Contact not found", 404

    contact = {
        "id": row[0],
        "user_id": row[1],
        "name": row[2],
        "phone": row[3],
        "email": row[4],
        "address": row[5],
        "birthday": row[6],
        "age": row[7],
        "notes": row[8],
        "profile_pic": row[9]
    }

    return render_template("contactDetails.html", contact=contact)

# --add button ----------
@app.route("/add", methods=["POST"])
def add_contact():

    user_id = session.get("user_id")

    if not user_id:
        return redirect("/login")

    name = request.form.get("name")
    phone = request.form.get("phone")
    email = request.form.get("email")
    address = request.form.get("address")
    birthday = request.form.get("birthday")
    age = request.form.get("age")
    notes = request.form.get("notes")

    file = request.files.get("profile_pic")
    filename = None

    if file and file.filename != "":
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
        INSERT INTO contacts
        (user_id, name, phone, email, address, birthday, age, notes, profile_pic)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        name,
        phone,
        email,
        address,
        birthday,
        age,
        notes,
        filename
    ))

    conn.commit()
    conn.close()

    return redirect("/")

# --delete function ----------
@app.route("/delete/<int:contact_id>")
def delete_contact(contact_id):

    user_id = session.get("user_id")

    if not user_id:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute(
        "DELETE FROM contacts WHERE id = ? AND user_id = ?",
        (contact_id, user_id)
    )

    conn.commit()
    conn.close()

    return redirect("/")

# --edit function ----------
@app.route("/edit/<int:contact_id>")
def edit_contact(contact_id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    user_id = session.get("user_id")

    c.execute(
        "SELECT * FROM contacts WHERE id = ? AND user_id = ?",
        (contact_id, user_id)
    )
    row = c.fetchone()
    if row is None:
        return "Contact not found", 404

    conn.close()

    contact = {
        "id": row[0],
        "user_id": row[1],
        "name": row[2],
        "phone": row[3],
        "email": row[4],
        "address": row[5],
        "birthday": row[6],
        "age": row[7],
        "notes": row[8],
        "profile_pic": row[9]
    }

    return render_template("edit.html", contact=contact)

# --update function ----------
@app.route("/update/<int:contact_id>", methods=["POST"])
def update_contact(contact_id):

    user_id = session.get("user_id")

    if not user_id:
        return redirect("/login")

    name = request.form.get("name")
    phone = request.form.get("phone")
    email = request.form.get("email")
    address = request.form.get("address")
    birthday = request.form.get("birthday")
    age = request.form.get("age")
    notes = request.form.get("notes")

    file = request.files.get("profile_pic")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    if file and file.filename != "":
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        c.execute("""
            UPDATE contacts
            SET name = ?, phone = ?, email = ?, address = ?, birthday = ?, age = ?, notes = ?, profile_pic = ?
            WHERE id = ? AND user_id = ?
        """, (
            name, phone, email, address,
            birthday, age, notes, filename,
            contact_id, user_id
        ))

    else:
        c.execute("""
            UPDATE contacts
            SET name = ?, phone = ?, email = ?, address = ?, birthday = ?, age = ?, notes = ?
            WHERE id = ? AND user_id = ?
        """, (
            name, phone, email, address,
            birthday, age, notes,
            contact_id, user_id
        ))

    conn.commit()
    conn.close()

    return redirect("/")

@app.route("/register")
def register_page():
    return render_template("register.html")


@app.route("/register", methods=["POST"])
def register():

    username = request.form.get("username")
    password = request.form.get("password")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    try:
        c.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password)
        )
        conn.commit()

    except sqlite3.IntegrityError:
        conn.close()
        return "Username already exists"

    conn.close()

    return redirect("/login")

@app.route("/login")
def login_page():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():

    username = request.form.get("username")
    password = request.form.get("password")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
        (username, password)
    )

    user = c.fetchone()

    conn.close()

    if user:
        session["user_id"] = user[0]
        return redirect("/")

    return "Invalid login"

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True, port=5001)