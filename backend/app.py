from flask import Flask, request, jsonify
import psycopg2
import os
import time

app = Flask(__name__)

DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("DB_NAME", "notesdb")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")


def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )


def init_db():
    retries = 10
    while retries > 0:
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id SERIAL PRIMARY KEY,
                    content TEXT NOT NULL
                );
            """)
            conn.commit()
            cur.close()
            conn.close()
            print("Database initialized successfully.")
            return
        except Exception as e:
            print(f"Database not ready yet: {e}")
            retries -= 1
            time.sleep(2)

    raise Exception("Could not connect to database after multiple retries.")


@app.route("/notes", methods=["GET"])
def get_notes():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, content FROM notes ORDER BY id ASC;")
        rows = cur.fetchall()
        cur.close()
        conn.close()

        notes = [{"id": row[0], "content": row[1]} for row in rows]
        return jsonify(notes), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/notes", methods=["POST"])
def add_note():
    try:
        data = request.get_json()

        if not data or "content" not in data or not data["content"].strip():
            return jsonify({"error": "Note content is required"}), 400

        content = data["content"].strip()

        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO notes (content) VALUES (%s) RETURNING id;",
            (content,)
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            "message": "Note added successfully",
            "id": new_id,
            "content": content
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)