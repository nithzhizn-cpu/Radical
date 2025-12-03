from typing import Dict
from analyzer.radicals import RADICAL_DESCRIPTIONS

NEGATIVE_EMOS = {"sad", "fear", "angry", "disgust"}
POSITIVE_EMOS = {"happy", "surprise"}


def estimate_radical(dominant_emotion: str, stress_level: str) -> str:
    """
    Дуже спрощене наближення радикалів Пономаренка по емоції та стресу.
    Це лише евристика, не клінічна діагностика.
    """
    dom = dominant_emotion.lower()

    if dom == "angry":
        return "Збудливий радикал"
    if dom == "happy":
        return "Гіпертимний радикал"
    if dom == "sad":
        return "Емотивний радикал"
    if dom == "fear":
        return "Тривожний радикал"
    if dom == "neutral":
        if stress_level == "високий":
            return "Застрягаючий радикал"
        else:
            return "Педантичний радикал"
    return "Змішаний або неявний радикал"


def estimate_big_five(
    face_info: Dict,
    emotion_profile: Dict,
    stress_info: Dict
):
    """
    Оцінка Big Five (OCEAN) в балах 0–100.
    Дуже спрощена, на основі емоцій, стресу, віку.
    """
    age = face_info.get("age", 30)
    dom_em = emotion_profile.get("dominant_emotion", "neutral")
    valence = emotion_profile.get("valence", "")
    intensity = emotion_profile.get("emotional_intensity", "")
    stress_level = stress_info.get("microstress_level", "")

    # базові значення
    O = 55
    C = 55
    E = 50
    A = 55
    N = 50

    # валентність та екстраверсія
    if valence == "переважно позитивна":
        E += 15
        N -= 10
    if valence == "переважно негативна":
        E -= 10
        N += 15

    # інтенсивність
    if intensity == "висока":
        E += 5
        N += 5
    if intensity == "низька":
        E -= 5

    # стрес
    if stress_level == "високий":
        N += 15
        C -= 5
    elif stress_level == "низький":
        N -= 10

    # домінантні емоції
    if dom_em == "angry":
        A -= 10
        E += 5
    if dom_em == "sad":
        N += 10
        E -= 5
    if dom_em == "fear":
        N += 10
    if dom_em == "happy":
        A += 5

    # вік (дуже грубо)
    if age < 25:
        O += 5
        N += 5
    elif age > 45:
        C += 5
        N -= 5

    def clamp(x): return int(max(0, min(100, round(x))))

    scores = {
        "openness": clamp(O),
        "conscientiousness": clamp(C),
        "extraversion": clamp(E),
        "agreeableness": clamp(A),
        "neuroticism": clamp(N),
    }

    descriptions = {
        "openness": "Відкритість до нового, креативність, гнучкість мислення.",
        "conscientiousness": "Організованість, відповідальність, дисципліна.",
        "extraversion": "Потреба у спілкуванні, енергійність, активність.",
        "agreeableness": "Доброжичливість, готовність до співпраці, мʼякість.",
        "neuroticism": "Рівень внутрішньої напруги, схильність до тривоги.",
    }

    return scores, descriptions


def build_personality_profile(face_info, emotion_profile, stress_info):
    scores, descriptions = estimate_big_five(face_info, emotion_profile, stress_info)
    radical = estimate_radical(
        emotion_profile.get("dominant_emotion", "neutral"),
        stress_info.get("microstress_level", "")
    )

    # 🔥 Додаємо повний опис радикала
    radical_description = RADICAL_DESCRIPTIONS.get(radical, "Опис відсутній.")

    return {
        "big_five_scores": scores,
        "big_five_descriptions": descriptions,
        "radical": radical,
        "radical_description": radical_description
    }