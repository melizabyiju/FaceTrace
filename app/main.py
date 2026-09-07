"""
FaceTrace — Streamlit UI
========================
Provides a visual, step-by-step interface for the entire pipeline:
  Face upload → Consent → Detection → Search → Match → Fingerprint → Blockchain → Verify
"""
import os
import sys
import tempfile
import warnings

# Suppress verbose TensorFlow logs and deprecation warnings
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
warnings.filterwarnings("ignore")

# Ensure project root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from app.config import Config
from app.pipeline import FaceTracePipeline

# ── Page config ─────────────────────────────────────────────────────────
st.set_page_config(page_title="FaceTrace", page_icon="🔍", layout="wide")


def main():
    st.title("🔍 FaceTrace")
    st.caption("Face Identification & Blockchain Verification Pipeline")
    st.markdown(
        "**Pipeline:** Face Image → Detection → Encoding → "
        "Reverse Image Search → Face Matching → SHA-256 Fingerprint → "
        "Blockchain Record → On-Chain Verification"
    )
    st.divider()

    # Show config warnings
    config_errors = Config.validate()
    if config_errors:
        for err in config_errors:
            st.warning(f"⚠️ {err}")

    # Init pipeline in session
    if "pipeline" not in st.session_state:
        st.session_state.pipeline = FaceTracePipeline()
    pipeline = st.session_state.pipeline

    # ── Step 1: Upload ──────────────────────────────────────────────────
    st.header("Step 1 · Upload Face Image")
    uploaded = st.file_uploader(
        "Choose a face image (JPG / PNG / WebP)",
        type=["jpg", "jpeg", "png", "webp"],
    )

    if not uploaded:
        st.info("👆 Upload an image to begin.")
        return

    # Save to temp file
    suffix = os.path.splitext(uploaded.name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded.getvalue())
        image_path = tmp.name

    col_img, col_info = st.columns([1, 2])
    with col_img:
        st.image(uploaded, caption="Uploaded Image", width=280)
    with col_info:
        st.write(f"**File:** {uploaded.name}")
        st.write(f"**Size:** {len(uploaded.getvalue()) / 1024:.1f} KB")

    # ── Step 2: Consent ─────────────────────────────────────────────────
    st.header("Step 2 · Consent Confirmation")
    st.warning(
        "⚠️ **CONSENT REQUIRED** — This tool performs reverse image search "
        "on the public web. Only proceed if:\n"
        "- This is **your own face** (selfie) or a photo you own the rights to.\n"
        "- You have **explicit consent** from the person in the photo.\n"
        "- You are comfortable with this image being searched on public websites.\n\n"
        "Do **NOT** use photos of other people without their consent."
    )
    consent = st.checkbox(
        "✅ I confirm this is my own face / I have consent to run this search"
    )
    if not consent:
        st.stop()

    st.success("Consent confirmed ✓")

    # ── Step 3: Face Detection & Encoding ───────────────────────────────
    st.header("Step 3 · Face Detection & Encoding")

    if st.button("🔍 Detect & Encode Face", type="primary"):
        with st.spinner("Detecting face and generating embedding…"):
            try:
                detection = pipeline.step1_validate_and_detect(image_path)
                st.session_state.face_done = True
                st.session_state.image_path = image_path
                st.success(
                    f"✅ Face detected — {detection['faces_detected']} face(s) found"
                )

                encoding = pipeline.step2_encode_face(image_path)
                st.success(
                    f"✅ Embedding generated — "
                    f"{encoding['embedding_size']}D vector (model: {encoding['model']})"
                )
            except Exception as e:
                st.error(f"❌ {e}")
                st.session_state.face_done = False

    if not st.session_state.get("face_done"):
        return

    # ── Step 4: Reverse Image Search ────────────────────────────────────
    st.header("Step 4 · Web / Social Media Search")

    # Allow key from sidebar or .env
    with st.sidebar:
        st.header("⚙️ Configuration")
        user_serp_key = st.text_input(
            "SerpAPI Key (optional if in .env)",
            value=Config.SERPAPI_KEY,
            type="password",
            help="Get your free key from https://serpapi.com"
        )
        if user_serp_key:
            Config.SERPAPI_KEY = user_serp_key

        rpc_input = st.text_input(
            "Blockchain RPC URL",
            value=Config.BLOCKCHAIN_RPC_URL,
            help="Default: http://127.0.0.1:8545 (Hardhat node)"
        )
        if rpc_input:
            Config.BLOCKCHAIN_RPC_URL = rpc_input

    active_api_key = user_serp_key or Config.SERPAPI_KEY
    if not active_api_key:
        st.error(
            "❌ `SERPAPI_KEY` is required. Enter it in the sidebar on the left or add it to your `.env` file.\n"
            "Get a free key (100 searches/month) at: https://serpapi.com/"
        )
        st.stop()

    if st.button("🌐 Search Web for Matching Posts", type="primary"):
        with st.spinner("Uploading image & querying Google Lens (10-30 s)…"):
            try:
                Config.SERPAPI_KEY = active_api_key
                results = pipeline.step3_search(st.session_state.image_path)
                st.session_state.search_done = True
                st.session_state.search_results = results
                st.success(f"✅ Found {len(results)} result(s)!")
            except Exception as e:
                st.error(f"❌ Search failed: {e}")


    if not st.session_state.get("search_done"):
        return

    # Show results
    st.subheader("Search Results")
    for i, r in enumerate(st.session_state.search_results[:8]):
        with st.expander(f"Result #{i+1} — {r.platform}: {r.title[:60] or r.url[:60]}"):
            st.write(f"**Platform:** {r.platform}")
            st.write(f"**URL:** [{r.url}]({r.url})")
            st.write(f"**Title:** {r.title}")
            st.write(f"**Source:** {r.source}")
            st.write(f"**Search Provider:** {r.search_provider}")
            if r.thumbnail_url:
                try:
                    st.image(r.thumbnail_url, width=200)
                except Exception:
                    pass

    # ── Step 5: Face Matching ───────────────────────────────────────────
    st.header("Step 5 · Face Matching Against Candidates")

    if st.button("🎯 Match Faces", type="primary"):
        with st.spinner("Downloading candidate images & comparing faces…"):
            try:
                matches = pipeline.step4_match_candidates(
                    st.session_state.image_path,
                    st.session_state.search_results,
                )
                st.session_state.matches = matches
                st.session_state.match_done = True

                if matches:
                    best = matches[0]
                    sim = best["comparison"].get("similarity_percent", 0)
                    st.success(f"✅ Best match — {sim:.1f}% similarity ({best['search_result'].platform})")
                else:
                    st.warning("⚠️ Face matching was inconclusive or candidate images did not contain detectable faces. Using top discovered post for fingerprinting.")
                    top_result = st.session_state.search_results[0]
                    st.session_state.matches = [{
                        "search_result": top_result,
                        "comparison": {"similarity_percent": 0.0, "verified": False, "image_data": top_result.url.encode("utf-8")},
                        "rank": 1
                    }]
            except Exception as e:
                st.error(f"❌ Matching failed: {e}")

    if not st.session_state.get("match_done"):
        return


    if st.session_state.get("matches"):
        st.subheader("Match Results (ranked by similarity)")
        for m in st.session_state.matches[:5]:
            sr = m["search_result"]
            comp = m["comparison"]
            sim = comp.get("similarity_percent", 0)
            icon = "✅" if comp.get("verified") else "➖"
            st.markdown(
                f"**Candidate #{m['rank']}** · {sr.platform} · "
                f"Similarity: **{sim:.1f}%** {icon}"
            )
            st.caption(f"URL: {sr.url}")
            if "error" in comp and comp["error"]:
                st.caption(f"Note: {comp['error']}")
            st.divider()

    # ── Step 6: Fingerprint + Blockchain ────────────────────────────────
    st.header("Step 6 · SHA-256 Fingerprint & Blockchain Record")

    best_match = st.session_state.matches[0] if st.session_state.get("matches") else None
    if not best_match:
        st.warning("No match available to fingerprint.")
        return

    if st.button("⛓️ Create Fingerprint & Write to Blockchain", type="primary"):
        with st.spinner("Hashing data and submitting blockchain transaction…"):
            try:
                # Fingerprint
                fingerprint = pipeline.step5_create_fingerprint(best_match)
                st.success("✅ SHA-256 fingerprint created")
                st.code(
                    f"Data Hash (SHA-256):  {fingerprint['data_hash']}\n"
                    f"Image Hash (SHA-256): {fingerprint['image_hash']}\n"
                    f"Timestamp:            {fingerprint['discovery_timestamp']}",
                    language="text",
                )

                # Blockchain
                platform = best_match["search_result"].platform
                vid, tx = pipeline.step6_blockchain_register(fingerprint, platform)

                st.success("✅ Hash recorded on blockchain!")
                st.code(
                    f"Transaction Hash: 0x{tx['tx_hash']}\n"
                    f"Block Number:     {tx['block_number']}\n"
                    f"Gas Used:         {tx['gas_used']}\n"
                    f"Status:           {tx['status']}\n"
                    f"Contract:         {tx['contract_address']}\n"
                    f"Verification ID:  {vid}",
                    language="text",
                )

                st.session_state.fingerprint = fingerprint
                st.session_state.verification_id = vid
                st.session_state.image_data = best_match["comparison"].get(
                    "image_data", b""
                )
                st.session_state.blockchain_done = True

            except Exception as e:
                st.error(f"❌ Blockchain error: {e}")
                import traceback
                st.code(traceback.format_exc())

    if not st.session_state.get("blockchain_done"):
        return

    # ── Step 7: On-Chain Verification ───────────────────────────────────
    st.header("Step 7 · On-Chain Re-Verification")

    if st.button("🔐 Verify Against Blockchain", type="primary"):
        with st.spinner("Re-computing hash and querying blockchain…"):
            try:
                image_data = st.session_state.image_data
                if not image_data:
                    image_data = (
                        st.session_state.fingerprint["post_url"].encode("utf-8")
                    )

                verification = pipeline.step7_verify(
                    st.session_state.verification_id,
                    st.session_state.fingerprint,
                    image_data,
                )

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("On-chain hash", verification["on_chain_hash"][:20] + "…")
                    st.code(verification["on_chain_hash"], language="text")
                with col2:
                    st.metric("Recomputed hash", verification["recomputed_hash"][:20] + "…")
                    st.code(verification["recomputed_hash"], language="text")

                if verification["verified"]:
                    st.success(
                        "## ✅ BLOCKCHAIN VERIFIED\n"
                        "The on-chain hash matches the recomputed hash. "
                        "Data integrity is confirmed — the discovered post data "
                        "has not been tampered with."
                    )
                else:
                    st.error(
                        "## ❌ VERIFICATION FAILED\n"
                        "The hashes do **not** match. The discovered data may "
                        "have been modified since the original record was created."
                    )

            except Exception as e:
                st.error(f"❌ Verification error: {e}")

    # ── Footer ──────────────────────────────────────────────────────────
    st.divider()
    st.caption(
        "FaceTrace · HH Goa 2026 · "
        "Only SHA-256 hashes are stored on-chain — never raw images, "
        "post text, or personal metadata."
    )


if __name__ == "__main__":
    main()
