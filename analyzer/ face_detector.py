from deepface import DeepFace

def detect_face_info(img_path: str):
    """
    Повертає детальну інформацію про лице:
    вік, стать, емоції, расовий тип (як контекст),
    домінантну емоцію.
    """
    try:
        result = DeepFace.analyze(
            img_path=img_path,
            actions=["emotion", "age", "gender", "race"],
            enforce_detection=True
        )
        # DeepFace може повертати список
        if isinstance(result, list):
            result = result[0]

        return {
            "age": int(result.get("age", 0)),
            "gender": str(result.get("gender", "")),
            "emotion": dict(result.get("emotion", {})),
            "dominant_emotion": str(result.get("dominant_emotion", "")),
            "race": dict(result.get("race", {})),
            "dominant_race": str(result.get("dominant_race", "")),
        }
    except Exception:
        return None
