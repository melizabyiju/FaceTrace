"""Face detection, encoding, and matching module."""
from .detector import detect_faces, validate_image
from .encoder import encode_face
from .matcher import compare_faces, download_and_compare
