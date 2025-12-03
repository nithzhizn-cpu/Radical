from typing import Dict


# Валентність емоцій від -1 до +1
VALENCE_MAP = {
    "angry": -0.9,
    "fear": -0.8,
    "sad": -0.8,
    "disgust": -0.7,
    "surprise": 0.1,   # нейтрально-позитивна/тривожна
    "neutral": 0.0,
    "happy": 0.9,
}


def interpret_emotions(emotions: Dict[str, float]):
    """
    Приймає raw-емоції з DeepFace, наприклад:
    {"angry": 5.1, "happy": 70.2, ...}

    Повертає структурований профіль:
    {
      "dominant_emotion": str,
      "valence": float (0..100),
      "intensity": float (0..100),
      "emotional_style": str,
      "raw": {...}
    }
    """
    if not emotions:
        return {
            "dominant_emotion": "unknown",
            "valence": 50.0,
            "intensity": 0.0,
            "emotional_style": "Емоційний стан не визначений.",
            "raw": {},
        }

    # Нормалізація
    total = sum(emotions.values()) or 1.0
    normalized = {k.lower(): (v / total) for k, v in emotions.items()}

    # Домінантна емоція
    dominant_emotion = max(normalized, key=normalized.get)
    dom_value = normalized[dominant_emotion]

    # Обчислення валентності (зважена сума)
    val_raw = 0.0
    for emo, frac in normalized.items():
        base = VALENCE_MAP.get(emo, 0.0)
        val_raw += base * frac

    # Переводимо валентність у шкалу 0..100
    # -1 -> 0, 0 -> 50, +1 -> 100
    valence_0_100 = (val_raw + 1.0) * 50.0
    valence_0_100 = max(0.0, min(100.0, valence_0_100))

    # Інтенсивність (наскільки домінує одна емоція)
    intensity = dom_value * 100.0

    # Текстовий стиль
    if valence_0_100 > 70:
        mood = "переважно позитивний емоційний фон"
    elif valence_0_100 < 30:
        mood = "переважно негативний або напружений емоційний фон"
    else:
        mood = "змішаний або відносно нейтральний фон"

    if intensity > 70:
        style = "Домінує одна яскраво виражена емоція; реакції можуть бути помітними для оточення."
    elif intensity < 35:
        style = "Емоційний стан більш розмитий, без різко вираженої емоції."
    else:
        style = "Є одна провідна емоція, але простежуються й інші емоційні відтінки."

    emotional_style = f"{mood}. {style}"

    return {
        "dominant_emotion": dominant_emotion,
        "valence": round(valence_0_100, 1),
        "intensity": round(intensity, 1),
        "emotional_style": emotional_style,
        "raw": emotions,
    }