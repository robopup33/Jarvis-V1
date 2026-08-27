"""
Jarvis face recognition helpers (OpenCV Haar + template matching).
Imported by Jarvis.py — no extra pip packages beyond opencv-python + numpy.
"""
import os
import base64
import hashlib
import cv2
import numpy as np

FACE_SIZE = (120, 120)
FACE_MATCH_THRESHOLD = 0.55

_FACE_CASCADE = None

def _load_face_cascade():
    cascade_path = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
    cascade = cv2.CascadeClassifier(cascade_path)
    if cascade.empty():
        for alt in (
            "/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml",
            "/usr/local/share/opencv4/haarcascades/haarcascade_frontalface_default.xml",
        ):
            if os.path.exists(alt):
                cascade = cv2.CascadeClassifier(alt)
                if not cascade.empty():
                    break
    return cascade if not cascade.empty() else None

def get_face_cascade():
    global _FACE_CASCADE
    if _FACE_CASCADE is None:
        _FACE_CASCADE = _load_face_cascade()
    return _FACE_CASCADE

def detect_and_crop_face(bgr_frame, min_size=60):
    cascade = get_face_cascade()
    if cascade is None or bgr_frame is None:
        return None
    gray = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(min_size, min_size))
    if len(faces) == 0:
        return None
    x, y, w, h = max(faces, key=lambda r: r[2] * r[3])
    pad = int(0.1 * max(w, h))
    x1, y1 = max(0, x - pad), max(0, y - pad)
    x2 = min(gray.shape[1], x + w + pad)
    y2 = min(gray.shape[0], y + h + pad)
    crop = gray[y1:y2, x1:x2]
    if crop.size == 0:
        return None
    crop = cv2.resize(crop, FACE_SIZE, interpolation=cv2.INTER_AREA)
    return cv2.equalizeHist(crop)

def face_similarity(crop_a, crop_b):
    if crop_a is None or crop_b is None:
        return 0.0
    if crop_a.shape != crop_b.shape:
        crop_b = cv2.resize(crop_b, (crop_a.shape[1], crop_a.shape[0]))
    hist_a = cv2.calcHist([crop_a], [0], None, [64], [0, 256])
    hist_b = cv2.calcHist([crop_b], [0], None, [64], [0, 256])
    cv2.normalize(hist_a, hist_a)
    cv2.normalize(hist_b, hist_b)
    hist_score = float(cv2.compareHist(hist_a, hist_b, cv2.HISTCMP_CORREL))
    hist_score = max(0.0, min(1.0, (hist_score + 1.0) / 2.0))
    res = cv2.matchTemplate(crop_a, crop_b, cv2.TM_CCOEFF_NORMED)
    tmpl_score = float(res[0][0]) if res.size else 0.0
    tmpl_score = max(0.0, min(1.0, (tmpl_score + 1.0) / 2.0))
    return 0.45 * hist_score + 0.55 * tmpl_score

def encode_face_crop(crop):
    if crop is None:
        return None
    ok, buf = cv2.imencode(".png", crop)
    if not ok:
        return None
    return base64.b64encode(buf.tobytes()).decode("utf-8")

def decode_face_crop(b64_str):
    if not b64_str:
        return None
    try:
        raw = base64.b64decode(b64_str)
        arr = np.frombuffer(raw, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return None
        if img.shape[:2] != FACE_SIZE:
            img = cv2.resize(img, FACE_SIZE, interpolation=cv2.INTER_AREA)
        return img
    except Exception:
        return None

def save_user_face_templates(user_name, face_crops, face_model_dir, save_json_fn):
    templates = [encode_face_crop(c) for c in face_crops if c is not None]
    templates = [t for t in templates if t]
    path = os.path.join(face_model_dir, f"{hashlib.sha256(user_name.encode()).hexdigest()[:16]}.json")
    save_json_fn(path, {"user": user_name, "templates": templates, "version": 1})
    return len(templates)

def load_user_face_templates(user_name, face_model_dir, load_json_fn):
    path = os.path.join(face_model_dir, f"{hashlib.sha256(user_name.encode()).hexdigest()[:16]}.json")
    data = load_json_fn(path, {})
    crops = []
    for t in data.get("templates", []):
        c = decode_face_crop(t)
        if c is not None:
            crops.append(c)
    return crops

def verify_face_against_user(user_name, bgr_frame, face_model_dir, load_json_fn):
    enrolled = load_user_face_templates(user_name, face_model_dir, load_json_fn)
    if not enrolled:
        return False, 0.0, "No enrolled face templates found."
    live = detect_and_crop_face(bgr_frame)
    if live is None:
        return False, 0.0, "No face detected. Look straight at the camera."
    scores = [face_similarity(live, t) for t in enrolled]
    best = max(scores) if scores else 0.0
    matched = best >= FACE_MATCH_THRESHOLD
    msg = f"Match confidence {best:.0%}" if matched else f"Low confidence ({best:.0%}). Try again."
    return matched, best, msg
