from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    send_from_directory
)

import sqlite3
import os
import uuid

from werkzeug.utils import secure_filename
import qrcode


# =========================================================
# APP
# =========================================================

app = Flask(__name__)

app.secret_key = "QR_HOTEL_MENU_SECRET_2026"


# =========================================================
# PATHS
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATABASE = os.path.join(
    BASE_DIR,
    "database",
    "hotel.db"
)

UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "static",
    "images"
)

QR_FOLDER = os.path.join(
    BASE_DIR,
    "static",
    "qr"
)


# =========================================================
# PUBLIC URL
# =========================================================
#
# LOCAL TESTING:
# http://192.168.29.196:5000
#
# PUBLIC DEPLOYMENT:
# change this to your real domain
#
# Example:
# https://yourdomain.com
#
# =========================================================

PUBLIC_URL = "http://192.168.29.196:5000"


app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# =========================================================
# ALLOWED IMAGE TYPES
# =========================================================

ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "gif",
    "webp"
}


# =========================================================
# CREATE FOLDERS
# =========================================================

def create_folders():

    os.makedirs(
        os.path.dirname(DATABASE),
        exist_ok=True
    )

    os.makedirs(
        UPLOAD_FOLDER,
        exist_ok=True
    )

    os.makedirs(
        QR_FOLDER,
        exist_ok=True
    )


# =========================================================
# DATABASE
# =========================================================

def get_db():

    conn = sqlite3.connect(
        DATABASE
    )

    conn.row_factory = sqlite3.Row

    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    return conn


# =========================================================
# IMAGE CHECK
# =========================================================

def allowed_file(filename):

    if not filename:
        return False

    if "." not in filename:
        return False

    extension = filename.rsplit(
        ".",
        1
    )[1].lower()

    return extension in ALLOWED_EXTENSIONS


# =========================================================
# SAVE IMAGE
# =========================================================

def save_image(file):

    if not file:
        return ""

    if not file.filename:
        return ""

    if not allowed_file(
        file.filename
    ):
        return ""

    original_name = secure_filename(
        file.filename
    )

    extension = original_name.rsplit(
        ".",
        1
    )[1].lower()

    unique_name = (
        uuid.uuid4().hex
        + "."
        + extension
    )

    file.save(
        os.path.join(
            UPLOAD_FOLDER,
            unique_name
        )
    )

    return unique_name


# =========================================================
# DELETE IMAGE
# =========================================================

def delete_image(filename):

    if not filename:
        return

    path = os.path.join(
        UPLOAD_FOLDER,
        filename
    )

    if os.path.isfile(path):

        try:
            os.remove(path)

        except OSError:
            pass


# =========================================================
# INITIALIZE DATABASE
# =========================================================

def init_db():

    create_folders()

    conn = get_db()

    # -----------------------------------------------------
    # HOTELS
    # -----------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS hotels (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            logo TEXT,

            address TEXT,

            phone TEXT,

            email TEXT,

            created_at
                TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # -----------------------------------------------------
    # USERS
    # -----------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            hotel_id INTEGER,

            username TEXT NOT NULL UNIQUE,

            password TEXT NOT NULL,

            role TEXT
                DEFAULT 'hotel_admin',

            created_at
                TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (hotel_id)
                REFERENCES hotels(id)
                ON DELETE CASCADE
        )
    """)

    # -----------------------------------------------------
    # CATEGORIES
    # -----------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS categories (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            hotel_id INTEGER NOT NULL,

            name TEXT NOT NULL,

            created_at
                TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (hotel_id)
                REFERENCES hotels(id)
                ON DELETE CASCADE
        )
    """)

    # -----------------------------------------------------
    # MENU ITEMS
    # -----------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS menu_items (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            hotel_id INTEGER NOT NULL,

            category_id INTEGER,

            name TEXT NOT NULL,

            description TEXT,

            image TEXT,

            available INTEGER DEFAULT 1,

            created_at
                TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (hotel_id)
                REFERENCES hotels(id)
                ON DELETE CASCADE,

            FOREIGN KEY (category_id)
                REFERENCES categories(id)
                ON DELETE SET NULL
        )
    """)

    # -----------------------------------------------------
    # ITEM SIZES
    # -----------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS item_sizes (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            menu_item_id INTEGER NOT NULL,

            size_name TEXT NOT NULL,

            price REAL NOT NULL,

            FOREIGN KEY (menu_item_id)
                REFERENCES menu_items(id)
                ON DELETE CASCADE
        )
    """)

    conn.commit()

    conn.close()


