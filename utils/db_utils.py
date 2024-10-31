import sqlite3

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def fetch_new_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM content WHERE analyzed = 0")
    data = cursor.fetchall()
    conn.close()
    return data

def mark_as_analyzed(content_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE content SET analyzed = 1 WHERE id = ?", (content_id,))
    conn.commit()
    conn.close()

def save_analysis_result(text, image_path, contains_profanity, is_nsfw):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO analysis_results (text, image_path, contains_profanity, is_nsfw)
        VALUES (?, ?, ?, ?)
    """, (text, image_path, contains_profanity, is_nsfw))
    conn.commit()
    analysis_id = cursor.lastrowid
    conn.close()
    return analysis_id