import cv2
from typing import Optional, Dict, Any

from deepface import DeepFace
from insightface.app import FaceAnalysis

# Глобальний інстанс моделі, щоб не вантажити її кожен раз
_insight_app: Optional[FaceAnalysis] = None


def _get_insight_app() -> FaceAnalysis:
    """
    Ледача ініціалізація InsightFace (buffalo_l).
    Працює на CPU через onnxruntime.
    """
    global _insight_app
    if _insight_app is None:
        app = FaceAnalysis(
            name="buffalo_l",  # якісний пайплайн: детектор + age/gender + embedding
            providers=["CPUExecutionProvider"],
        )
        # det_size можна зменшити, якщо будуть проблеми з ресурсами
        app.prepare(ctx_id=0, det_size=(640, 640))
        _insight_app = app
    return _insight_app


def _analyze_emotion(img_path: str) -> Dict[str, Any]:
    """
    Окремо рахуємо емоції через DeepFace,
    але НЕ використовуємо його стать/вік.
    """
    emo_res = DeepFace.analyze(
        img_path=img_path,
        actions=["emotion"],
        enforce_detection=True,
    )
    if isinstance(emo_res, list):
        emo_res = emo_res[0]
    emotion_raw = emo_res.get("emotion", {}) or {}
    dominant_emo = emo_res.get("dominant_emotion", "") or ""

    # нормалізуємо ключі до lower-case
    emotion_norm = {k.lower(): float(v) for k, v in emotion_raw.items()}

    return {
        "emotion": emotion_norm,
        "dominant_emotion": dominant_emo.lower(),
    }


def detect_face_info(img_path: str) -> Optional[Dict[str, Any]]:
    """
    Детальний аналіз обличчя:
    - age / gender через InsightFace (buffalo_l)
    - emotion через DeepFace
    - структура на виході сумісна з рештою бота
    """
    try:
        img = cv2.imread(img_path)
        if img is None:
            print(f"[face_detector] Cannot read image: {img_path}")
            return None

        app = _get_insight_app()
        faces = app.get(img)

        if not faces:
            print("[face_detector] No faces detected")
            return None

        # Беремо найбільше обличчя
        faces_sorted = sorted(
            faces,
            key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]),
            reverse=True,
        )
        face = faces_sorted[0]

        # ------- ВІК -------
        age_raw = getattr(face, "age", None)
        try:
            age = int(age_raw) if age_raw is not None else 0
        except Exception:
            age = 0

        # Невелика корекція віку (InsightFace іноді занижує)
        if age > 0 and age < 30:
            age += 5

        # ------- СТАТЬ -------
        # InsightFace: gender = 0 (female), 1 (male)
        gender_raw = getattr(face, "gender", None)

        if gender_raw == 1:
            gender = "man"
        elif gender_raw == 0:
            gender = "woman"
        else:
            gender = "unknown"

        # ------- ЕМОЦІЇ -------
        emo_info = _analyze_emotion(img_path)
        emotion_dict = emo_info["emotion"]
        dominant_emo = emo_info["dominant_emotion"]

        # Ми расу не використовуємо — повертаємо заглушки
        race_dict: Dict[str, float] = {}
        dominant_race = ""

        return {
            "age": age,
            "gender": gender,          # "man"/"woman"/"unknown"
            "emotion": emotion_dict,   # dict з імовірностями
            "dominant_emotion": dominant_emo,
            "race": race_dict,
            "dominant_race": dominant_race,
        }

    except Exception as e:
        print(f"[face_detector] ERROR: {e}")
        return None