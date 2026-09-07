"""Face matching / comparison module."""
import os
import tempfile
import requests
from deepface import DeepFace


def compare_faces(img1_path: str, img2_path: str, model_name: str = "VGG-Face",
                  detector_backend: str = "opencv") -> dict:
    """
    Compare two face images and return similarity metrics.
    
    Returns dict with: verified, distance, threshold, model,
                       similarity_metric, similarity_percent
    """
    try:
        result = DeepFace.verify(
            img1_path=img1_path,
            img2_path=img2_path,
            model_name=model_name,
            detector_backend=detector_backend,
            enforce_detection=False
        )
        
        distance = result["distance"]
        threshold = result["threshold"]
        metric = result.get("similarity_metric", "cosine")
        
        # Compute similarity percentage
        if metric == "cosine":
            similarity_percent = round(max(0, (1 - distance)) * 100, 2)
        else:
            similarity_percent = round(max(0, (1 - distance / (threshold * 2))) * 100, 2)
        
        return {
            "verified": result["verified"],
            "distance": round(distance, 6),
            "threshold": threshold,
            "model": result.get("model", model_name),
            "similarity_metric": metric,
            "similarity_percent": similarity_percent
        }
    except Exception as e:
        return {
            "verified": False,
            "error": str(e),
            "similarity_percent": 0.0,
            "distance": 1.0,
            "threshold": 0.0
        }


def download_and_compare(input_image_path: str, candidate_url: str,
                         model_name: str = "VGG-Face") -> dict:
    """
    Download a candidate image from a URL and compare it with the input face.
    
    Returns comparison result dict, plus candidate_url and image_data.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(candidate_url, timeout=15, headers=headers)
        response.raise_for_status()
        
        content_type = response.headers.get("content-type", "")
        if "image" not in content_type and len(response.content) < 1000:
            return {
                "verified": False,
                "error": "URL did not return an image",
                "candidate_url": candidate_url,
                "similarity_percent": 0.0
            }
        
        suffix = ".jpg"
        if "png" in content_type:
            suffix = ".png"
        elif "webp" in content_type:
            suffix = ".webp"
        
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(response.content)
            tmp_path = tmp.name
        
        img_bytes = response.content
        try:
            result = compare_faces(input_image_path, tmp_path, model_name)
            result["candidate_url"] = candidate_url
            result["image_data"] = img_bytes
            return result
        except Exception as e:
            return {
                "verified": False,
                "error": f"Comparison failed: {e}",
                "candidate_url": candidate_url,
                "similarity_percent": 0.0,
                "image_data": img_bytes
            }
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
    
    except requests.RequestException as e:
        return {
            "verified": False,
            "error": f"Download failed: {e}",
            "candidate_url": candidate_url,
            "similarity_percent": 0.0,
            "image_data": b""
        }
    except Exception as e:
        return {
            "verified": False,
            "error": f"Comparison failed: {e}",
            "candidate_url": candidate_url,
            "similarity_percent": 0.0,
            "image_data": b""
        }
