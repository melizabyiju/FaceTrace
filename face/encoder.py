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
    backends = [detector_backend, "opencv", "ssd"]
    seen = set()
    backends = [b for b in backends if not (b in seen or seen.add(b))]

    for backend in backends:
        try:
            embeddings = DeepFace.represent(
                img_path=image_path,
                model_name=model_name,
                detector_backend=backend,
                enforce_detection=True
            )
            if embeddings and len(embeddings) > 0:
                emb = embeddings[0]
                return {
                    "success": True,
                    "embedding": emb["embedding"],
                    "facial_area": emb.get("facial_area", {}),
                    "model": model_name,
                    "embedding_size": len(emb["embedding"])
                }
        except Exception:
            continue

    # Fallback to non-strict detection
    try:
        embeddings = DeepFace.represent(
            img_path=image_path,
            model_name=model_name,
            detector_backend="opencv",
            enforce_detection=False
        )
        if embeddings and len(embeddings) > 0:
            emb = embeddings[0]
            return {
                "success": True,
                "embedding": emb["embedding"],
                "facial_area": emb.get("facial_area", {}),
                "model": model_name,
                "embedding_size": len(emb["embedding"])
            }
    except Exception as e:
        return {"success": False, "error": f"Encoding error: {e}"}

    return {"success": False, "error": "No face could be encoded"}

