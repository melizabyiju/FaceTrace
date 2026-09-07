"""Deterministic SHA-256 fingerprinting for verification records."""
import hashlib
from datetime import datetime, timezone


def calculate_sha256_file(file_path: str) -> str:
    """Calculate SHA-256 hash of a file's bytes."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def calculate_sha256_bytes(data: bytes) -> str:
    """Calculate SHA-256 hash of raw bytes."""
    return hashlib.sha256(data).hexdigest()


def calculate_sha256_string(data: str) -> str:
    """Calculate SHA-256 hash of a UTF-8 string."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def create_verification_fingerprint(
    post_url: str,
    image_data: bytes,
    discovery_timestamp: str = None
) -> dict:
    """
    Create a deterministic fingerprint of discovered post data.

    Hash formula:
        SHA-256( post_url  + "|" + SHA-256(image_data) + "|" + timestamp )

    Determinism guarantee:
        Same URL + same image bytes + same timestamp  →  same data_hash.
        Any change in any input                       →  different data_hash.

    Args:
        post_url:            The URL of the discovered post/page.
        image_data:          Raw bytes of the discovered image.
        discovery_timestamp: ISO-8601 timestamp string; auto-generated if omitted.

    Returns:
        dict with keys: data_hash, post_url, image_hash, discovery_timestamp, hash_input
    """
    if discovery_timestamp is None:
        discovery_timestamp = datetime.now(timezone.utc).isoformat()

    image_hash = calculate_sha256_bytes(image_data)
    combined = f"{post_url}|{image_hash}|{discovery_timestamp}"
    data_hash = calculate_sha256_string(combined)

    return {
        "data_hash": data_hash,
        "post_url": post_url,
        "image_hash": image_hash,
        "discovery_timestamp": discovery_timestamp,
        "hash_input": combined
    }


def reverify_fingerprint(
    post_url: str,
    image_data: bytes,
    discovery_timestamp: str,
    on_chain_hash: str
) -> dict:
    """
    Re-compute the fingerprint and compare with the on-chain hash.

    Args:
        post_url:            Same URL used during registration.
        image_data:          Same image bytes used during registration.
        discovery_timestamp: Same timestamp used during registration.
        on_chain_hash:       The data_hash retrieved from the blockchain.

    Returns:
        dict with keys: verified, recomputed_hash, on_chain_hash, match, image_hash
    """
    image_hash = calculate_sha256_bytes(image_data)
    combined = f"{post_url}|{image_hash}|{discovery_timestamp}"
    recomputed_hash = calculate_sha256_string(combined)

    verified = recomputed_hash == on_chain_hash

    return {
        "verified": verified,
        "recomputed_hash": recomputed_hash,
        "on_chain_hash": on_chain_hash,
        "match": "VERIFIED ✓" if verified else "MISMATCH ✗",
        "image_hash": image_hash
    }
