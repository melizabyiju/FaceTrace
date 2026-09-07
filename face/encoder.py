"""Face encoding/embedding module using DeepFace."""
from deepface import DeepFace


def encode_face(image_path: str, model_name: str = "VGG-Face",
                detector_backend: str = "opencv") -> dict:
    """
    Generate a face embedding vector for the given image.
    
    Args:
        image_path: Path to the image file.
        model_name: DeepFace model to use (VGG-Face, Facenet, ArcFace, etc.).
        detector_backend: Face detector backend (opencv, ssd, mtcnn, etc.).
    
    Returns:
        dict with keys: success, embedding, facial_area, model, embedding_size
    """
    try:
        embeddings = DeepFace.represent(
            img_path=image_path,
            model_name=model_name,
            detector_backend=detector_backend,
            enforce_detection=True
        )
        
        if not embeddings:
            return {"success": False, "error": "No face embedding generated"}
        
        emb = embeddings[0]
        return {
            "success": True,
            "embedding": emb["embedding"],
            "facial_area": emb.get("facial_area", {}),
            "model": model_name,
            "embedding_size": len(emb["embedding"])
        }
    except ValueError as e:
        return {"success": False, "error": f"No face detected: {e}"}
    except Exception as e:
        return {"success": False, "error": f"Encoding error: {e}"}
