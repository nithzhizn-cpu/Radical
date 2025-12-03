import sqlite3
import json
from datetime import datetime

DB_NAME = "psychodb.sqlite"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        img_path TEXT,
        face_data TEXT,
        emotion_data TEXT,
        stress_data TEXT,
        personality_data TEXT,
        professional_data TEXT,
        full_report TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()


def save_report(user_id, img_path, face_data, emotion_data, stress_data,
                personality_data, professional_data, full_report):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO reports (
            user_id, img_path, face_data, emotion_data, stress_data,
            personality_data, professional_data, full_report, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        img_path,
        json.dumps(face_data, ensure_ascii=False),
        json.dumps(emotion_data, ensure_ascii=False),
        json.dumps(stress_data, ensure_ascii=False),
        json.dumps(personality_data, ensure_ascii=False),
        json.dumps(professional_data, ensure_ascii=False),
        full_report,
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()


def get_user_reports(user_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("SELECT * FROM reports WHERE user_id=? ORDER BY created_at DESC", (user_id,))
    rows = cur.fetchall()

    conn.close()
    return rows


def get_report_by_id(report_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT * FROM reports WHERE id=?", (report_id,))
    row = cur.fetchone()
    conn.close()
    return row