import sqlite3

conn = sqlite3.connect("database/hotel.db")

username = "superadmin"
password = "super123"

exists = conn.execute(
    "SELECT id FROM users WHERE username = ?",
    (username,)
).fetchone()

if not exists:

    conn.execute("""
        INSERT INTO users
        (hotel_id, username, password, role)
        VALUES (?, ?, ?, ?)
    """, (
        1,
        username,
        password,
        "super_admin"
    ))

    conn.commit()

    print("Super Admin created successfully!")
    print("Username:", username)
    print("Password:", password)

else:

    print("Super Admin already exists!")

conn.close()