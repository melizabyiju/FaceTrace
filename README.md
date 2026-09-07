# FaceTrace 🔍

**Face Identification & Blockchain Verification Pipeline**

> HH Goa 2026 — Task 3

---

## Overview

FaceTrace is a consent-based identity verification pipeline that:

1. **Detects and encodes** a face from an input image using deep learning.
2. **Searches the web** using genuine reverse image search (Google Lens via SerpAPI) to find matching public social media posts or web pages.
3. **Creates a cryptographic fingerprint** (SHA-256) of the discovered data.
4. **Writes only the hash** to a blockchain — never raw images, text, or personal metadata.
5. **Re-verifies** by recomputing the hash and comparing it against the on-chain record.

```
Face Image
    ↓
Face Detection (DeepFace + OpenCV)
    ↓
Face Embedding (128-2622D vector)
    ↓
Reverse Image Search (Google Lens via SerpAPI)
    ↓
Candidate Posts / Pages
    ↓
Face Similarity Comparison
    ↓
Best Matching Post
    ↓
SHA-256 Fingerprint (of URL + image hash + timestamp)
    ↓
Blockchain Registry (hash only — no PII on-chain)
    ↓
On-chain Retrieval
    ↓
Hash Comparison
    ↓
✅ VERIFIED / ❌ MISMATCH
```

---

## ⚠️ Consent & Privacy

### Consent Requirement (Non-Negotiable)

- This pipeline **must only be run on a face image the user explicitly consents to submit** — a selfie or a photo they own the rights to.
- **Do NOT** use photos of other people, images scraped from someone else's account, or any face without clear consent.
- The code includes an **explicit confirmation step** (CLI prompt or Streamlit checkbox) before any search is executed.

### Privacy by Design

- **Only a SHA-256 hash** is written to the blockchain — never the face image, post text, or any directly identifying metadata.
- Blockchain data is **effectively permanent and immutable**. This is precisely why raw personal data is excluded from on-chain storage.
- The hash acts as a tamper-evident fingerprint: it can prove data integrity without revealing the underlying data.

### Ethical Considerations

- Face recognition is **probabilistic** — similarity scores are algorithmic estimates, not absolute identity proof.
- Results should be treated as **matching evidence**, not certainty.
- This tool is designed for self-verification only, not for surveillance or identifying unconsenting third parties.

---

## Tech Stack

| Component             | Technology                          |
|-----------------------|-------------------------------------|
| Language              | Python 3.10+                        |
| Face Recognition      | DeepFace (VGG-Face model) + OpenCV  |
| Reverse Image Search  | SerpAPI (Google Lens engine)        |
| Blockchain            | Local Hardhat Node (EVM-compatible) |
| Smart Contract        | Solidity 0.8.19                     |
| Blockchain Client     | web3.py + py-solc-x                 |
| Hashing               | SHA-256 (hashlib)                   |
| UI                    | Streamlit (or CLI)                  |

---

## Features

- ✅ Face detection and encoding with DeepFace
- ✅ Genuine reverse image search via Google Lens (SerpAPI) — not hardcoded
- ✅ Face similarity comparison between input and candidates
- ✅ Deterministic SHA-256 fingerprinting
- ✅ Smart contract deployment and hash registration on-chain
- ✅ On-chain re-verification with clear VERIFIED / MISMATCH output
- ✅ Explicit consent confirmation before search
- ✅ Both Streamlit UI and CLI interfaces
- ✅ No raw personal data ever written on-chain

---

## Installation

### Prerequisites

- **Python 3.10+**
- **Node.js 18+** (for Hardhat local blockchain)
- **Git**

### Setup

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/facetrace.git
cd facetrace

# Create a virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
# source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install Hardhat (local blockchain)
npm install
```

### Configure Environment

```bash
# Copy the example environment file
copy .env.example .env        # Windows
# cp .env.example .env        # macOS/Linux
```

Edit `.env` and set your API keys:

```env
# REQUIRED: Get free key at https://serpapi.com/ (100 searches/month free)
SERPAPI_KEY=your_serpapi_key_here

