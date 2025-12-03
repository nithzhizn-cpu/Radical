import cv2
import numpy as np
import mediapipe as mp


mp_face_mesh = mp.solutions.face_mesh


def _distance(p1, p2):
    return float(np.linalg.norm(np.array(p1) - np.array(p2)))


def _load_landmarks(img_path: str):
    img = cv2.imread(img_path)
    if img is None:
        return None, None, None

    h, w = img.shape[:2]

    with mp_face_mesh.FaceMesh(
        static_image_mode=True,
        refine_landmarks=False,
        max_num_faces=1,
        min_detection_confidence=0.5,
    ) as face_mesh:
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        res = face_mesh.process(rgb)

    if not res.multi_face_landmarks:
        return None, w, h

    lm = res.multi_face_landmarks[0].landmark
    landmarks = [(p.x * w, p.y * h) for p in lm]
    return landmarks, w, h


def detect_microstress(img_path: str, face_info: dict | None = None):
    """
    Евристичний аналіз мікростресу:
    - очі (розкритість повік)
    - брови (напруження)
    - рот (стиснення губ)
    - базовий шум (розмитість)
    """
    landmarks, w, h = _load_landmarks(img_path)

    if landmarks is None:
        # Якщо не вдалося зчитати лендмарки — повертаємо “середній” стрес
        return {
            "microstress_level": 50,
            "stress_label": "середній",
            "factors": ["Не вдалося якісно зчитати мікроміміку."],
        }

    # орієнтовні індекси (MediaPipe FaceMesh):
    # очі
    lid_top_L = landmarks[159]   # верхнє повіко лівого ока
    lid_bot_L = landmarks[145]   # нижнє повіко лівого ока
    lid_top_R = landmarks[386]
    lid_bot_R = landmarks[374]

    # брови до очей
    brow_L = landmarks[70]
    brow_R = landmarks[300]

    # рот
    mouth_L = landmarks[61]
    mouth_R = landmarks[291]
    mouth_top = landmarks[13]
    mouth_bottom = landmarks[14]

    # розмір обличчя (нормалізація)
    chin = landmarks[152]
    forehead = landmarks[10]
    face_h = _distance(chin, forehead) or h

    # Метрики
    eye_open_L = _distance(lid_top_L, lid_bot_L) / face_h
    eye_open_R = _distance(lid_top_R, lid_bot_R) / face_h
    eye_open = (eye_open_L + eye_open_R) / 2.0

    brow_eye_L = _distance(brow_L, lid_top_L) / face_h
    brow_eye_R = _distance(brow_R, lid_top_R) / face_h
    brow_eye = (brow_eye_L + brow_eye_R) / 2.0

    mouth_width = _distance(mouth_L, mouth_R) / face_h
    mouth_height = _distance(mouth_top, mouth_bottom) / face_h
    mouth_ratio = mouth_height / (mouth_width + 1e-6)

    # Базова оцінка стресу
    stress_score = 50.0
    factors = []

    # Стиснуті очі -> напруга
    if eye_open < 0.020:
        stress_score += 15
        factors.append("Звужені очі (можлива напруга або роздратування).")
    elif eye_open > 0.040:
        stress_score += 5
        factors.append("Сильно розкриті очі (можлива тривога або напружена увага).")

    # Брови близько до очей -> напруга
    if brow_eye < 0.085:
        stress_score += 15
        factors.append("Опущені брови, м'язова напруга в ділянці лоба.")

    # Стиснені губи (малий mouth_height) при нормальній ширині -> стрес
    if mouth_ratio < 0.08:
        stress_score += 10
        factors.append("Стиснені губи (стримування емоцій або внутрішня напруга).")

    # Додатковий шум: якщо є face_info з високим нейротизмом (у тебе можна додати пізніше)
    # зараз просто залишимо цю гілку як місце для майбутніх фіч

    # Нормуємо 0..100
    stress_score = max(0.0, min(100.0, stress_score))

    if stress_score < 35:
        label = "низький"
        if not factors:
            factors.append("Зовнішні ознаки мікростресу мінімальні.")
    elif stress_score < 65:
        label = "середній"
    else:
        label = "високий"

    return {
        "microstress_level": int(round(stress_score)),
        "stress_label": label,
        "factors": factors,
    }