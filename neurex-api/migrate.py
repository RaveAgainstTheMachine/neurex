import sqlite3


def migrate():
    conn = sqlite3.connect("./neurex.db")
    cursor = conn.cursor()

    print("Checking tasknode table...")
    try:
        cursor.execute("ALTER TABLE tasknode ADD COLUMN approval_reason VARCHAR")
        print("Successfully added approval_reason to tasknode.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("approval_reason already exists.")
        else:
            print(f"Error migrating tasknode: {e}")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    migrate()