# The other defaults work for local Hardhat — no changes needed
```

### Required Environment Variables

| Variable              | Required | Default                                    | Description                              |
|-----------------------|----------|--------------------------------------------|------------------------------------------|
| `SERPAPI_KEY`         | ✅ Yes   | —                                          | SerpAPI key for Google Lens search       |
| `BLOCKCHAIN_RPC_URL`  | No       | `http://127.0.0.1:8545`                    | RPC endpoint for blockchain              |
| `PRIVATE_KEY`         | No       | Hardhat account #0 key                     | Wallet private key (never use on mainnet!)|
| `CONTRACT_ADDRESS`    | No       | Auto-deployed                              | Pre-deployed contract address            |
| `CHAIN_ID`            | No       | `31337`                                    | Network chain ID                         |
| `FACE_MODEL`          | No       | `VGG-Face`                                 | DeepFace recognition model               |
| `FACE_DETECTOR`       | No       | `opencv`                                   | Face detector backend                    |
| `IMGBB_API_KEY`       | No       | —                                          | Optional: ImgBB for image hosting        |

---

## Blockchain Setup

### Blockchain Used: Local Hardhat Node

We use a **local Hardhat Ethereum node** (EVM-compatible) for the following reasons:

- **Free**: No testnet ETH, no gas costs, no faucet delays
- **Reliable**: Runs locally, always available, instant confirmations
- **Real EVM**: Executes actual Solidity bytecode — real transactions, real block hashes
- **Easy to demo**: Visible in terminal, shows transaction details

### Starting the Blockchain Node

Open a **separate terminal** and run:

```bash
npx hardhat node
```

This starts a local Ethereum node on `http://127.0.0.1:8545` with 20 pre-funded accounts.

> **Note:** Keep this terminal open while running the pipeline. The blockchain state resets when the node is stopped.

### Smart Contract

The `VerificationRegistry` contract ([contracts/VerificationRegistry.sol](contracts/VerificationRegistry.sol)) stores:

- `bytes32 dataHash` — SHA-256 fingerprint of the discovered data
- `string source` — Platform name (e.g., "Instagram")
- `uint256 timestamp` — Block timestamp
- `address submitter` — Transaction sender

**No raw images, post text, or personal metadata are stored on-chain.**

The contract is automatically compiled and deployed when the pipeline first runs. You can also deploy separately:

```bash
python scripts/deploy_contract.py
```

---

## Running

### Option A: Streamlit UI (Recommended for Demo)

```bash
# Terminal 1: Start blockchain
npx hardhat node

# Terminal 2: Start app
streamlit run app/main.py
```

Then open `http://localhost:8501` in your browser.

### Option B: CLI

```bash
# Terminal 1: Start blockchain
npx hardhat node

# Terminal 2: Run pipeline
python scripts/run_pipeline.py path/to/your/face/image.jpg
```

---

## How the Pipeline Works

### Step 1 — Face Detection
The input image is validated and faces are detected using DeepFace with the OpenCV backend. The system rejects images with no faces.

### Step 2 — Face Encoding
A numerical embedding vector (128–2622 dimensions depending on the model) is generated for the detected face, which captures facial features in a way suitable for comparison.

### Step 3 — Reverse Image Search
The image is uploaded to a temporary hosting service and searched via Google Lens using SerpAPI. This is a **genuine runtime search** — not a hardcoded or cached result. The search returns candidate web pages/social media posts containing visually similar images.

### Step 4 — Face Matching
For each candidate result with an available image, the system:
1. Downloads the candidate image
2. Detects faces in it
3. Generates a face embedding
4. Compares it with the input face embedding
5. Ranks candidates by similarity percentage

### Step 5 — SHA-256 Fingerprint
A deterministic fingerprint is computed:
```
SHA-256( post_url + "|" + SHA-256(image_bytes) + "|" + discovery_timestamp )
```
This ensures the same inputs always produce the same hash.

### Step 6 — Blockchain Record
The hash is submitted to the VerificationRegistry smart contract via a blockchain transaction. Only the `bytes32` hash, platform name, and block timestamp are stored on-chain.

