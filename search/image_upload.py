"""Temporary image upload helpers to obtain a public URL."""
import os
import base64
import requests


def upload_to_0x0(image_path: str) -> str:
    """Upload an image to 0x0.st (no API key required)."""
    try:
        with open(image_path, "rb") as f:
            resp = requests.post("https://0x0.st", files={"file": f}, timeout=30)
        if resp.status_code == 200:
            url = resp.text.strip()
            if url.startswith("http"):
                return url
    except Exception as e:
        print(f"[Upload] 0x0.st failed: {e}")
    return ""


def upload_to_imgbb(image_path: str, api_key: str = "") -> str:
    """Upload an image to ImgBB (requires free API key)."""
    if not api_key:
        api_key = os.getenv("IMGBB_API_KEY", "")
    if not api_key:
        return ""
    try:
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        resp = requests.post(
            "https://api.imgbb.com/1/upload",
            data={"key": api_key, "image": b64},
            timeout=30,
        )
        if resp.status_code == 200:
            return resp.json()["data"]["url"]
    except Exception as e:
        print(f"[Upload] ImgBB failed: {e}")
    return ""


def upload_to_freeimage(image_path: str) -> str:
    """Upload to freeimage.host (no API key required for basic uploads)."""
    try:
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        resp = requests.post(
            "https://freeimage.host/api/1/upload",
            data={"key": "6d207e02198a847aa98d0a2a901485a5", "source": b64, "format": "json"},
            timeout=30,
        )
        if resp.status_code == 200:
            return resp.json()["image"]["url"]
    except Exception as e:
        print(f"[Upload] freeimage.host failed: {e}")
    return ""


def upload_image_for_url(image_path: str) -> str:
    """
    Upload a local image and return a publicly accessible URL.
    Tries multiple free hosting services in order.
    """
    # 1. ImgBB (if API key present)
    url = upload_to_imgbb(image_path)
    if url:
        return url

    # 2. freeimage.host (public key)
    url = upload_to_freeimage(image_path)
    if url:
        return url

    # 3. 0x0.st
    url = upload_to_0x0(image_path)
    if url:
        return url

    raise RuntimeError(
        "Could not upload image to any hosting service. "
        "Set IMGBB_API_KEY in .env or check your internet connection."
    )
