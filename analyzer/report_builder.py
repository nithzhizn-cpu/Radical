# analyzer/report_builder.py
# v2 — Professional Psychological Report Generator

from typing import Dict, Any


# ---------------------------------------------------------
# UTILS
# ---------------------------------------------------------

def bar(value: int) -> str:
    """Графічна шкала Big Five."""
    filled = int(value / 5)
    empty = 20 - filled
    return "█" * filled + "░" * empty + f" ({value})"


def confidence_score(face_info: Dict[str, Any], emotion: Dict[str, Any]) -> int:
    """Оцінка достовірності профілю."""
    score = 90

    # Якщо модель сумнівається у віці / статі — мінус
    if face_info.get("age", 0) in (0, None):
        score -= 15
    if not face_info.get("gender"):
        score -= 10

    # Якщо емоція "neutral" — інтерпретація менш точна
    if (emotion.get("dominant_emotion") or "").lower() == "neutral":
        score -= 10

    return max(40, min(97, score))  # діапазон 40–97%


# ---------------------------------------------------------
# MAIN REPORT
# ---------------------------------------------------------

def build_full_report(
    face: Dict[str, Any],
    emotion: Dict[str, Any],
    stress: Dict[str, Any],
    personality: Dict[str, Any],
    professional: Dict[str, Any],
    physio: Dict[str, Any],
) -> str:

    big = personality["big_five_scores"]
    radical = personality["radical"]
    radical_desc = personality["radical_description"]
    radical_short = personality["radical_short"]
    radical_key = personality["radical_key"]

    roles = professional["recommended_roles"]
    risks = professional["risks"]
    work = professional["work_style"]
    comm = professional["communication_style"]

    agreeability = big["agreeableness"]
    neuro = big["neuroticism"]
    extr = big["extraversion"]

    # ---------------------------------------------------------
    # ARCHETYPE (simple but powerful)
    # ---------------------------------------------------------
    if extr > 60 and agreeability > 55:
        archetype = "Комунікатор / Ведучий (ENFJ-style)"
    elif extr < 45 and neuro < 50:
        archetype = "Аналітик / Стратег (INTJ-style)"
    elif agreeability > 65 and neuro > 55:
        archetype = "Емпат / Підтримуючий тип (INFP-style)"
    else:
        archetype = "Універсальний адаптивний тип"

    # ---------------------------------------------------------
    # SHORT MICRO-PORTRAIT
    # ---------------------------------------------------------
    microportrait = (
        f"Людина з домінуючим радикалом «{radical}». Поведінка поєднує риси "
        f"{radical_short.lower()}. Емоційний фон: {emotion.get('dominant_emotion')}. "
        f"Міміка та фізіогномічні ознаки вказують на {physio.get('short_summary').lower()}."
    )

    # ---------------------------------------------------------
    # STRESS FORECAST
    # ---------------------------------------------------------
    stress_level = stress.get("microstress_level", 0.0)

    if stress_level < 0.3:
        stress_forecast = (
            "У стресі зберігає контроль, рішення приймає раціонально. "
            "Малоймовірні різкі емоційні реакції."
        )
    elif stress_level < 0.7:
        stress_forecast = (
            "Стрес переноситься помірно. Можлива підвищена напруга, "
            "але самоконтроль зазвичай зберігається."
        )
    else:
        stress_forecast = (
            "Висока реактивність. Можливі різкі зміни настрою, "
            "звуження уваги та імпульсивність."
        )

    # ---------------------------------------------------------
    # CONFIDENCE
    # ---------------------------------------------------------
    confidence = confidence_score(face, emotion)

    # ---------------------------------------------------------
    # BUILD REPORT
    # ---------------------------------------------------------
    report = f"""
=============================
   🧠 ПСИХОЛОГІЧНИЙ ПРОФІЛЬ
=============================

📌 **Загальна характеристика**
{microportrait}

----------------------------------
II. 🧩 **Особистісний профіль (Big Five)**
----------------------------------

Openness:        {bar(big['openness'])}
Conscientious:   {bar(big['conscientiousness'])}
Extraversion:    {bar(big['extraversion'])}
Agreeableness:   {bar(big['agreeableness'])}
Neuroticism:     {bar(big['neuroticism'])}

----------------------------------
III. 🎭 **Провідний радикал: {radical}**
----------------------------------
📌 Коротко:
{radical_short}

📌 Детальний опис:
{radical_desc}

----------------------------------
IV. 🧬 **Архетип поведінки**
----------------------------------
{archetype}

----------------------------------
V. 👁 **Фізіогномічний профіль**
----------------------------------
{physio.get('age_morphology')}
{physio.get('gender_morphology')}
{physio.get('mimic_description')}

📌 Домінантні риси:
- {physio['dominant_features'][0]}
- {physio['dominant_features'][1]}
- {physio['dominant_features'][2]}

----------------------------------
VI. 🔧 **Робоча поведінка**
----------------------------------
• {work[0]}
• {work[1]}

----------------------------------
VII. 🤝 **Комунікація**
----------------------------------
• {comm[0]}

----------------------------------
VIII. ⚠️ **Поведінкові ризики**
----------------------------------
• {risks[0]}

----------------------------------
IX. 🚀 **Професійні ролі**
----------------------------------
• {roles[0]}

----------------------------------
X. 🔥 **Прогноз поведінки в стресі**
----------------------------------
{stress_forecast}

----------------------------------
XI. 🧪 **Рівень достовірності аналізу**
----------------------------------
{confidence}%


=============================
📘 Кінець звіту
=============================
"""

    return report.strip()