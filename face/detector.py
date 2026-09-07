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
    
    Returns list of detected face dicts with facial_area info.
    Each dict contains keys: 'face', 'facial_area', 'confidence'.
    """
    try:
        faces = DeepFace.extract_faces(
            img_path=image_path,
            detector_backend=detector_backend,
            enforce_detection=True,
            align=True
        )
        return faces
    except ValueError:
        return []
    except Exception as e:
        print(f"[FaceDetect] Error: {e}")
        return []


def get_face_count(image_path: str, detector_backend: str = "opencv") -> int:
    """Return the number of faces detected."""
    return len(detect_faces(image_path, detector_backend))
