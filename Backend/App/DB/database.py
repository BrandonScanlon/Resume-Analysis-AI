import sqlite3
def save_resume(user_id, original, optimized):
    conn = sqlite3.connect("resumes.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO resumes VALUES (?, ?, ?)", (user_id, original, optimized))
    conn.commit()