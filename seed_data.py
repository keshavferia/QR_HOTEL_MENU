import sqlite3
from database import DATABASE_FILE


def seed_database():
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    # -------------------------
    # HOTEL
    # -------------------------
    cursor.execute("""
        INSERT INTO hotels
        (name, address, phone, email)
        VALUES (?, ?, ?, ?)
    """, (
        "Grand Hotel",
        "Main Market",
        "9876543210",
        "grandhotel@example.com"
    ))

    hotel_id = cursor.lastrowid

    # -------------------------
    # ADMIN
    # -------------------------
    cursor.execute("""
        INSERT INTO users
        (hotel_id, username, password, role)
        VALUES (?, ?, ?, ?)
    """, (
        hotel_id,
        "admin",
        "admin123",
        "hotel_admin"
    ))

    # -------------------------
    # CATEGORIES
    # -------------------------
    categories = [
        "Indian Food",
        "Chinese Food",
        "Burgers",
        "Drinks"
    ]

    category_ids = {}

    for category in categories:
        cursor.execute("""
            INSERT INTO categories
            (hotel_id, name)
            VALUES (?, ?)
        """, (hotel_id, category))

        category_ids[category] = cursor.lastrowid

    # -------------------------
    # BIRYANI
    # -------------------------
    cursor.execute("""
        INSERT INTO menu_items
        (hotel_id, category_id, name, description, image, available)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        hotel_id,
        category_ids["Indian Food"],
        "Biryani",
        "Delicious aromatic chicken biryani",
        "biryani.png",
        1
    ))

    biryani_id = cursor.lastrowid

    biryani_sizes = [
        ("Small", 120),
        ("Medium", 180),
        ("Large", 250)
    ]

    for size, price in biryani_sizes:
        cursor.execute("""
            INSERT INTO item_sizes
            (menu_item_id, size_name, price)
            VALUES (?, ?, ?)
        """, (biryani_id, size, price))

    # -------------------------
    # BUTTER CHICKEN
    # -------------------------
    cursor.execute("""
        INSERT INTO menu_items
        (hotel_id, category_id, name, description, image, available)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        hotel_id,
        category_ids["Indian Food"],
        "Butter Chicken",
        "Creamy and delicious butter chicken",
        "butter_chicken.png",
        1
    ))

    butter_chicken_id = cursor.lastrowid

    butter_chicken_sizes = [
        ("Small", 180),
        ("Medium", 280),
        ("Large", 380)
    ]

    for size, price in butter_chicken_sizes:
        cursor.execute("""
            INSERT INTO item_sizes
            (menu_item_id, size_name, price)
            VALUES (?, ?, ?)
        """, (butter_chicken_id, size, price))

    # -------------------------
    # BURGER
    # -------------------------
    cursor.execute("""
        INSERT INTO menu_items
        (hotel_id, category_id, name, description, image, available)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        hotel_id,
        category_ids["Burgers"],
        "Chicken Burger",
        "Crispy chicken burger",
        "burger.png",
        1
    ))

    burger_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO item_sizes
        (menu_item_id, size_name, price)
        VALUES (?, ?, ?)
    """, (burger_id, "Regular", 120))

    connection.commit()
    connection.close()

    print("Test hotel and menu data added successfully!")
    print("Hotel: Grand Hotel")
    print("Admin username: admin")
    print("Admin password: admin123")


if __name__ == "__main__":
    seed_database()