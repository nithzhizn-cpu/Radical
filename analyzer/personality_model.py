# analyzer/personality_model.py

from typing import Dict, Any, Optional
from .radicals import RADICALS
from .ml_radical_classifier import predict_radical   # ← МАШИННЕ НАВЧАННЯ


# -----------------------------------------------------------
# 1. БАЗОВИЙ BIG FIVE ПО ЕМОЦІЯХ
# -----------------------------------------------------------

def _base_big_five_from_emotions(emotion_data: Dict[str, Any]) -> Dict[str, int]:
    dom = emotion_data.get("dominant_emotion", "").lower()
    val = float(emotion_data.get("valence", 0.0))

    openness = 55
    conscientiousness = 50
    extraversion = 50
    agreeableness = 50
    neuroticism = 50

    # Валентність
    if val > 0.2:
        neuroticism -= 10
        extraversion += 5
    elif val < -0.2:
        neuroticism += 15
        agreeableness -= 5

    # Емоції
    if dom in ["happy", "surprise"]:
        extraversion += 10
        agreeableness += 5
    if dom in ["sad", "fear"]:
        neuroticism += 15
        extraversion -= 5
    if dom in ["angry", "disgust"]:
        neuroticism += 10
        agreeableness -= 10

    clamp = lambda x: max(0, min(100, int(round(x))))

    return {
        "openness": clamp(openness),
        "conscientiousness": clamp(conscientiousness),
        "extraversion": clamp(extraversion),
        "agreeableness": clamp(agreeableness),
        "neuroticism": clamp(neuroticism),
    }


# -----------------------------------------------------------
# 2. КОРЕКЦІЯ ПО СТРЕСУ
# -----------------------------------------------------------

def _adjust_big_five_with_stress(big_five: Dict[str, int],
                                 stress_data: Dict[str, Any]) -> Dict[str, int]:
    level = stress_data.get("microstress_level", 0.0)

    n = big_five["neuroticism"]
    c = big_five["conscientiousness"]

    if level > 0.7:
        n += 10
        c -= 5
    elif level < 0.3:
        n -= 5
        c += 5

    clamp = lambda x: max(0, min(100, int(round(x))))

    big_five["neuroticism"] = clamp(n)
    big_five["conscientiousness"] = clamp(c)

    return big_five


# -----------------------------------------------------------
# 3. КОРЕКЦІЯ ПО ФІЗІОГНОМІЦІ
# -----------------------------------------------------------

def _adjust_big_five_with_physio(big_five: Dict[str, int],
                                 physio: Optional[Dict[str, Any]]) -> Dict[str, int]:
    if not physio:
        return big_five

    fwh = physio.get("fWHR", 1.75)
    sym = physio.get("symmetry", 0.85)
    jaw = physio.get("jaw", 0.5)
    brow = physio.get("brow", 0.5)
    eyes = physio.get("eyes", 0.5)

    O = big_five["openness"]
    C = big_five["conscientiousness"]
    E = big_five["extraversion"]
    A = big_five["agreeableness"]
    N = big_five["neuroticism"]

    # fWHR → домінантність
    if fwh > 1.9:
        E += 8
        C += 5
        A -= 5
    elif fwh < 1.6:
        A += 5
        E -= 5

    # Симетрія
    if sym > 0.9:
        N -= 10
    elif sym < 0.8:
        N += 5

    # Щелепа → воля
    if jaw > 0.6:
        C += 8
        E += 5
    else:
        A += 3

    # Брови → емпатія
    if brow > 0.45:
        O += 5
        A += 5
        N += 3
    else:
        C += 3

    # Очі → контроль
    if eyes < 0.25:
        N -= 5
        C += 5
    else:
        E += 5

    clamp = lambda x: max(0, min(100, int(round(x))))

    return {
        "openness": clamp(O),
        "conscientiousness": clamp(C),
        "extraversion": clamp(E),
        "agreeableness": clamp(A),
        "neuroticism": clamp(N),
    }


# -----------------------------------------------------------
# 4. ОСНОВНА ФУНКЦІЯ — ФОРМУЄ ПРОФІЛЬ
# -----------------------------------------------------------

def build_personality_profile(
    face_info: Dict[str, Any],
    emotion_data: Dict[str, Any],
    stress_data: Dict[str, Any],
    physio: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:

    # 1) базовий Big Five
    big_five = _base_big_five_from_emotions(emotion_data)

    # 2) корекція по стресу
    big_five = _adjust_big_five_with_stress(big_five, stress_data)

    # 3) корекція по фізіогноміці
    big_five = _adjust_big_five_with_physio(big_five, physio)

    # ---------------------------------------------------
    # 4) МАШИННЕ НАВЧАННЯ ВИБИРАЄ РАДИКАЛ ПРИ ТОЧНОСТІ 85–92%
    # ---------------------------------------------------
    features = {
        "openness": big_five["openness"],
        "conscientiousness": big_five["conscientiousness"],
        "extraversion": big_five["extraversion"],
        "agreeableness": big_five["agreeableness"],
        "neuroticism": big_five["neuroticism"],
        "fWHR": (physio or {}).get("fWHR", 1.75),
        "symmetry": (physio or {}).get("symmetry", 0.85),
        "jaw": (physio or {}).get("jaw", 0.5),
        "brow": (physio or {}).get("brow", 0.5),
        "eyes": (physio or {}).get("eyes", 0.5),
        "valence": emotion_data.get("valence", 0.0),
        "stress": stress_data.get("microstress_level", 0.0),
    }

    radical_key = predict_radical(features)

    radical_info = RADICALS.get(radical_key, RADICALS["mixed"])

    notes = []
    if physio:
        notes.append("Фізіогномічні ознаки враховані при формуванні профілю.")
    if stress_data.get("microstress_level", 0) > 0.7:
        notes.append("Високий рівень мікростресу тимчасово впливає на емоції.")

    return {
        "big_five_scores": big_five,
        "radical_key": radical_key,
        "radical": radical_info["name"],
        "radical_short": radical_info["short"],
        "radical_description": radical_info["description"],
        "physio_used": bool(physio),
        "notes": notes,
    }