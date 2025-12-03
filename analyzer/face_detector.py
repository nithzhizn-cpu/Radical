# analyzer/face_detector.py

from typing import Optional, Dict, Any
from deepface import DeepFace


def detect_face_info(img_path: str) -> Optional[Dict[str, Any]]:
    """
    Аналіз обличчя на основі стеку:
    - Детектор: RetinaFace (через DeepFace)
    - Емоції: модель DeepFace (аналог FER+)
    - Вік, стать, расовий профіль — з вбудованих моделей DeepFace.

    Повертає:
        {
            "age": int,
            "gender": str,
            "emotion": dict,
            "dominant_emotion": str,
            "race": dict,
            "dominant_race": str
        }
    або None, якщо обличчя не знайдено / помилка.
    """
    try:
        result = DeepFace.analyze(
            img_path=img_path,
            actions=["emotion", "age", "gender", "race"],
            detector_backend="retinaface",  # RetinaFace як детектор
            enforce_detection=True,
            prog_bar=False,
        )

        # DeepFace іноді повертає список результатів (для кількох облич)
        if isinstance(result, list):
            result = result[0]

        age = int(result.get("age", 0)) if result.get("age") is not None else 0
        gender = str(result.get("gender", "") or "")

        emotion_raw = result.get("emotion") or {}
        if not isinstance(emotion_raw, dict):
            emotion_raw = {}

        dominant_emotion = str(result.get("dominant_emotion", "") or "")

        race_raw = result.get("race") or {}
        if not isinstance(race_raw, dict):
            race_raw = {}

        dominant_race = str(result.get("dominant_race", "") or "")

        return {
            "age": age,
            "gender": gender,
            "emotion": emotion_raw,
            "dominant_emotion": dominant_emotion,
            "race": race_raw,
            "dominant_race": dominant_race,
        }

    except Exception as e:
        # Лог у консолі Railway, але бот не падає
        print(f"[face_detector] Error while analyzing face: {e}", flush=True)
        return None