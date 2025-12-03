import cv2
from deepface import DeepFace


def detect_face_info(img_path: str):
    """
    Повертає детальну інформацію про обличчя:
    вік, стать, емоції, расовий тип, домінантну емоцію.
    Використовує DeepFace.analyze без параметра prog_bar,
    щоб працювати з різними версіями бібліотеки.
    """
    try:
        # ✅ Варіант 1 — стандартний виклик без prog_bar
        result = DeepFace.analyze(
            img_path=img_path,
            actions=["emotion", "age", "gender", "race"],
            enforce_detection=True
        )

    except TypeError:
        # ✅ На випадок, якщо сигнатура ще інша — робимо мінімальний виклик
        try:
            result = DeepFace.analyze(
                img_path=img_path,
                actions=["emotion", "age", "gender", "race"]
            )
        except Exception as e:
            print(f"[face_detector] DeepFace analyze failed (fallback): {e}")
            return None
    except Exception as e:
        print(f"[face_detector] Error while analyzing face: {e}")
        return None

    # DeepFace іноді повертає список результатів
    if isinstance(result, list):
        result = result[0]

    try:
        age = int(result.get("age", 0))
    except Exception:
        age = 0

    gender = str(result.get("gender", ""))

    emotion = result.get("emotion", {}) or {}
    dominant_emotion = str(result.get("dominant_emotion", ""))

    race = result.get("race", {}) or {}
    dominant_race = str(result.get("dominant_race", ""))

    return {
        "age": age,
        "gender": gender,
        "emotion": dict(emotion),
        "dominant_emotion": dominant_emotion,
        "race": dict(race),
        "dominant_race": dominant_race,
    }