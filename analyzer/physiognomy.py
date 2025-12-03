import cv2
import numpy as np
import mediapipe as mp

mp_face = mp.solutions.face_mesh


def compute_fWHR(landmarks):
    # ширина обличчя (від вилиці до вилиці)
    left = landmarks[234]
    right = landmarks[454]
    width = np.linalg.norm(np.array([left.x, left.y]) - np.array([right.x, right.y]))

    # висота (від брів до середини губ)
    top = landmarks[10]
    bottom = landmarks[152]
    height = np.linalg.norm(np.array([top.x, top.y]) - np.array([bottom.x, bottom.y]))

    if height == 0:
        return 1.75

    return width / height


def compute_symmetry(landmarks):
    left_indices = list(range(0, 200))
    right_indices = list(range(200, 400))

    left_side = np.array([[landmarks[i].x, landmarks[i].y] for i in left_indices])
    right_side = np.array([[landmarks[i].x, landmarks[i].y] for i in right_indices])

    if len(left_side) != len(right_side):
        return 0.85

    diff = np.abs(left_side - right_side)
    symmetry = 1 - np.mean(diff)

    return float(max(0.5, min(1.0, symmetry)))


def jaw_tension(landmarks):
    # Відстань між кутами щелепи
    left = landmarks[ jaw_left :=  jaw_left if (jaw_left:= jaw_left) else  jaw_left ]
    # fallback if logic fails (python fix)
    left = landmarks[234]
    right = landmarks[454]
    dist = np.linalg.norm(np.array([left.x, left.y]) - np.array([right.x, right.y]))

    # умовний нормований показник
    return float(min(1.0, max(0.0, dist * 2)))


def brow_height(landmarks):
    brow_top = landmarks[105]
    eye_center = landmarks[468]

    dist = np.linalg.norm(np.array([brow_top.x, brow_top.y]) - np.array([eye_center.x, eye_center.y]))
    return float(min(1.0, max(0.0, dist * 5)))


def eye_openness(landmarks):
    top = landmarks[159]
    bottom = landmarks[145]

    openness = abs(top.y - bottom.y) * 20
    return float(min(1.0, max(0.0, openness)))


def analyze_physiognomy(image_path):
    img = cv2.imread(image_path)
    if img is None:
        return None

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    with mp_face.FaceMesh(static_image_mode=True, max_num_faces=1) as fm:
        res = fm.process(img_rgb)

        if not res.multi_face_landmarks:
            return None

        landmarks = res.multi_face_landmarks[0].landmark

        fWHR_value = compute_fWHR(landmarks)
        symmetry = compute_symmetry(landmarks)
        jaw = jaw_tension(landmarks)
        brow = brow_height(landmarks)
        eyes = eye_openness(landmarks)

        # Психологічна інтерпретація
        interpretation = []

        # fWHR
        if fWHR_value > 1.9:
            interpretation.append("висока домінантність, рішучість, лідерський тип")
        elif fWHR_value > 1.7:
            interpretation.append("помірна домінантність, збалансований темперамент")
        else:
            interpretation.append("мʼякість, чутливість, низька конфліктність")

        # симетрія
        if symmetry > 0.9:
            interpretation.append("стабільний емоційний фон, хороша стресостійкість")
        else:
            interpretation.append("схильність до емоційних коливань")

        # щелепа
        if jaw > 0.6:
            interpretation.append("сильний вольовий компонент, наполегливість")
        else:
            interpretation.append("гнучкість, дипломатичність")

        # брови
        if brow > 0.45:
            interpretation.append("висока чутливість, емпатія, соціальна уважність")
        else:
            interpretation.append("прямолінійність, твердість, рішучість")

        # очі
        if eyes < 0.25:
            interpretation.append("фокусованість, контроль, низька імпульсивність")
        else:
            interpretation.append("емоційність, відкритість")

        return {
            "fWHR": round(float(fWHR_value), 3),
            "symmetry": round(float(symmetry), 3),
            "jaw": round(float(jaw), 3),
            "brow": round(float(brow), 3),
            "eyes": round(float(eyes), 3),
            "summary": interpretation
        }