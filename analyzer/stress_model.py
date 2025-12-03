import cv2
import numpy as np

def detect_microstress(img_path: str):
    """
    Дуже спрощений індикатор рівня напруги:
    - загальний контраст
    - різкість (Laplacian variance)
    Це не медичний показник, а лише евристика.
    """
    img = cv2.imread(img_path)
    if img is None:
        return {
            "microstress_level": "невідомий",
            "contrast": 0.0,
            "sharpness": 0.0,
            "notes": ["Неможливо прочитати зображення."],
        }

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    contrast = float(gray.std())
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    notes = []

    # рівень стресу (дуже грубо)
    score = contrast * 0.6 + sharpness * 0.4

    if score > 120:
        level = "високий"
        notes.append("Можлива підвищена напруга або зосередженість.")
    elif score > 70:
        level = "середній"
        notes.append("Стан помірної напруги, робочий режим.")
    else:
        level = "низький"
        notes.append("Загальний рівень напруги невисокий або стан розслабленості.")

    return {
        "microstress_level": level,
        "contrast": contrast,
        "sharpness": sharpness,
        "score": score,
        "notes": notes,
    }
