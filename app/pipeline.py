"""Pipeline orchestration — connects face, search, hashing, and blockchain modules."""
import os
import sys
import hashlib
from datetime import datetime, timezone

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from face.detector import detect_faces, validate_image
from face.encoder import encode_face
from face.matcher import download_and_compare
from search.serpapi_provider import SerpAPIProvider
from hashing.fingerprint import create_verification_fingerprint, reverify_fingerprint
from blockchain.client import BlockchainClient
from app.config import Config


class FaceTracePipeline:
    """End-to-end pipeline: face → search → fingerprint → blockchain → verify."""

    def __init__(self):
        self.config = Config
        self.blockchain_client = None
        self.results = {}

    # ------------------------------------------------------------------ #
    # Step 1 — Validate image & detect faces                              #
    # ------------------------------------------------------------------ #
    def step1_validate_and_detect(self, image_path: str) -> dict:
        """Validate the image file and detect faces in it."""
        validation = validate_image(image_path)
        if not validation["valid"]:
            raise ValueError(f"Invalid image: {validation['error']}")

        faces = detect_faces(image_path, self.config.FACE_DETECTOR)
        if not faces:
            raise ValueError(
                "No face detected in the image. "
                "Please provide a clear photo containing a face."
            )

        if len(faces) > 1:
            print(
                f"⚠  Multiple faces detected ({len(faces)}). "
                "Using the primary (first) face."
            )

        self.results["face_count"] = len(faces)
        self.results["image_path"] = image_path
        return {"faces_detected": len(faces), "faces": faces}

    # ------------------------------------------------------------------ #
    # Step 2 — Generate face embedding                                    #
    # ------------------------------------------------------------------ #
    def step2_encode_face(self, image_path: str) -> dict:
        """Generate a numerical face embedding vector."""
        result = encode_face(
            image_path, self.config.FACE_MODEL, self.config.FACE_DETECTOR
        )
        if not result["success"]:
            raise ValueError(f"Face encoding failed: {result['error']}")

        self.results["embedding"] = result
        return result

    # ------------------------------------------------------------------ #
    # Step 3 — Reverse image search                                       #
    # ------------------------------------------------------------------ #
    def step3_search(self, image_path: str) -> list:
        """Perform a genuine reverse image search using SerpAPI Google Lens."""
        if not self.config.SERPAPI_KEY:
            raise ValueError(
                "SERPAPI_KEY is not configured. "
                "Get a free key at https://serpapi.com/ and add it to .env"
            )

        provider = SerpAPIProvider(self.config.SERPAPI_KEY)
        results = provider.search(image_path)

        if not results:
            raise ValueError(
                "No search results found. The image may be too unique or "
                "not indexed by any public source."
            )

        self.results["search_results"] = results
        self.results["search_provider"] = provider.provider_name
        return results

    # ------------------------------------------------------------------ #
    # Step 4 — Compare faces in candidates with input face                #
    # ------------------------------------------------------------------ #
    def step4_match_candidates(self, image_path: str, search_results: list) -> list:
        """Download candidate images and compare face embeddings."""
        matches = []

        for i, result in enumerate(search_results[:10]):
            image_url = result.image_url or result.thumbnail_url
            if not image_url:
                continue

            print(f"[Match] Checking candidate #{i+1}: {result.url[:80]}...")

            comparison = download_and_compare(
                image_path, image_url, self.config.FACE_MODEL
            )

            match_data = {
                "search_result": result,
                "comparison": comparison,
                "rank": i + 1,
            }
            matches.append(match_data)

        # Sort by similarity (highest first)
        matches.sort(
            key=lambda x: x["comparison"].get("similarity_percent", 0),
            reverse=True,
        )

        self.results["matches"] = matches
        return matches

    # ------------------------------------------------------------------ #
    # Step 5 — Create SHA-256 fingerprint                                 #
    # ------------------------------------------------------------------ #
    def step5_create_fingerprint(self, best_match: dict) -> dict:
        """Create a deterministic cryptographic fingerprint of the match."""
        search_result = best_match["search_result"]
        image_data = best_match["comparison"].get("image_data", b"")

        if not image_data:
            # Fallback: hash the URL itself
            image_data = search_result.url.encode("utf-8")

        fingerprint = create_verification_fingerprint(
            post_url=search_result.url,
            image_data=image_data,
            discovery_timestamp=search_result.discovery_timestamp,
        )

        self.results["fingerprint"] = fingerprint
        return fingerprint

    # ------------------------------------------------------------------ #
    # Step 6 — Write hash to blockchain                                   #
    # ------------------------------------------------------------------ #
    def step6_blockchain_register(
        self, fingerprint: dict, source_platform: str
    ) -> tuple:
        """Deploy contract (if needed) and register the hash on-chain."""
        if not self.blockchain_client:
            self.blockchain_client = BlockchainClient(
                rpc_url=self.config.BLOCKCHAIN_RPC_URL,
                private_key=self.config.PRIVATE_KEY,
                contract_address=self.config.CONTRACT_ADDRESS or None,
            )

            if not self.config.CONTRACT_ADDRESS:
                address = self.blockchain_client.deploy_contract()
                self.config.CONTRACT_ADDRESS = address

        # Deterministic verification ID
        verification_id = hashlib.sha256(
            f"{fingerprint['data_hash']}:{fingerprint['discovery_timestamp']}".encode()
        ).hexdigest()

        tx_result = self.blockchain_client.register_verification(
            verification_id=verification_id,
            data_hash=fingerprint["data_hash"],
            source=source_platform,
        )

        self.results["verification_id"] = verification_id
        self.results["tx_result"] = tx_result
        return verification_id, tx_result

    # ------------------------------------------------------------------ #
    # Step 7 — Re-verify against blockchain                               #
    # ------------------------------------------------------------------ #
    def step7_verify(
        self, verification_id: str, fingerprint: dict, image_data: bytes
    ) -> dict:
        """Re-compute the hash and compare with the on-chain record."""
        on_chain = self.blockchain_client.get_verification(verification_id)

        verification = reverify_fingerprint(
            post_url=fingerprint["post_url"],
            image_data=image_data,
            discovery_timestamp=fingerprint["discovery_timestamp"],
            on_chain_hash=on_chain["data_hash"],
        )

        self.results["verification"] = verification
        return verification
