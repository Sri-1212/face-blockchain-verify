# HH Goa 2026 Task 3: Face Identification & Blockchain Verification

## Stages Overview
- **Stage 1: Face Identification** — DeepFace & Facenet embedding extraction (`src/face_module.py`).
- **Stage 2: Web & Social Media Search** — ImgBB image hosting & SerpApi Google Lens reverse image search (`src/search_module.py`).
- **Stage 3: Blockchain Verification** — Smart contract interaction & on-chain record lookup (`src/blockchain_module.py`).

---

## Project Structure

```text
face-blockchain-verify/
├── src/
│   ├── __init__.py           # Package initialization
│   ├── face_module.py        # Stage 1: Face detection and Facenet embedding extraction
│   ├── search_module.py      # Stage 2: ImgBB upload & SerpApi Google Lens reverse search
│   ├── blockchain_module.py  # Stage 3: Blockchain verification (Upcoming)
│   └── main.py               # Main CLI pipeline entry point (Upcoming)
├── test_images/              # Directory to store test sample images (.jpg, .png)
│   └── .gitkeep
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules for Python, cache, and secrets
├── requirements.txt          # Python dependencies
└── README.md                 # Project documentation
```


---

## Prerequisites & Installation

### 1. Python Environment
Python 3.10 or 3.11 is recommended.

### 2. Create and Activate Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
Install the required packages listed in `requirements.txt`:
```bash
pip install -r requirements.txt
```

---

## Usage

### Run Face Identification on an Image

1. Place your target image in the `test_images/` folder (or reference any local image path).
2. Run `face_module.py`:

```bash
python src/face_module.py test_images/your_photo.jpg
```

### Optional Arguments

You can specify a different DeepFace model (default is `Facenet`):
```bash
python src/face_module.py test_images/your_photo.jpg --model Facenet
```

### Run Stage 2: Web / Social Media Search
```bash
python src/search_module.py test_images/my_public_photo.jpg
```

---

## Expected Output

### Stage 1: Face Identification
```text
============================================================
 HH Goa 2026 - Stage 1: Face Identification 
============================================================
[INFO] Loading image from: 'test_images/your_photo.jpg'...
[INFO] Using DeepFace model: 'Facenet'...
[SUCCESS] Face detected successfully!
[SUCCESS] Generated embedding vector with dimension: 128
============================================================
[RESULT] Process completed successfully.
[RESULT] Embedding Dimension (Vector Length): 128
[RESULT] Sample Vector Values (first 5 values): [-0.0412, 0.0891, -0.0123, 0.1420, -0.0519]...
============================================================
```

### Stage 2: Web & Social Media Search
```text
======================================================================
 HH Goa 2026 - Stage 2: Web / Social Media Search 
======================================================================
[INFO] Uploading 'test_images/my_public_photo.jpg' temporarily to ImgBB...
[SUCCESS] Image uploaded successfully to ImgBB.
[INFO] Public Image URL: https://i.ibb.co/nMv1YCrH/my-public-photo.png
[INFO] Querying SerpApi Google Lens engine for visual matches...
[SUCCESS] Google Lens search completed successfully.
[SUCCESS] Extracted 60 total visual matches from Google Lens.
[SUCCESS] Found 16 social media match(es).
======================================================================
[RESULT] Overall Status: SUCCESS
[RESULT] Target Image: test_images/my_public_photo.jpg
[RESULT] Hosted Image URL: https://i.ibb.co/nMv1YCrH/my-public-photo.png
[RESULT] Total Visual Matches: 60
[RESULT] Social Media Matches: 16
----------------------------------------------------------------------
[RESULT] BEST SOCIAL MEDIA MATCH:
  * Platform : Instagram
  * Title    : Hair has been listening to me a lil!! Love this top from ...
  * Link     : https://www.instagram.com/p/DcI8m8Ak7Ad/
  * Source   : Instagram
  * Position : #1
----------------------------------------------------------------------
```


---

## Notes & Troubleshooting
- **First Run Download:** When executing for the first time, DeepFace will automatically download the pre-trained `Facenet` model weights (~90MB) into `~/.deepface/weights/`.
- **Facenet Dimensions:** The standard `Facenet` model produces a **128-dimensional** embedding vector representing unique facial features.
