from typing import Dict

def build_professional_profile(personality: Dict):
    """
    На основі Big Five + радикала формує:
    - рекомендовані ролі
    - стиль роботи
    - ризики на роботі
    - стиль комунікації
    """
    scores = personality["big_five_scores"]
    radical = personality["radical"]

    O = scores["openness"]
    C = scores["conscientiousness"]
    E = scores["extraversion"]
    A = scores["agreeableness"]
    N = scores["neuroticism"]

    roles = []
    communication = []
    work_style = []
    risks = []

    # ролі
    if O >= 60:
        roles.append("креативні ролі (маркетинг, дизайн, генерація ідей).")
    if C >= 60:
        roles.append("структурні ролі (менеджмент процесів, аналітика, контроль якості).")
    if E >= 60:
        roles.append("роль публічного представника, продажі, переговори.")
    if A >= 60:
        roles.append("командні ролі, медіація, HR, підтримка людей.")
    if N >= 60:
        roles.append("ролі з високою чутливістю до ризиків (перевірка, аудит, безпека), але з контролем навантаження.")

    if not roles:
        roles.append("універсальні робочі ролі зі збалансованим навантаженням.")

    # стиль роботи
    if C >= 60:
        work_style.append("Любить порядок, системність та чіткі правила.")
    else:
        work_style.append("Може віддавати перевагу більш вільному, гнучкому стилю роботи.")

    if E >= 60:
        work_style.append("Комфортно почувається в середовищі з великою кількістю спілкування.")
    else:
        work_style.append("Потребує часу на самостійні задачі та усамітнення.")

    if N >= 60:
        risks.append("Схильність до перенапруги та емоційного вигорання при високому стресі.")
    if A < 40:
        risks.append("Можливі конфлікти через прямолінійність або жорсткість у відстоюванні позиції.")
    if C < 40:
        risks.append("Ризик прокрастинації й труднощів із доведенням задач до кінця.")

    if not risks:
        risks.append("Серйозних поведінкових ризиків не видно, важливе лише дотримання балансу навантаження.")

    # стиль комунікації
    if "Збудливий" in radical:
        communication.append("Краще говорити прямо, по суті, без затягувань, але з повагою.")
    if "Гіпертимний" in radical:
        communication.append("Підходить енергійний, живий стиль спілкування, з акцентом на можливості.")
    if "Емотивний" in radical:
        communication.append("Важливі мʼякість, підтримка та емоційна чутливість.")
    if "Тривожний" in radical:
        communication.append("Потрібні чіткі рамки, пояснення та відчуття безпеки.")
    if "Педантичний" in radical or "Застрягаючий" in radical:
        communication.append("Працюють структуровані аргументи, логіка, факти й послідовність.")

    if not communication:
        communication.append("Найкраще працює чесна, відкрита та поважна комунікація без маніпуляцій.")

    return {
        "recommended_roles": roles,
        "work_style": work_style,
        "risks": risks,
        "communication_style": communication,
    }
