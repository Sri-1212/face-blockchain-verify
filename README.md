# HH Goa 2026 Task 3: Face Identification & Blockchain Verification

A cybersecurity and cryptographic verification pipeline that pairs AI-powered facial feature identification with publicly indexed web discovery and tamper-evident, privacy-preserving blockchain record verification.

---

## Stages & Architecture Overview

```text
BROWSER (Web UI)
  │
  │  POST /api/verify (multipart/form-data)
  ▼
FLASK BACKEND (src/app.py)
  │
  ├─► Stage 1: Face Identification (DeepFace / Facenet 128-d Embedding)
  │
  ├─► Stage 2: Web & Social Search (ImgBB Temporary Upload + SerpApi Google Lens)
  │            └─► Deterministic Social Profile Matching (Instagram, X, LinkedIn, FB, etc.)
  │
  └─► Stage 3: SHA-256 Canonical Hashing + Blockchain Commitment (chain.json)
               ├─► Cryptographic Re-fetch & Hash Comparison
               └─► End-to-End Chain Ledger Audit
  │
  ▼
JSON Response & Interactive Theme-Aware UI (http://localhost:5000)
```

- **Stage 1: Face Identification** — DeepFace & Facenet 128-dimensional embedding extraction (`src/face_module.py`).
- **Stage 2: Web & Social Media Search** — ImgBB temporary image hosting & SerpApi Google Lens reverse image discovery (`src/search_module.py`).
- **Stage 3: Blockchain Verification** — Canonical JSON serialization, SHA-256 record hashing, append-only simulated hash chain (`chain.json`), and cryptographic audit (`src/blockchain_module.py`).
- **Web UI & API Server** — Flask application serving an interactive theme-aware Web UI with animated 3-stage pipeline progress and verification dashboard (`src/app.py` & `src/static/`).

---

## Project Structure

```text
face-blockchain-verify/
├── chain.json                # Persisted immutable simulated blockchain ledger
├── requirements.txt          # Python dependencies (DeepFace, Flask, etc.)
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules for virtualenvs, cache, and secrets
├── README.md                 # Full project documentation
├── test_images/              # Test sample photographs
│   ├── my_public_photo.jpg   # Sample image with public web matches
│   ├── no_face.jpg           # Negative test case (non-face image)
│   └── ...
└── src/
    ├── __init__.py           # Package exports
    ├── face_module.py        # Stage 1: Face detection & Facenet vector extraction
    ├── search_module.py      # Stage 2: ImgBB upload & SerpApi Google Lens search
    ├── blockchain_module.py  # Stage 3: SHA-256 hashing, SimulatedChain, & verification
    ├── main.py               # Full pipeline CLI orchestrator
    ├── app.py                # Flask Web Backend & API routes
    └── static/               # Vanilla Web UI (No build steps / frameworks needed)
        ├── index.html        # Modern semantic HTML5 interface
        ├── style.css         # Dark cyberpunk / Web3 responsive styling
        └── app.js            # Reactive drag-and-drop, pipeline animation & API client
```

---

## Prerequisites & Installation

### 1. Python Environment
Python **3.10** or **3.11** is recommended.

### 2. Virtual Environment Setup

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables (`.env`)

Create a `.env` file in the project root:

```ini
# SerpApi Key: https://serpapi.com/manage-api-key
SERPAPI_KEY=your_serpapi_key_here

# ImgBB Key: https://api.imgbb.com/
IMGBB_API_KEY=your_imgbb_key_here
```

---

## Running the Application

### Option A: Interactive Web UI (Recommended)

Start the Flask server:

```bash
# Standard Python
python src/app.py

# Windows Virtual Environment
.\venv\Scripts\python.exe src\app.py
```

Then open your browser to:
**[http://localhost:5000](http://localhost:5000)**

#### Web UI Highlights:
- **Zero Build Tooling:** Pure HTML5, CSS3, and modern Vanilla JS (no Node/Vite/Tailwind build steps required).
- **Drag-and-Drop Uploader:** Supports JPG, PNG, and WEBP with instantaneous preview and file validation.
- **1-Click Demo Buttons:** Quick-load buttons for `my_public_photo.jpg` (verified discovery) and `no_face.jpg` (error handling).
- **Real-Time Pipeline Stages:** Visual 3-step progress animation with rotating status indicators.
- **Audited Results Dashboard:** Displays face dimensions, web/social match counts, best matched profile with clickable link, block number, and block hash.
- **1-Click Copy:** Copy full 64-character SHA-256 record hash directly to clipboard with visual confirmation.
- **Reset State:** "Verify Another Image" resets UI cleanly without full page reloads.

---

### Option B: Full Pipeline via CLI

Run the full end-to-end pipeline directly in the terminal:

```bash
# Windows
.\venv\Scripts\python.exe src\main.py test_images\my_public_photo.jpg

# Linux / macOS
python src/main.py test_images/my_public_photo.jpg
```

#### Individual Module Testing via CLI:

- **Stage 1 Only (Face ID):**
  ```bash
  python src/face_module.py test_images/my_public_photo.jpg
  ```
- **Stage 2 Only (Web Search):**
  ```bash
  python src/search_module.py test_images/my_public_photo.jpg
  ```
- **Stage 3 Only (Blockchain Standalone & Tamper Audit):**
  ```bash
  python src/blockchain_module.py
  ```

---

## Technical Guarantees & Privacy Design

1. **Privacy-Preserving Biometric Hashing:**
   - The raw 128-dimensional facial embedding vector is **never stored in plaintext** on the blockchain or exposed to the client.
   - Only the deterministic SHA-256 hash of the normalized embedding is committed to the verification record.
2. **Immutable Hash Chain (`chain.json`):**
   - Each committed block contains the canonical SHA-256 data hash, timestamp, previous block hash, and computed block header hash.
   - Any retrospective modification to committed records immediately invalidates subsequent block hashes and is caught during ledger audit.
3. **Temporary Public Hosting for Visual Search:**
   - ImgBB is utilized solely for temporary image hosting with auto-expiration (10 minutes) to provide a publicly accessible URL for SerpApi Google Lens queries.
4. **Verification Disclaimer:**
   - Reverse image search provides visual matches across publicly indexed web and social profiles.
   - Blockchain verification confirms that the discovered post metadata (platform, title, link, source) and face hash match the exact data committed to the immutable ledger.
   - The blockchain provides tamper-evident auditability for recorded discovery data; **it does not establish real-world legal identity from visual similarity alone.**
