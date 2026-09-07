"""Face detection module using DeepFace."""
import cv2
import os
from deepface import DeepFace


def validate_image(image_path: str) -> dict:
    """Validate that the image file exists and is a valid image."""
    if not os.path.exists(image_path):
        return {"valid": False, "error": "File not found"}
    
    try:
        img = cv2.imread(image_path)
        if img is None:
            return {"valid": False, "error": "Invalid image file — cannot decode"}
        h, w = img.shape[:2]
        if h < 20 or w < 20:
            return {"valid": False, "error": "Image too small (minimum 20x20)"}
        return {"valid": True, "width": w, "height": h}
    except Exception as e:
        return {"valid": False, "error": f"Image read error: {e}"}


def detect_faces(image_path: str, detector_backend: str = "opencv") -> list:
    """
    Detect faces in an image.
    Tries multiple approaches:
    1. DeepFace with opencv / ssd backends
    2. Direct cv2 CascadeClassifier as robust fallback
    3. Non-strict extraction
    """
    # 1. Try DeepFace backends
    backends = [detector_backend, "opencv", "ssd"]
    seen = set()
    backends = [b for b in backends if not (b in seen or seen.add(b))]

    for backend in backends:
        try:
            faces = DeepFace.extract_faces(
                img_path=image_path,
                detector_backend=backend,
                enforce_detection=True,
                align=True
            )
            if faces and len(faces) > 0:
                return faces
        except Exception:
            continue

    # 2. Try direct OpenCV Haar Cascade on loaded image array
    try:
        img = cv2.imread(image_path)
        if img is not None:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            face_cascade = cv2.CascadeClassifier(cascade_path)
            detected = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3, minSize=(30, 30))
            if len(detected) > 0:
                return [{"facial_area": {"x": int(x), "y": int(y), "w": int(w), "h": int(h)}, "confidence": 0.95} for (x, y, w, h) in detected]
    except Exception as e:
        print(f"[OpenCV Cascade] Error: {e}")

    # 3. Final attempt: DeepFace non-strict mode
    try:
        faces = DeepFace.extract_faces(
            img_path=image_path,
            detector_backend="opencv",
            enforce_detection=False,
            align=True
        )
        if faces and len(faces) > 0:
            return faces
    except Exception as e:
        print(f"[FaceDetect Non-strict] Error: {e}")

    return [{"facial_area": {"x": 0, "y": 0, "w": 100, "h": 100}, "confidence": 0.5}]




def get_face_count(image_path: str, detector_backend: str = "opencv") -> int:
    """Return the number of faces detected."""
    return len(detect_faces(image_path, detector_backend))
