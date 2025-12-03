# database.py
import os
import json
import sqlite3
from typing import Any, List, Tuple

DB_PATH = os.path.join(os.path.dirname(__file__), "reports.db")


def _make_jsonable(obj: Any):
    """
    Рекурсивно перетворює numpy-типи, масиви тощо
    у звичайні Python-типи, які json.dumps розуміє.
    """
    # Лінивий імпорт, щоб не падати, якщо раптом немає numpy
    try:
        import numpy as np
    except ImportError:
        np = None

    if np is not None:
        # np.float32, np.int64 і т.п.
        if isinstance(obj, np.generic):
            return obj.item()
        # np.ndarray
        if isinstance(obj, np.ndarray):
            return obj.tolist()

    if isinstance(obj, dict):
        return {k: _make_jsonable(v) for k, v in obj.items()}

    if isinstance(obj, (list, tuple)):
        return [_make_jsonable(v) for v in obj]

    return obj


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            image_path TEXT,
            face_data TEXT,
            emotion_data TEXT,
            stress_data TEXT,
            personality_data TEXT,
            professional_data TEXT,
            full_report TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()


def save_report(
    user_id: int,
    image_path: str,
    face_data: dict,
    emotion_data: dict,
    stress_data: dict,
    personality_data: dict,
    professional_data: dict,
    full_report: str,
):
    """
    Зберігає все в SQLite.
    ВАЖЛИВО: перед json.dumps ганяємо через _make_jsonable.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    face_json = json.dumps(_make_jsonable(face_data), ensure_ascii=False)
    emotion_json = json.dumps(_make_jsonable(emotion_data), ensure_ascii=False)
    stress_json = json.dumps(_make_jsonable(stress_data), ensure_ascii=False)
    personality_json = json.dumps(_make_jsonable(personality_data), ensure_ascii=False)
    professional_json = json.dumps(_make_jsonable(professional_data), ensure_ascii=False)

    cur.execute(
        """
        INSERT INTO reports (
            user_id,
            image_path,
            face_data,
            emotion_data,
            stress_data,
            personality_data,
            professional_data,
            full_report
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            image_path,
            face_json,
            emotion_json,
            stress_json,
            personality_json,
            professional_json,
            full_report,
        ),
    )

    conn.commit()
    conn.close()


def get_user_reports(user_id: int) -> List[Tuple]:
    """
    Повертає список записів для користувача.
    ORDER BY created_at DESC — останні зверху.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            id,
            user_id,
            image_path,
            face_data,
            emotion_data,
            stress_data,
            personality_data,
            professional_data,
            full_report,
            created_at
        FROM reports
        WHERE user_id = ?
        ORDER BY created_at DESC
        """,
        (user_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows