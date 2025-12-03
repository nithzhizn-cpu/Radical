import math

POSITIVE_EMOS = {"happy", "surprise"}
NEGATIVE_EMOS = {"sad", "fear", "angry", "disgust"}
NEUTRAL_EMOS = {"neutral"}


def interpret_emotions(emotions: dict):
    """
    Аналізує розподіл емоцій:
    - домінантна емоція
    - валентність (позитив/негатив/нейтраль)
    - інтенсивність, стабільність, тенденції
    """
    if not emotions:
        return {
            "dominant_emotion": "unknown",
            "valence": "невизначена",
            "emotional_intensity": "невідомо",
            "emotional_stability": "невідомо",
            "tendencies": [],
        }

    # нормалізація в 0–1
    total = sum(emotions.values())
    norm = {k: (v / total * 100.0) for k, v in emotions.items()} if total > 0 else emotions

    dominant = max(norm, key=norm.get)
    dom_val = norm[dominant]

    # валентність
    if dominant in POSITIVE_EMOS:
        valence = "переважно позитивна"
    elif dominant in NEGATIVE_EMOS:
        valence = "переважно негативна"
    elif dominant in NEUTRAL_EMOS:
        valence = "стримана / нейтральна"
    else:
        valence = "змішана"

    # інтенсивність
    if dom_val > 70:
        emotional_intensity = "висока"
    elif dom_val > 40:
        emotional_intensity = "помірна"
    else:
        emotional_intensity = "низька"

    # простий показник стабільності — чим більш рівномірний розподіл, тим менш стабільний стан
    probs = [v / total for v in emotions.values()] if total > 0 else []
    entropy = -sum(p * math.log(p + 1e-9) for p in probs) if probs else 0.0
    # грубе правило: низька ентропія = стабільний профіль
    if entropy < 1.2:
        stability = "відносно стабільний"
    elif entropy < 1.8:
        stability = "змінний"
    else:
        stability = "дуже варіативний"

    tendencies = []

    if valence == "переважно позитивна":
        tendencies.append("Схильність бачити ситуації у більш позитивному світлі.")
    if valence == "переважно негативна":
        tendencies.append("Є тенденція фокусуватися на ризиках, проблемах та загрозах.")
    if "neutral" in norm and norm["neutral"] > 40:
        tendencies.append("Схильність до емоційного контролю та стриманості.")
    if emotional_intensity == "висока":
        tendencies.append("Емоційні реакції можуть бути яскравими та помітними для оточення.")

    return {
        "dominant_emotion": dominant,
        "valence": valence,
        "emotional_intensity": emotional_intensity,
        "emotional_stability": stability,
        "tendencies": tendencies,
        "normalized_emotions": norm,
    }