### Step 7 — Re-Verification
The system re-downloads the data, recomputes the SHA-256 hash, retrieves the on-chain hash, and compares them:
- **VERIFIED ✅** — Hashes match, data integrity confirmed
- **MISMATCH ❌** — Hashes differ, data may have been tampered with

---

## Demo Instructions (Screen Recording)

Follow this sequence for a clean ~60-second recording:

1. **Start Hardhat node** in Terminal 1: `npx hardhat node`
2. **Start Streamlit** in Terminal 2: `streamlit run app/main.py`
3. **Upload** your own face photo (selfie)
4. **Check consent** checkbox
5. **Click** "Detect & Encode Face" → show ✅ Face detected
6. **Click** "Search Web" → show search results appearing
7. **Click** "Match Faces" → show similarity scores
8. **Click** "Create Fingerprint & Write to Blockchain" → show hash + transaction
9. **Click** "Verify Against Blockchain" → show ✅ VERIFIED
10. **Done** — scroll to show the full pipeline completed

---

## Testing

```bash
# Run hash tests (no external deps needed)
pytest tests/test_hash.py -v

# Run face validation tests
pytest tests/test_face.py -v

# Run blockchain tests (requires Hardhat node running)
pytest tests/test_blockchain.py -v

# Run all tests
pytest tests/ -v
```

---

## Known Limitations

### Reverse Image Search
- **SerpAPI Google Lens** requires an API key (free tier: 100 searches/month)
- Search results depend on what Google has indexed — a photo not present on any public website will return no matches
- Results may include false positives (visually similar but different people)

### Face Recognition
- **DeepFace** accuracy varies with image quality, lighting, angle, and occlusion
- Similarity scores are probabilistic — a high score does not guarantee identity
- The default VGG-Face model may produce different results than Facenet or ArcFace

### Image Upload
- Local images must be uploaded to a temporary hosting service to generate a URL for Google Lens
- Upload services (freeimage.host, 0x0.st) may have rate limits or downtime

### Blockchain
- **Local Hardhat node** state resets when stopped — not persistent across restarts
- For production use, deploy to a public testnet (Sepolia) or mainnet
- Gas costs apply on public networks

### Privacy
- Uploaded images are temporarily hosted on third-party services during search
- Search queries are processed by SerpAPI/Google
- Face embeddings are computed locally and not stored permanently

---

## Project Structure

```
facetrace/
├── app/
│   ├── __init__.py
│   ├── config.py          # Environment configuration
│   ├── pipeline.py        # Pipeline orchestration
│   └── main.py            # Streamlit UI
├── face/
│   ├── __init__.py
│   ├── detector.py        # Face detection (DeepFace)
│   ├── encoder.py         # Face embedding generation
│   └── matcher.py         # Face comparison & candidate matching
├── search/
│   ├── __init__.py
│   ├── base.py            # SearchProvider abstract base
│   ├── models.py          # SearchResult dataclass
│   ├── serpapi_provider.py # SerpAPI Google Lens provider
│   └── image_upload.py    # Temp image hosting helpers
├── hashing/
│   ├── __init__.py
│   └── fingerprint.py     # SHA-256 fingerprinting
├── blockchain/
│   ├── __init__.py
│   ├── client.py          # Web3 blockchain client
│   ├── verifier.py        # On-chain verification
│   └── contract_data.py   # Pre-compiled contract ABI
├── contracts/
│   └── VerificationRegistry.sol  # Solidity smart contract
├── scripts/
│   ├── deploy_contract.py # Standalone contract deployer
│   └── run_pipeline.py    # CLI pipeline runner
├── tests/
│   ├── test_hash.py       # Hashing unit tests
│   ├── test_face.py       # Face validation tests
│   └── test_blockchain.py # Blockchain integration tests
├── data/                  # Place input images here
├── .env.example           # Environment template
├── .gitignore
├── requirements.txt
├── package.json           # Hardhat dependency
├── hardhat.config.js      # Hardhat configuration
├── LICENSE
└── README.md
```

---

## License

MIT License — see [LICENSE](LICENSE) for details.
