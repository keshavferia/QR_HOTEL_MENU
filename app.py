from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
from werkzeug.utils import secure_filename
import qrcode

app = Flask(__name__)

DATABASE = "database/hotel.db"
UPLOAD_FOLDER = "static/images"
QR_FOLDER = "static/qr"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# =========================
# DATABASE
# =========================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():

    os.makedirs("database", exist_ok=True)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(QR_FOLDER, exist_ok=True)

    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS food_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            image TEXT,
            available INTEGER DEFAULT 1
        )
    """)

    conn.commit()
    conn.close()


# =========================
# LOGIN
# =========================

@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "1234":
            return redirect(url_for("dashboard"))

        return render_template(
            "login.html",
            error="Invalid username or password"
        )

    return render_template("login.html")


# =========================
# DASHBOARD
# =========================

@app.route("/dashboard")
def dashboard():

    conn = get_db()

    foods = conn.execute("""
        SELECT * FROM food_items
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        foods=foods
    )


# =========================
# ADD FOOD
# =========================

@app.route("/add-item", methods=["GET", "POST"])
def add_item():

    if request.method == "POST":

        name = request.form["name"]
        category = request.form["category"]
        description = request.form["description"]
        price = request.form["price"]

        image_file = request.files.get("image")

        image_name = ""

        if image_file and image_file.filename:

            image_name = secure_filename(
                image_file.filename
            )

            image_file.save(
                os.path.join(
                    UPLOAD_FOLDER,
                    image_name
                )
            )

        conn = get_db()

        conn.execute("""
            INSERT INTO food_items
            (name, category, description, price, image)
            VALUES (?, ?, ?, ?, ?)
        """, (
            name,
            category,
            description,
            price,
            image_name
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("dashboard"))

    return render_template("add_item.html")


# =========================
# EDIT FOOD
# =========================

@app.route("/edit-item/<int:item_id>", methods=["GET", "POST"])
def edit_item(item_id):

    conn = get_db()

    food = conn.execute(
        "SELECT * FROM food_items WHERE id = ?",
        (item_id,)
    ).fetchone()

    if food is None:

        conn.close()

        return "Food item not found", 404

    if request.method == "POST":

        name = request.form["name"]
        category = request.form["category"]
        description = request.form["description"]
        price = request.form["price"]

        image_file = request.files.get("image")

        image_name = food["image"]

        if image_file and image_file.filename:

            image_name = secure_filename(
                image_file.filename
            )

            image_file.save(
                os.path.join(
                    UPLOAD_FOLDER,
                    image_name
                )
            )

        conn.execute("""
            UPDATE food_items

            SET name = ?,
                category = ?,
                description = ?,
                price = ?,
                image = ?

            WHERE id = ?
        """, (
            name,
            category,
            description,
            price,
            image_name,
            item_id
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("dashboard"))

    conn.close()

    return render_template(
        "edit_item.html",
        food=food
    )


# =========================
# DELETE FOOD
# =========================

@app.route("/delete-item/<int:item_id>", methods=["POST"])
def delete_item(item_id):

    conn = get_db()

    conn.execute(
        "DELETE FROM food_items WHERE id = ?",
        (item_id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))


# =========================
# TOGGLE AVAILABILITY
# =========================

@app.route("/toggle-item/<int:item_id>", methods=["POST"])
def toggle_item(item_id):

    conn = get_db()

    food = conn.execute(
        "SELECT available FROM food_items WHERE id = ?",
        (item_id,)
    ).fetchone()

    if food:

        new_status = 0 if food["available"] else 1

        conn.execute("""
            UPDATE food_items
            SET available = ?
            WHERE id = ?
        """, (
            new_status,
            item_id
        ))

        conn.commit()

    conn.close()

    return redirect(url_for("dashboard"))


# =========================
# CUSTOMER MENU
# =========================

@app.route("/menu")
def menu():

    conn = get_db()

    foods = conn.execute("""
        SELECT * FROM food_items
        WHERE available = 1
        ORDER BY category, name
    """).fetchall()

    conn.close()

    return render_template(
        "menu.html",
        foods=foods
    )


# =========================
# GENERATE QR CODE
# =========================

@app.route("/generate-qr")
def generate_qr():

    menu_url = "http://192.168.29.196:5000/menu"

    qr = qrcode.make(menu_url)

    qr_path = os.path.join(
        QR_FOLDER,
        "hotel_menu_qr.png"
    )

    qr.save(qr_path)

    return redirect(url_for("dashboard"))


# =========================
# RUN APPLICATION
# =========================

if __name__ == "__main__":

    init_db()

    app.run(host="0.0.0.0", port=5000, debug=True)