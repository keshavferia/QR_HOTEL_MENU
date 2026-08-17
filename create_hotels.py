import sqlite3

conn = sqlite3.connect("database/hotel.db")

hotels = [
    ("Hotel A", "", "", "", ""),
    ("Hotel B", "", "", "", ""),
    ("Hotel C", "", "", "", "")
]

for hotel in hotels:

    exists = conn.execute(
        "SELECT id FROM hotels WHERE name = ?",
        (hotel[0],)
    ).fetchone()

    if not exists:

        conn.execute("""
            INSERT INTO hotels
            (name, logo, address, phone, email)
            VALUES (?, ?, ?, ?, ?)
        """, hotel)

conn.commit()

print("Hotels created successfully!")

rows = conn.execute(
    "SELECT id, name FROM hotels"
).fetchall()

for row in rows:
    print(row[0], "-", row[1])

conn.close()