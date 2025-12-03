# analyzer/personality_model.py

from typing import Dict, Any, Optional
from .radicals import RADICALS  # очікуємо dict з описами радикалів


def _base_big_five_from_emotions(emotion_data: Dict[str, Any]) -> Dict[str, int]:
    """
    Базова евристика Big Five по емоціям та валентності.
    emotion_data:
      {
        "dominant_emotion": "happy",
        "valence": float,
        "emotion": {...}
      }
    """
    dom = emotion_data.get("dominant_emotion", "").lower()
    val = float(emotion_data.get("valence", 0.0))

    # базові середні значення
    openness = 55
    conscientiousness = 50
    extraversion = 50
    agreeableness = 50
    neuroticism = 50

    # валентність
    if val > 0.2:
        neuroticism -= 10
        extraversion += 5
    elif val < -0.2:
        neuroticism += 15
        agreeableness -= 5

    # по емоції
    if dom in ["happy", "surprise"]:
        extraversion += 10
        agreeableness += 5
    if dom in ["sad", "fear"]:
        neuroticism += 15
        extraversion -= 5
    if dom in ["angry", "disgust"]:
        neuroticism += 10
        agreeableness -= 10

    def clamp(x): return max(0, min(100, int(round(x))))

    return {
        "openness": clamp(openness),
        "conscientiousness": clamp(conscientiousness),
        "extraversion": clamp(extraversion),
        "agreeableness": clamp(agreeableness),
        "neuroticism": clamp(neuroticism),
    }


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

    def clamp(x): return max(0, min(100, int(round(x))))

    big_five["neuroticism"] = clamp(n)
    big_five["conscientiousness"] = clamp(c)
    return big_five


def _adjust_big_five_with_physio(big_five: Dict[str, int],
                                 physio: Optional[Dict[str, Any]]) -> Dict[str, int]:
    """
    Корекція Big Five за даними фізіогноміки:
      fWHR, symmetry, jaw, brow, eyes
    """
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

    # fWHR – домінантність / сила
    if fwh > 1.9:
        E += 8
        C += 5
        A -= 5
    elif fwh < 1.6:
        A += 5
        E -= 5

    # Симетрія – стабільність / стресостійкість
    if sym > 0.9:
        N -= 10
    elif sym < 0.8:
        N += 5

    # Щелепа – вольовий компонент
    if jaw > 0.6:
        C += 8
        E += 5
    else:
        A += 3

    # Брови – чутливість / емпатія
    if brow > 0.45:
        O += 5
        A += 5
        N += 3  # більше чутливості
    else:
        C += 3

    # Очі – контроль / імпульсивність
    if eyes < 0.25:
        N -= 5
        C += 5
    else:
        E += 5

    def clamp(x): return max(0, min(100, int(round(x))))

    return {
        "openness": clamp(O),
        "conscientiousness": clamp(C),
        "extraversion": clamp(E),
        "agreeableness": clamp(A),
        "neuroticism": clamp(N),
    }


def _select_radical(big_five: Dict[str, int],
                    emotion_data: Dict[str, Any],
                    stress_data: Dict[str, Any],
                    physio: Optional[Dict[str, Any]]) -> str:
    """
    Підбираємо ключ радикала (ключ у RADICALS) за сумарними даними.
    """
    dom = (emotion_data.get("dominant_emotion") or "").lower()
    val = float(emotion_data.get("valence", 0.0))
    stress = float(stress_data.get("microstress_level", 0.0))

    fwh = physio.get("fWHR", 1.75) if physio else 1.75
    sym = physio.get("symmetry", 0.85) if physio else 0.85
    eyes = physio.get("eyes", 0.5) if physio else 0.5
    brow = physio.get("brow", 0.5) if physio else 0.5

    E = big_five["extraversion"]
    N = big_five["neuroticism"]
    C = big_five["conscientiousness"]
    A = big_five["agreeableness"]

    # Приклади правил:
    # 1) Високий fWHR + високий E + високий N → збудливий
    if fwh > 1.9 and E > 60 and N > 60:
        return "excitable"

    # 2) Висока симетрія + високий C + низький N → ананкастний / педантичний
    if sym > 0.9 and C > 65 and N < 50:
        return "anankast"

    # 3) Високий N + низька симетрія + суміш страх/тривога → тривожний / сенситивний
    if N > 70 and sym < 0.85 and dom in ["fear", "sad"]:
        return "sensetive"

    # 4) Високий Е + низький A + злість/роздратування → агресивно-збудливий / епілептоїд
    if E > 60 and A < 45 and dom in ["angry", "disgust"]:
        return "epileptoid"

    # 5) Високий О + високі брови + позитивні емоції → демонстративний / істероїд
    if big_five["openness"] > 60 and brow > 0.45 and val > 0:
        return "hysteroid"

    # 6) Базовий fallback – якщо нічого не підійшло:
    if N < 50 and A > 55:
        return "harmonic"
    return "mixed"


def build_personality_profile(
    face_info: Dict[str, Any],
    emotion_data: Dict[str, Any],
    stress_data: Dict[str, Any],
    physio: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Формує Big Five + радикал Пономаренка + опис, з урахуванням фізіогноміки.
    """

    # 1) Базовий Big Five по емоціях
    big_five = _base_big_five_from_emotions(emotion_data)

    # 2) Корекція за стресом
    big_five = _adjust_big_five_with_stress(big_five, stress_data)

    # 3) Корекція за фізіогномікою
    big_five = _adjust_big_five_with_physio(big_five, physio)

    # 4) Вибір радикала
    radical_key = _select_radical(big_five, emotion_data, stress_data, physio)
    radical_info = RADICALS.get(radical_key, {
        "name": "Змішаний профіль",
        "short": "Комбінація кількох радикалів без вираженого домінування.",
        "description": "У структурі особистості проявляються риси різних радикалів, без чітко домінуючого типу.",
    })

    notes = []

    if physio:
        notes.append("Фізіогномічні ознаки враховані при формуванні профілю (форма обличчя, симетрія, очі, брови, щелепа).")
    if stress_data.get("microstress_level", 0) > 0.7:
        notes.append("Високий рівень мікростресу: короткостроково це може викривляти емоційні реакції.")

    return {
        "big_five_scores": big_five,
        "radical_key": radical_key,
        "radical": radical_info.get("name"),
        "radical_short": radical_info.get("short"),
        "radical_description": radical_info.get("description"),
        "physio_used": bool(physio),
        "notes": notes,
    }