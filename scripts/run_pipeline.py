#!/usr/bin/env python3
"""
FaceTrace — CLI Pipeline Runner
================================
Run the full pipeline from the command line without Streamlit.

Usage:
    python scripts/run_pipeline.py <image_path>
"""
import os
import sys
import json
import hashlib

# Project root
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from app.config import Config
from face.detector import detect_faces, validate_image
from face.encoder import encode_face
from face.matcher import download_and_compare
from search.serpapi_provider import SerpAPIProvider
from hashing.fingerprint import create_verification_fingerprint, reverify_fingerprint
from blockchain.client import BlockchainClient


BANNER = r"""
╔══════════════════════════════════════════════════════════════╗
║                        FACETRACE                             ║
║       Face Identification & Blockchain Verification          ║
╚══════════════════════════════════════════════════════════════╝
"""


def main():
    print(BANNER)

    # ── Parse args ──────────────────────────────────────────────────────
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_pipeline.py <image_path>")
        sys.exit(1)

    image_path = sys.argv[1]
    if not os.path.isabs(image_path):
        image_path = os.path.join(os.getcwd(), image_path)

    # ── Validate config ────────────────────────────────────────────────
    errors = Config.validate()
    if errors:
        print("\n⚠  Configuration warnings:")
        for e in errors:
            print(f"   • {e}")
        print()

    # ── Step 1 — Consent ───────────────────────────────────────────────
    print("=" * 60)
    print("CONSENT CONFIRMATION")
    print("=" * 60)
    print(
        "This tool performs reverse image search on the public web.\n"
        "Only proceed if:\n"
        "  • This is YOUR OWN face (selfie) or a photo you own.\n"
        "  • You have EXPLICIT CONSENT from the person in the photo.\n"
        "  • You are comfortable with this image being searched publicly.\n"
    )
    answer = input(
        "I confirm this is my own face / I have consent [y/n]: "
    ).strip().lower()
    if answer not in ("y", "yes"):
        print("\n❌ Consent not given. Exiting.")
        sys.exit(0)
    print("\n✅ Consent confirmed.\n")

    # ── Step 2 — Validate & Detect Face ────────────────────────────────
    print("=" * 60)
    print("STEP 1 — Face Detection")
    print("=" * 60)
    validation = validate_image(image_path)
    if not validation["valid"]:
        print(f"❌ Invalid image: {validation['error']}")
        sys.exit(1)
    print(f"  Image: {image_path}")
    print(f"  Size:  {validation['width']}x{validation['height']}")

    faces = detect_faces(image_path, Config.FACE_DETECTOR)
    if not faces:
        print("❌ No face detected. Please use a clear face photo.")
        sys.exit(1)
    print(f"  ✅ {len(faces)} face(s) detected\n")

    # ── Step 3 — Face Encoding ─────────────────────────────────────────
    print("=" * 60)
    print("STEP 2 — Face Encoding")
    print("=" * 60)
    encoding = encode_face(image_path, Config.FACE_MODEL, Config.FACE_DETECTOR)
    if not encoding["success"]:
        print(f"❌ Encoding failed: {encoding['error']}")
        sys.exit(1)
    print(f"  Model:          {encoding['model']}")
    print(f"  Embedding size: {encoding['embedding_size']}D")
    print(f"  ✅ Face embedding generated\n")

    # ── Step 4 — Reverse Image Search ──────────────────────────────────
    print("=" * 60)
    print("STEP 3 — Reverse Image Search")
    print("=" * 60)
    if not Config.SERPAPI_KEY:
        print("❌ SERPAPI_KEY not set. Add it to .env")
        sys.exit(1)

    provider = SerpAPIProvider(Config.SERPAPI_KEY)
    search_results = provider.search(image_path)

    if not search_results:
        print("❌ No search results found.")
        sys.exit(1)

    print(f"\n  ✅ Found {len(search_results)} result(s):")
    for i, r in enumerate(search_results[:5]):
        print(f"\n  Result #{i+1}:")
        print(f"    Platform: {r.platform}")
        print(f"    Title:    {r.title[:60]}")
        print(f"    URL:      {r.url}")
    print()

    # ── Step 5 — Face Matching ─────────────────────────────────────────
    print("=" * 60)
    print("STEP 4 — Face Matching")
    print("=" * 60)
    matches = []
    for i, r in enumerate(search_results[:10]):
        img_url = r.image_url or r.thumbnail_url
        if not img_url:
            continue
        print(f"  Checking candidate #{i+1}...")
        comp = download_and_compare(image_path, img_url, Config.FACE_MODEL)
        matches.append({"search_result": r, "comparison": comp, "rank": i + 1})

    matches.sort(
        key=lambda x: x["comparison"].get("similarity_percent", 0), reverse=True
    )

    if matches:
        best = matches[0]
        sim = best["comparison"].get("similarity_percent", 0)
        print(f"\n  ✅ Best match: {sim:.1f}% similarity")
        print(f"     Platform:  {best['search_result'].platform}")
        print(f"     URL:       {best['search_result'].url}")
    else:
        print("  ⚠  No face matches found in candidates.")
        # Continue with best search result anyway
        matches = [
            {
                "search_result": search_results[0],
                "comparison": {"image_data": b"", "similarity_percent": 0},
                "rank": 1,
            }
        ]
    print()

    # ── Step 6 — SHA-256 Fingerprint ───────────────────────────────────
    print("=" * 60)
    print("STEP 5 — SHA-256 Fingerprint")
    print("=" * 60)
    best_match = matches[0]
    sr = best_match["search_result"]
    image_data = best_match["comparison"].get("image_data", b"")
    if not image_data:
        image_data = sr.url.encode("utf-8")

    fingerprint = create_verification_fingerprint(
        post_url=sr.url,
        image_data=image_data,
        discovery_timestamp=sr.discovery_timestamp,
    )
    print(f"  Data Hash:      {fingerprint['data_hash']}")
    print(f"  Image Hash:     {fingerprint['image_hash']}")
    print(f"  Timestamp:      {fingerprint['discovery_timestamp']}")
    print(f"  ✅ Fingerprint created\n")

    # ── Step 7 — Blockchain ────────────────────────────────────────────
    print("=" * 60)
    print("STEP 6 — Blockchain Record")
    print("=" * 60)
    try:
        client = BlockchainClient(
            rpc_url=Config.BLOCKCHAIN_RPC_URL,
            private_key=Config.PRIVATE_KEY,
            contract_address=Config.CONTRACT_ADDRESS or None,
        )

        if not Config.CONTRACT_ADDRESS:
            address = client.deploy_contract()
            print(f"  Contract deployed at: {address}")

        verification_id = hashlib.sha256(
            f"{fingerprint['data_hash']}:{fingerprint['discovery_timestamp']}".encode()
        ).hexdigest()

        tx = client.register_verification(
            verification_id=verification_id,
            data_hash=fingerprint["data_hash"],
            source=sr.platform,
        )
        print(f"  Transaction Hash: 0x{tx['tx_hash']}")
        print(f"  Block Number:     {tx['block_number']}")
        print(f"  Gas Used:         {tx['gas_used']}")
        print(f"  Status:           {tx['status']}")
        print(f"  Verification ID:  {verification_id}")
        print(f"  ✅ Hash recorded on blockchain\n")
    except Exception as e:
        print(f"  ❌ Blockchain error: {e}")
        sys.exit(1)

    # ── Step 8 — Re-Verification ───────────────────────────────────────
    print("=" * 60)
    print("STEP 7 — On-Chain Re-Verification")
    print("=" * 60)
    on_chain = client.get_verification(verification_id)
    verification = reverify_fingerprint(
        post_url=fingerprint["post_url"],
        image_data=image_data,
        discovery_timestamp=fingerprint["discovery_timestamp"],
        on_chain_hash=on_chain["data_hash"],
    )
    print(f"  On-chain hash:   {verification['on_chain_hash']}")
    print(f"  Recomputed hash: {verification['recomputed_hash']}")
    print()

    if verification["verified"]:
        print("  ╔════════════════════════════════════════════╗")
        print("  ║   ✅  BLOCKCHAIN VERIFIED                  ║")
        print("  ║   Hashes match — data integrity confirmed  ║")
        print("  ╚════════════════════════════════════════════╝")
    else:
        print("  ╔════════════════════════════════════════════╗")
        print("  ║   ❌  VERIFICATION FAILED                  ║")
        print("  ║   Hashes do NOT match — possible tampering ║")
        print("  ╚════════════════════════════════════════════╝")

    print()
    print("Pipeline complete.")


if __name__ == "__main__":
    main()