# =========================================================
# LOGIN
# =========================================================

@app.route(
    "/",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        if not username or not password:

            return render_template(
                "login.html",
                error="Username and password required."
            )

        conn = get_db()

        user = conn.execute("""
            SELECT *
            FROM users
            WHERE username = ?
              AND password = ?
        """, (
            username,
            password
        )).fetchone()

        conn.close()

        if not user:

            return render_template(
                "login.html",
                error="Invalid username or password."
            )

        session.clear()

        session["user_id"] = user["id"]

        session["username"] = user["username"]

        session["role"] = user["role"]

        if user["hotel_id"]:

            session["hotel_id"] = user["hotel_id"]

        # -------------------------------------------------
        # SUPER ADMIN
        # -------------------------------------------------

        if user["role"] == "super_admin":

            session["is_super_admin"] = True

            return redirect(
                url_for("super_admin")
            )

        # -------------------------------------------------
        # HOTEL ADMIN
        # -------------------------------------------------

        if user["role"] == "hotel_admin":

            session["is_super_admin"] = False

            return redirect(
                url_for("dashboard")
            )

        session.clear()

        return redirect(
            url_for("login")
        )

    return render_template(
        "login.html"
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# =========================================================
# SUPER ADMIN DASHBOARD
# =========================================================

@app.route("/super-admin")
def super_admin():

    if session.get("role") != "super_admin":

        return redirect(
            url_for("login")
        )

    conn = get_db()

    hotels = conn.execute("""
        SELECT

            hotels.*,

            users.id AS admin_id,

            users.username AS admin_username

        FROM hotels

        LEFT JOIN users
            ON users.hotel_id = hotels.id

           AND users.role = 'hotel_admin'

        ORDER BY hotels.id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "super_admin.html",
        hotels=hotels
    )


# =========================================================
# ADD HOTEL
# =========================================================

@app.route(
    "/add-hotel",
    methods=["GET", "POST"]
)
def add_hotel():

    if session.get("role") != "super_admin":

        return redirect(
            url_for("login")
        )

    if request.method == "POST":

        hotel_name = request.form.get(
            "hotel_name",
            ""
        ).strip()

        address = request.form.get(
            "address",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        logo_file = request.files.get(
            "logo"
        )

        if not hotel_name:

            return render_template(
                "add_hotel.html",
                error="Hotel name is required."
            )

        if not username:

            return render_template(
                "add_hotel.html",
                error="Admin username is required."
            )

        if not password:

            return render_template(
                "add_hotel.html",
                error="Admin password is required."
            )

        logo_name = save_image(
            logo_file
        )

        conn = get_db()

        try:

            cursor = conn.execute("""
                INSERT INTO hotels
                (
                    name,
                    logo,
                    address,
                    phone,
                    email
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                hotel_name,
                logo_name,
                address,
                phone,
                email
            ))

            hotel_id = cursor.lastrowid

            conn.execute("""
                INSERT INTO users
                (
                    hotel_id,
                    username,
                    password,
                    role
                )
                VALUES (?, ?, ?, 'hotel_admin')
            """, (
                hotel_id,
                username,
                password
            ))

            conn.commit()

        except sqlite3.IntegrityError:

            conn.rollback()

            conn.close()

            if logo_name:
                delete_image(
                    logo_name
                )

            return render_template(
                "add_hotel.html",
                error="Username already exists."
            )

        conn.close()

        return redirect(
            url_for("super_admin")
        )

    return render_template(
        "add_hotel.html"
    )


# =========================================================
# EDIT HOTEL
# =========================================================

@app.route(
    "/edit-hotel/<int:hotel_id>",
    methods=["GET", "POST"]
)
def edit_hotel(hotel_id):

    if session.get("role") != "super_admin":

        return redirect(
            url_for("login")
        )

    conn = get_db()

    hotel = conn.execute("""
        SELECT *
        FROM hotels
        WHERE id = ?
    """, (
        hotel_id,
    )).fetchone()

    if not hotel:

        conn.close()

        return "Hotel not found", 404

    if request.method == "POST":

        hotel_name = request.form.get(
            "hotel_name",
            ""
        ).strip()

        address = request.form.get(
            "address",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        if not hotel_name:

            conn.close()

            return render_template(
                "edit_hotel.html",
                hotel=hotel,
                error="Hotel name is required."
            )

        logo_name = hotel["logo"]

        logo_file = request.files.get(
            "logo"
        )

        if (
            logo_file
            and logo_file.filename
        ):

            new_logo = save_image(
                logo_file
            )

            if new_logo:

                old_logo = hotel["logo"]

                logo_name = new_logo

                if old_logo:
                    delete_image(
                        old_logo
                    )

        conn.execute("""
            UPDATE hotels

            SET

                name = ?,

                logo = ?,

                address = ?,

                phone = ?,

                email = ?

            WHERE id = ?
        """, (
            hotel_name,
            logo_name,
            address,
            phone,
            email,
            hotel_id
        ))

        conn.commit()

        conn.close()

        return redirect(
            url_for("super_admin")
        )

    conn.close()

    return render_template(
        "edit_hotel.html",
        hotel=hotel
    )


# =========================================================
# CHANGE HOTEL ADMIN PASSWORD
# =========================================================

@app.route(
    "/change-password/<int:user_id>",
    methods=["GET", "POST"]
)
def change_password(user_id):

    if session.get("role") != "super_admin":

        return redirect(
            url_for("login")
        )

    conn = get_db()

    user = conn.execute("""
        SELECT

            users.*,

            hotels.name AS hotel_name

        FROM users

        LEFT JOIN hotels
            ON users.hotel_id = hotels.id

        WHERE users.id = ?
    """, (
        user_id,
    )).fetchone()

    if not user:

        conn.close()

        return "User not found", 404

    if user["role"] != "hotel_admin":

        conn.close()

        return "Not allowed", 403

    if request.method == "POST":

        new_password = request.form.get(
            "new_password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        if not new_password:

            conn.close()

            return render_template(
                "change_password.html",
                user=user,
                error="Password cannot be empty."
            )

        if new_password != confirm_password:

            conn.close()

            return render_template(
                "change_password.html",
                user=user,
                error="Passwords do not match."
            )

        conn.execute("""
            UPDATE users

            SET password = ?

            WHERE id = ?
        """, (
            new_password,
            user_id
        ))

        conn.commit()

        conn.close()

        return redirect(
            url_for("super_admin")
        )

    conn.close()

    return render_template(
        "change_password.html",
        user=user
    )


# =========================================================
# HOTEL ADMIN DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if session.get("role") != "hotel_admin":

        return redirect(
            url_for("login")
        )

    hotel_id = session.get(
        "hotel_id"
    )

    if not hotel_id:

        session.clear()

        return redirect(
            url_for("login")
        )

    conn = get_db()

    hotel = conn.execute("""
        SELECT *
        FROM hotels
        WHERE id = ?
    """, (
        hotel_id,
    )).fetchone()

    if not hotel:

        conn.close()

        session.clear()

        return redirect(
            url_for("login")
        )

    foods = conn.execute("""
        SELECT

            menu_items.*,

            categories.name AS category_name

        FROM menu_items

        LEFT JOIN categories
            ON menu_items.category_id =
               categories.id

           AND categories.hotel_id =
               menu_items.hotel_id

        WHERE menu_items.hotel_id = ?

        ORDER BY menu_items.id DESC
    """, (
        hotel_id,
    )).fetchall()

    food_sizes = conn.execute("""
        SELECT

            item_sizes.*

        FROM item_sizes

        JOIN menu_items
            ON item_sizes.menu_item_id =
               menu_items.id

        WHERE menu_items.hotel_id = ?

        ORDER BY item_sizes.id
    """, (
        hotel_id,
    )).fetchall()

    conn.close()

    qr_filename = (
        "hotel_"
        + str(hotel_id)
        + "_menu_qr.png"
    )

    qr_exists = os.path.isfile(
        os.path.join(
            QR_FOLDER,
            qr_filename
        )
    )

    return render_template(
        "dashboard.html",
        hotel=hotel,
        foods=foods,
        food_sizes=food_sizes,
        qr_exists=qr_exists,
        qr_filename=qr_filename
    )


# =========================================================
# ADD MENU ITEM
# =========================================================

@app.route(
    "/add-item",
    methods=["GET", "POST"]
)
def add_item():

    if session.get("role") != "hotel_admin":

        return redirect(
            url_for("login")
        )

    hotel_id = session.get(
        "hotel_id"
    )

    if not hotel_id:

        return redirect(
            url_for("login")
        )

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        category = request.form.get(
            "category",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        if not name:

            return render_template(
                "add_item.html",
                error="Item name is required."
            )

        # -------------------------------------------------
        # IMAGE
        # -------------------------------------------------

        image_file = request.files.get(
            "image"
        )

        image_name = save_image(
            image_file
        )

        conn = get_db()

        # -------------------------------------------------
        # CATEGORY
        # -------------------------------------------------

        category_id = None

        if category:

            category_row = conn.execute("""
                SELECT id

                FROM categories

                WHERE hotel_id = ?

                  AND LOWER(TRIM(name))
                      = LOWER(TRIM(?))
            """, (
                hotel_id,
                category
            )).fetchone()

            if category_row:

                category_id = category_row["id"]

            else:

                cursor = conn.execute("""
                    INSERT INTO categories
                    (
                        hotel_id,
                        name
                    )
                    VALUES (?, ?)
                """, (
                    hotel_id,
                    category
                ))

                category_id = cursor.lastrowid

        # -------------------------------------------------
        # MENU ITEM
        # -------------------------------------------------

        cursor = conn.execute("""
            INSERT INTO menu_items
            (
                hotel_id,
                category_id,
                name,
                description,
                image,
                available
            )
            VALUES (?, ?, ?, ?, ?, 1)
        """, (
            hotel_id,
            category_id,
            name,
            description,
            image_name
        ))

        item_id = cursor.lastrowid

        # -------------------------------------------------
        # PRICES
        # -------------------------------------------------

        sizes = [
            (
                "Regular",
                request.form.get(
                    "regular_price",
                    ""
                )
            ),
            (
                "Small",
                request.form.get(
                    "small_price",
                    ""
                )
            ),
            (
                "Medium",
                request.form.get(
                    "medium_price",
                    ""
                )
            ),
            (
                "Large",
                request.form.get(
                    "large_price",
                    ""
                )
            )
        ]

        for size_name, price in sizes:

            price = (
                price or ""
            ).strip()

            if not price:
                continue

            try:

                price_value = float(
                    price
                )

            except ValueError:

                continue

            if price_value < 0:
                continue

            conn.execute("""
                INSERT INTO item_sizes
                (
                    menu_item_id,
                    size_name,
                    price
                )
                VALUES (?, ?, ?)
            """, (
                item_id,
                size_name,
                price_value
            ))

        conn.commit()

        conn.close()

        return redirect(
            url_for("dashboard")
        )

    return render_template(
        "add_item.html"
    )


# =========================================================
# EDIT MENU ITEM
# =========================================================

@app.route(
    "/edit-item/<int:item_id>",
    methods=["GET", "POST"]
)
def edit_item(item_id):

    if session.get("role") != "hotel_admin":

        return redirect(
            url_for("login")
        )

    hotel_id = session.get(
        "hotel_id"
    )

    conn = get_db()

    food = conn.execute("""
        SELECT

            menu_items.*,

            categories.name AS category_name

        FROM menu_items

        LEFT JOIN categories
            ON menu_items.category_id =
               categories.id

           AND categories.hotel_id =
               menu_items.hotel_id

        WHERE menu_items.id = ?

          AND menu_items.hotel_id = ?
    """, (
        item_id,
        hotel_id
    )).fetchone()

    if not food:

        conn.close()

        return "Menu item not found", 404

    sizes = conn.execute("""
        SELECT *

        FROM item_sizes

        WHERE menu_item_id = ?
    """, (
        item_id,
    )).fetchall()

    size_prices = {}

    for size in sizes:

        size_prices[
            size["size_name"]
        ] = size["price"]

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        category = request.form.get(
            "category",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        if not name:

            conn.close()

            return render_template(
                "edit_item.html",
                food=food,
                size_prices=size_prices,
                error="Item name is required."
            )

        # -------------------------------------------------
        # IMAGE
        # -------------------------------------------------

        image_name = food["image"]

        image_file = request.files.get(
            "image"
        )

        if (
            image_file
            and image_file.filename
        ):

            new_image = save_image(
                image_file
            )

            if new_image:

                old_image = food["image"]

                image_name = new_image

                if old_image:

                    delete_image(
                        old_image
                    )

        # -------------------------------------------------
        # CATEGORY
        # -------------------------------------------------

        category_id = None

        if category:

            category_row = conn.execute("""
                SELECT id

                FROM categories

                WHERE hotel_id = ?

                  AND LOWER(TRIM(name))
                      = LOWER(TRIM(?))
            """, (
                hotel_id,
                category
            )).fetchone()

            if category_row:

                category_id = category_row["id"]

            else:

                cursor = conn.execute("""
                    INSERT INTO categories
                    (
                        hotel_id,
                        name
                    )
                    VALUES (?, ?)
                """, (
                    hotel_id,
                    category
                ))

                category_id = cursor.lastrowid

        # -------------------------------------------------
        # UPDATE ITEM
        # -------------------------------------------------

        conn.execute("""
            UPDATE menu_items

            SET

                name = ?,

                category_id = ?,

                description = ?,

                image = ?

            WHERE id = ?

              AND hotel_id = ?
        """, (
            name,
            category_id,
            description,
            image_name,
            item_id,
            hotel_id
        ))

        # -------------------------------------------------
        # DELETE OLD PRICES
        # -------------------------------------------------

        conn.execute("""
            DELETE FROM item_sizes

            WHERE menu_item_id = ?
        """, (
            item_id,
        ))

        # -------------------------------------------------
        # ADD NEW PRICES
        # -------------------------------------------------

        sizes = [
            (
                "Regular",
                request.form.get(
                    "regular_price",
                    ""
                )
            ),
            (
                "Small",
                request.form.get(
                    "small_price",
                    ""
                )
            ),
            (
                "Medium",
                request.form.get(
                    "medium_price",
                    ""
                )
            ),
            (
                "Large",
                request.form.get(
                    "large_price",
                    ""
                )
            )
        ]

        for size_name, price in sizes:

            price = (
                price or ""
            ).strip()

            if not price:
                continue

            try:

                price_value = float(
                    price
                )

            except ValueError:

                continue

            if price_value < 0:
                continue

            conn.execute("""
                INSERT INTO item_sizes
                (
                    menu_item_id,
                    size_name,
                    price
                )
                VALUES (?, ?, ?)
            """, (
                item_id,
                size_name,
                price_value
            ))

        conn.commit()

        conn.close()

        return redirect(
            url_for("dashboard")
        )

    conn.close()

    return render_template(
        "edit_item.html",
        food=food,
        size_prices=size_prices
    )


# =========================================================
# DELETE MENU ITEM
# =========================================================

@app.route(
    "/delete-item/<int:item_id>",
    methods=["POST"]
)
def delete_item(item_id):

    if session.get("role") != "hotel_admin":

        return redirect(
            url_for("login")
        )

    hotel_id = session.get(
        "hotel_id"
    )

    conn = get_db()

    food = conn.execute("""
        SELECT image

        FROM menu_items

        WHERE id = ?

          AND hotel_id = ?
    """, (
        item_id,
        hotel_id
    )).fetchone()

    if food:

        conn.execute("""
            DELETE FROM menu_items

            WHERE id = ?

              AND hotel_id = ?
        """, (
            item_id,
            hotel_id
        ))

        conn.commit()

        if food["image"]:

            delete_image(
                food["image"]
            )

    conn.close()

    return redirect(
        url_for("dashboard")
    )


# =========================================================
# TOGGLE ITEM AVAILABILITY
# =========================================================

@app.route(
    "/toggle-item/<int:item_id>",
    methods=["POST"]
)
def toggle_item(item_id):

    if session.get("role") != "hotel_admin":

        return redirect(
            url_for("login")
        )

    hotel_id = session.get(
        "hotel_id"
    )

    conn = get_db()

    food = conn.execute("""
        SELECT available

        FROM menu_items

        WHERE id = ?

          AND hotel_id = ?
    """, (
        item_id,
        hotel_id
    )).fetchone()

    if food:

        new_status = (
            0
            if food["available"]
            else 1
        )

        conn.execute("""
            UPDATE menu_items

            SET available = ?

            WHERE id = ?

              AND hotel_id = ?
        """, (
            new_status,
            item_id,
            hotel_id
        ))

        conn.commit()

    conn.close()

    return redirect(
        url_for("dashboard")
    )


# =========================================================
# PUBLIC CUSTOMER MENU
# =========================================================

@app.route(
    "/menu/<int:hotel_id>"
)
def hotel_menu(hotel_id):

    conn = get_db()

    hotel = conn.execute("""
        SELECT *

        FROM hotels

        WHERE id = ?
    """, (
        hotel_id,
    )).fetchone()

    if not hotel:

        conn.close()

        return "Hotel not found", 404

    foods = conn.execute("""
        SELECT

            menu_items.id,

            menu_items.hotel_id,

            menu_items.category_id,

            menu_items.name,

            menu_items.description,

            menu_items.image,

            menu_items.available,

            categories.name AS category_name

        FROM menu_items

        LEFT JOIN categories

            ON menu_items.category_id =
               categories.id

           AND categories.hotel_id =
               menu_items.hotel_id

        WHERE menu_items.hotel_id = ?

          AND menu_items.available = 1

        ORDER BY

            CASE

                WHEN categories.name IS NULL
                     OR TRIM(categories.name) = ''

                THEN 1

                ELSE 0

            END,

            categories.name COLLATE NOCASE,

            menu_items.name COLLATE NOCASE
    """, (
        hotel_id,
    )).fetchall()

    food_sizes = conn.execute("""
        SELECT

            item_sizes.id,

            item_sizes.menu_item_id,

            item_sizes.size_name,

            item_sizes.price

        FROM item_sizes

        INNER JOIN menu_items

            ON item_sizes.menu_item_id =
               menu_items.id

        WHERE menu_items.hotel_id = ?

        ORDER BY item_sizes.id
    """, (
        hotel_id,
    )).fetchall()

    conn.close()

    return render_template(
        "menu.html",
        hotel=hotel,
        foods=foods,
        food_sizes=food_sizes
    )


# =========================================================
# GENERATE QR
# =========================================================

@app.route(
    "/generate-qr"
)
def generate_qr():

    if session.get("role") != "hotel_admin":

        return redirect(
            url_for("login")
        )

    hotel_id = session.get(
        "hotel_id"
    )

    if not hotel_id:

        return redirect(
            url_for("login")
        )

    # -----------------------------------------------------
    # PUBLIC MENU URL
    # -----------------------------------------------------

    menu_url = (
        PUBLIC_URL.rstrip("/")
        + "/menu/"
        + str(hotel_id)
    )

    # -----------------------------------------------------
    # QR
    # -----------------------------------------------------

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4
    )

    qr.add_data(
        menu_url
    )

    qr.make(
        fit=True
    )

    qr_image = qr.make_image()

    qr_filename = (
        "hotel_"
        + str(hotel_id)
        + "_menu_qr.png"
    )

    qr_path = os.path.join(
        QR_FOLDER,
        qr_filename
    )

    qr_image.save(
        qr_path
    )

    return render_template(
        "qr.html",
        qr_filename=qr_filename,
        menu_url=menu_url
    )


# =========================================================
# QR IMAGE
# =========================================================

@app.route(
    "/qr/<filename>"
)
def qr_image(filename):

    return send_from_directory(
        QR_FOLDER,
        filename
    )


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route(
    "/health"
)
def health():

    return "OK"


# =========================================================
# CREATE DATABASE
# =========================================================

create_folders()

init_db()


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )