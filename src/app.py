"""
HH Goa 2026 Task 3: Face Identification & Blockchain Verification
Flask Web Application Backend

Architecture:
Browser
  |
  | POST /api/verify (multipart/form-data)
  v
Flask Backend (src/app.py)
  |
  +--> Stage 1: src.face_module.extract_face_embedding
  |
  +--> Stage 2: src.search_module.search_image
  |
  +--> Stage 3: src.blockchain_module (create_verification_record, commit_record, verify_record)
  |
  v
JSON Response + Tamper-Evident Verification Proof
"""

import os
import sys
import uuid
import logging
import tempfile
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from dotenv import load_dotenv

# Ensure project root is in Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load environment variables
load_dotenv(override=False)

# Import existing pipeline modules without modifying core logic
from src.face_module import extract_face_embedding
from src.search_module import search_image, validate_image
from src.blockchain_module import (
    create_verification_record,
    calculate_canonical_hash,
    commit_record,
    verify_record,
    SimulatedChain,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("face_blockchain_app")

# Initialize Flask App
STATIC_DIR = Path(__file__).resolve().parent / "static"
TEST_IMAGES_DIR = PROJECT_ROOT / "test_images"
CHAIN_PATH = str(PROJECT_ROOT / "chain.json")

app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="")
CORS(app)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH


def is_allowed_file(filename: str) -> bool:
    """Checks if the uploaded file has a valid image extension."""
    suffix = Path(filename).suffix.lower()
    return suffix in ALLOWED_EXTENSIONS


