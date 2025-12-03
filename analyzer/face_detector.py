import cv2
import numpy as np
from deepface import DeepFace
import mediapipe as mp


mp_face_mesh = mp.solutions.face_mesh


def _run_deepface(img_path: str):
    """
    Обгортка над DeepFace.analyze:
    повертає age / gender / emotion / race та домінанти.
    """
    result = DeepFace.analyze(
        img_path=img_path,
        actions=["emotion", "age", "gender", "race"],
        enforce_detection=True
    )

    # DeepFace може повертати список
    if isinstance(result, list):
        result = result[0]

    age = int(result.get("age", 0))
    gender = str(result.get("gender", "") or "")
    emotion = dict(result.get("emotion", {}))
    dominant_emotion = str(result.get("dominant_emotion", "") or "")
    race = dict(result.get("race", {}))
    dominant_race = str(result.get("dominant_race", "") or "")

    return {
        "age": age,
        "gender": gender,
        "emotion": emotion,
        "dominant_emotion": dominant_emotion,
        "race": race,
        "dominant_race": dominant_race,
    }


def _run_facemesh(img_path: str):
    """
    Запускає MediaPipe FaceMesh та повертає:
    - список 468 лендмарок (x, y) у пікселях
    - базові метрики якості (frontal_score, blur_score)
    """
    img = cv2.imread(img_path)
    if img is None:
        return None

    h, w = img.shape[:2]

    # оцінка різкості (чим вище, тим краще)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()

    with mp_face_mesh.FaceMesh(
        static_image_mode=True,
        refine_landmarks=False,
        max_num_faces=1,
        min_detection_confidence=0.5,
    ) as face_mesh:
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        res = face_mesh.process(img_rgb)

    if not res.multi_face_landmarks:
        return None

    lm = res.multi_face_landmarks[0].landmark
    landmarks = []
    for p in lm:
        landmarks.append((p.x * w, p.y * h))

    # простенька евристика “наскільки лице фронтальне”
    # беремо відстані між лівим/правим оком та центром обличчя
    # і дивимось, наскільки вони симетричні
    def dist(a, b):
        return np.linalg.norm(np.array(a) - np.array(b))

    # індекси з face mesh (приблизно)
    # 33 – зовнішній кут правого ока, 263 – зовнішній кут лівого
    # 1 – “центр” обличчя
    try:
        center = landmarks[1]
        right_eye = landmarks[33]
        left_eye = landmarks[263]

        d_r = dist(center, right_eye)
        d_l = dist(center, left_eye)
        if d_r + d_l == 0:
            frontal_score = 0.0
        else:
            frontal_score = 1.0 - abs(d_r - d_l) / (d_r + d_l)
            frontal_score = float(max(0.0, min(1.0, frontal_score)))
    except Exception:
        frontal_score = 0.0

    return {
        "landmarks": landmarks,
        "blur_score": float(blur_score),
        "frontal_score": float(frontal_score),
        "image_size": (w, h),
    }


def detect_face_info(img_path: str):
    """
    Головна функція, яку викликає бот.

    Повертає словник:
    {
        "age": int,
        "gender": str,
        "emotion": {...},
        "dominant_emotion": str,
        "race": {...},
        "dominant_race": str,
        "landmarks": [(x, y), ...] або None,
        "blur_score": float,
        "frontal_score": float,
    }

    Якщо не вдалося нічого — повертає None
    """
    try:
        deep = _run_deepface(img_path)
    except Exception:
        return None

    mesh = _run_facemesh(img_path)

    if mesh is None:
        # повертаємо хоча б DeepFace-частину
        deep.update(
            {
                "landmarks": None,
                "blur_score": 0.0,
                "frontal_score": 0.0,
            }
        )
        return deep

    deep.update(
        {
            "landmarks": mesh["landmarks"],
            "blur_score": mesh["blur_score"],
            "frontal_score": mesh["frontal_score"],
        }
    )
    return deep