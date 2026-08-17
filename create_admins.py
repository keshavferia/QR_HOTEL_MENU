import sqlite3

conn = sqlite3.connect("database/hotel.db")

admins = [
    (1, "grandadmin", "grand123"),
    (2, "adminA", "hotelA123"),
    (3, "adminB", "hotelB123"),
    (4, "adminC", "hotelC123")
]

for hotel_id, username, password in admins:

    exists = conn.execute(
        "SELECT id FROM users WHERE username = ?",
        (username,)
    ).fetchone()

    if not exists:

        conn.execute("""
            INSERT INTO users
            (hotel_id, username, password, role)
            VALUES (?, ?, ?, 'hotel_admin')
        """, (
            hotel_id,
            username,
            password
        ))

conn.commit()

print("Admins created successfully!")

rows = conn.execute("""
    SELECT
        users.username,
        hotels.name
    FROM users
    JOIN hotels
        ON users.hotel_id = hotels.id
""").fetchall()

for row in rows:
    print(row[1], "->", row[0])

conn.close()