@app.route("/", methods=["GET"])
def serve_index():
    """Serves the main single-page web UI."""
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint to verify backend service status."""
    return jsonify({
        "status": "healthy",
        "service": "Face Identification & Blockchain Verification",
        "protocol": "HH_GOA_2026_TASK3",
        "blockchain_mode": "simulated"
    }), 200


@app.route("/api/sample-images", methods=["GET"])
def get_sample_images():
    """Returns available sample test images for 1-click testing in the UI."""
    samples = []
    if TEST_IMAGES_DIR.exists():
        for file in sorted(TEST_IMAGES_DIR.iterdir()):
            if file.is_file() and file.suffix.lower() in ALLOWED_EXTENSIONS:
                samples.append({
                    "filename": file.name,
                    "size_bytes": file.stat().st_size,
                    "url": f"/api/sample-images/{file.name}",
                    "is_demo_photo": file.name == "my_public_photo.jpg",
                    "is_no_face": file.name == "no_face.jpg"
                })
    return jsonify({"samples": samples}), 200


@app.route("/api/sample-images/<filename>", methods=["GET"])
def serve_sample_image(filename: str):
    """Serves a specific sample image file."""
    safe_path = TEST_IMAGES_DIR / Path(filename).name
    if not safe_path.exists() or not safe_path.is_file():
        return jsonify({"error": "Sample image not found"}), 404
    return send_file(str(safe_path))


@app.route("/api/verify", methods=["POST"])
def verify_image_pipeline():
    """
    Executes the 3-stage Face Identification & Blockchain Verification pipeline.
    Accepts: multipart/form-data with 'image' file.
    """
    # 1. Validate request payload
    if "image" not in request.files:
        return jsonify({
            "success": False,
            "stage": "upload",
            "message": "No image file provided in request. Please upload an image with key 'image'."
        }), 400

    file = request.files["image"]

    if not file or file.filename.strip() == "":
        return jsonify({
            "success": False,
            "stage": "upload",
            "message": "Empty file received. Please select a valid image file."
        }), 400

    original_filename = file.filename
    ext = Path(original_filename).suffix.lower()

    if not is_allowed_file(original_filename):
        return jsonify({
            "success": False,
            "stage": "upload",
            "message": f"Unsupported file type '{ext}'. Allowed types: JPG, PNG, WEBP, BMP."
        }), 400

    # 2. Save to temporary file safely
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    temp_path = temp_file.name

    try:
        file.save(temp_path)
        temp_file.close()

        # Check that file is non-empty
        if os.path.getsize(temp_path) == 0:
            return jsonify({
                "success": False,
                "stage": "upload",
                "message": "Uploaded image file is empty (0 bytes)."
            }), 400

        logger.info(f"Processing uploaded image '{original_filename}' (temp: {temp_path})")

        # ---------------------------------------------------------------------
        # STAGE 1: Face Identification
        # ---------------------------------------------------------------------
        logger.info("[STAGE 1] Extracting face embedding using Facenet...")
        try:
            face_embedding = extract_face_embedding(image_path=temp_path, model_name="Facenet")
        except Exception as face_err:
            logger.error(f"[STAGE 1 ERROR] {face_err}")
            return jsonify({
                "success": False,
                "stage": "face",
                "message": f"Face identification module encountered an error: {str(face_err)}"
            }), 400

        if face_embedding is None or len(face_embedding) == 0:
            logger.warning("[STAGE 1 FAILED] No face detected in uploaded image.")
            return jsonify({
                "success": False,
                "stage": "face",
                "message": "No human face was detected in the uploaded image. Please provide a clear face photo."
            }), 400

        embedding_dim = len(face_embedding)
        logger.info(f"[STAGE 1 SUCCESS] Face detected. Embedding dimension: {embedding_dim}")

        # ---------------------------------------------------------------------
        # STAGE 2: Web / Social Media Search (ImgBB + SerpApi Google Lens)
        # ---------------------------------------------------------------------
        logger.info("[STAGE 2] Executing Web / Social Media Search...")
        try:
            search_result = search_image(image_path=temp_path)
        except Exception as search_err:
            logger.error(f"[STAGE 2 ERROR] {search_err}")
            return jsonify({
                "success": False,
                "stage": "search",
                "message": f"Web search module error: {str(search_err)}"
            }), 502

        if search_result.get("status") == "ERROR":
            err_msg = search_result.get("error_message") or "Reverse image search failed."
            logger.error(f"[STAGE 2 FAILED] {err_msg}")
            return jsonify({
                "success": False,
                "stage": "search",
                "message": err_msg
            }), 502

        best_match = search_result.get("best_social_match")
        all_matches = search_result.get("all_matches", [])
        social_matches = search_result.get("social_matches", [])

        if not best_match or search_result.get("status") == "NO_MATCH":
            logger.warning("[STAGE 2 NO_MATCH] No matching social media profile found.")
            return jsonify({
                "success": False,
                "stage": "search",
                "message": "No matching social-media content was found for this face image.",
                "total_web_matches": len(all_matches)
            }), 404

        title = best_match.get("title", "")
        link = best_match.get("link", "")
        source = best_match.get("source") or best_match.get("platform", "Web")
        platform = best_match.get("platform", "Web")
        thumbnail = best_match.get("thumbnail", "")
        position = best_match.get("position", 1)

        logger.info(f"[STAGE 2 SUCCESS] Best match: [{platform}] {title} -> {link}")

        # ---------------------------------------------------------------------
        # STAGE 3: Blockchain Record Creation, Commitment & Verification
        # ---------------------------------------------------------------------
        logger.info("[STAGE 3] Creating privacy-preserving verification record...")
        try:
            # Privacy guarantee: only the hash of the face embedding is stored
            record = create_verification_record(
                face_embedding=face_embedding,
                social_match=best_match,
                image_path=original_filename  # Use user-facing clean filename
            )
        except Exception as rec_err:
            logger.error(f"[STAGE 3 ERROR] Failed to create record: {rec_err}")
            return jsonify({
                "success": False,
                "stage": "blockchain",
                "message": f"Failed to construct verification record: {str(rec_err)}"
            }), 500

        # Calculate canonical SHA-256 hash of the record
        record_hash = calculate_canonical_hash(record)
        face_hash = record.get("face_embedding_hash", "")

        # Commit record to simulated blockchain
        logger.info("[STAGE 3] Committing record to simulated blockchain...")
        try:
            commit_res = commit_record(record=record, chain_path=CHAIN_PATH)
        except Exception as commit_err:
            logger.error(f"[STAGE 3 ERROR] Failed to commit block: {commit_err}")
            return jsonify({
                "success": False,
                "stage": "blockchain",
                "message": f"Blockchain commitment failed: {str(commit_err)}"
            }), 500

        block_index = commit_res["block_index"]
        block_hash = commit_res["block_hash"]
        timestamp = commit_res.get("timestamp", "")

        # Re-fetch block and verify cryptographic integrity
        logger.info(f"[STAGE 3] Re-verifying committed Block #{block_index}...")
        try:
            chain = SimulatedChain(chain_path=CHAIN_PATH)
            fetched_block = chain.get_block(block_index)
            if not fetched_block:
                raise ValueError(f"Block #{block_index} could not be retrieved from chain.")

            recomputed_hash = calculate_canonical_hash(fetched_block.data)
            hashes_match = (recomputed_hash == fetched_block.data_hash == record_hash)

            verif_result = verify_record(record=record, block_identifier=block_index, chain_path=CHAIN_PATH)
            chain_audit = chain.validate_chain()

            is_verified = (
                verif_result.get("verified", False) and
                hashes_match and
                chain_audit.get("valid", False)
            )
        except Exception as verif_err:
            logger.error(f"[STAGE 3 ERROR] Verification check error: {verif_err}")
            return jsonify({
                "success": False,
                "stage": "blockchain",
                "message": f"Blockchain verification validation failed: {str(verif_err)}"
            }), 500

        if not is_verified:
            logger.error("[STAGE 3 FAILED] Cryptographic hash verification failed.")
            return jsonify({
                "success": False,
                "stage": "blockchain",
                "message": "Record hash mismatch or blockchain integrity violation detected."
            }), 500

        logger.info(f"[SUCCESS] Pipeline complete. Block #{block_index} verified.")

        # ---------------------------------------------------------------------
        # 4. Return Structured Success Response
        # ---------------------------------------------------------------------
        response_payload = {
            "success": True,
            "face": {
                "detected": True,
                "embedding_dim": embedding_dim,
                "model": "Facenet",
                "status_message": "Face detected & 128-dimensional embedding generated successfully."
            },
            "search": {
                "matches_found": len(all_matches),
                "social_matches_found": len(social_matches),
                "image_url": search_result.get("image_url"),
                "best_match": {
                    "platform": platform,
                    "title": title,
                    "link": link,
                    "source": source,
                    "thumbnail": thumbnail,
                    "position": position
                }
            },
            "blockchain": {
                "post_hash": record_hash,
                "face_embedding_hash": face_hash,
                "block_index": block_index,
                "block_hash": block_hash,
                "timestamp": timestamp,
                "verified": True,
                "chain_integrity": True,
                "total_chain_blocks": chain_audit.get("total_blocks", block_index + 1)
            }
        }

        return jsonify(response_payload), 200

    except Exception as unexpected_err:
        logger.error(f"[UNEXPECTED ERROR] {unexpected_err}", exc_info=True)
        return jsonify({
            "success": False,
            "stage": "server",
            "message": "An unexpected server error occurred while processing the request."
        }), 500

    finally:
        # Safe temporary file cleanup: delete file even if an error occurs
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                logger.info(f"Temporary file '{temp_path}' removed cleanly.")
            except Exception as cleanup_err:
                logger.warning(f"Could not remove temp file '{temp_path}': {cleanup_err}")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"Starting Face-Blockchain Verification server on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
