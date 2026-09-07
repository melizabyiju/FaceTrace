"""Centralised configuration — reads from .env via python-dotenv."""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """All runtime settings, driven by environment variables."""

    # ── Search ──────────────────────────────────────────────────────────
    SERPAPI_KEY: str = os.getenv("SERPAPI_KEY", "")
    IMGBB_API_KEY: str = os.getenv("IMGBB_API_KEY", "")

    # ── Blockchain ──────────────────────────────────────────────────────
    BLOCKCHAIN_RPC_URL: str = os.getenv(
        "BLOCKCHAIN_RPC_URL", "http://127.0.0.1:8545"
    )
    PRIVATE_KEY: str = os.getenv(
        "PRIVATE_KEY",
        "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
    )
    CONTRACT_ADDRESS: str = os.getenv("CONTRACT_ADDRESS", "")
    CHAIN_ID: int = int(os.getenv("CHAIN_ID", "31337"))

    # ── Face Recognition ────────────────────────────────────────────────
    FACE_MODEL: str = os.getenv("FACE_MODEL", "VGG-Face")
    FACE_DETECTOR: str = os.getenv("FACE_DETECTOR", "opencv")
    SIMILARITY_THRESHOLD: float = float(
        os.getenv("SIMILARITY_THRESHOLD", "0.40")
    )

    # ── Demo ────────────────────────────────────────────────────────────
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "false").lower() == "true"

    @classmethod
    def validate(cls) -> list[str]:
        """Return a list of configuration errors (empty = OK)."""
        errors = []
        if not cls.SERPAPI_KEY:
            errors.append("SERPAPI_KEY is not set — reverse image search will fail.")
        if not cls.PRIVATE_KEY:
            errors.append("PRIVATE_KEY is not set — blockchain transactions will fail.")
        return errors
