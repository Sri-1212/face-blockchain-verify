"""
HH Goa 2026 Task 3: Face Identification & Blockchain Verification
Full Pipeline Integration Orchestrator (Day 3)

Pipeline Stages:
USER PHOTO
  ↓
Stage 1 — Face Identification (DeepFace / Facenet embedding)
  ↓
Stage 2 — Web / Social Media Reverse-Image Search (ImgBB + SerpApi Google Lens)
  ↓
Best social-media match (Platform, Title, Link, Source)
  ↓
Stage 3 — SHA-256 Canonical Hashing + Simulated Blockchain Commitment (chain.json)
  ↓
Re-fetch committed record & recompute SHA-256 hash
  ↓
Cryptographic Hash & Chain Integrity Verification
  ↓
FINAL VERIFICATION RESULT
"""

import os
import sys
import argparse
from pathlib import Path

# Ensure safe console output for Windows cmd/powershell
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.face_module import extract_face_embedding
from src.search_module import search_image, validate_image, load_api_keys
from src.blockchain_module import (
    create_verification_record,
    calculate_canonical_hash,
    commit_record,
    verify_record,
    SimulatedChain,
)


def _clean_str(text: any) -> str:
    """Safely sanitizes strings for terminal output across any console encoding."""
    if text is None:
        return ""
    text_str = str(text).strip()
    return text_str.encode("ascii", errors="replace").decode("ascii")


def run_pipeline(image_path: str, chain_path: str = "chain.json", verbose: bool = True) -> dict:
    """
    Executes the complete end-to-end verification pipeline:
    Stage 1 -> Stage 2 -> Stage 3 -> Cryptographic Verification.

    Parameters:
        image_path (str): Path to the target face photograph.
        chain_path (str): Persistence file path for simulated blockchain.
        verbose (bool): Whether to print stage-by-stage CLI output.

    Returns:
        dict: Complete structured pipeline result.
    """
    summary = {
        "success": False,
        "image_path": str(image_path),
        "stage1_face_id": "FAILED",
        "stage2_web_search": "FAILED",
        "stage2_social_match": "NOT_FOUND",
        "stage3_blockchain_commit": "FAILED",
        "stage3_hash_verification": "FAILED",
        "stage3_chain_integrity": "INVALID",
        "face_embedding_dim": None,
        "face_embedding_hash": None,
        "best_social_match": None,
        "block_index": None,
        "block_hash": None,
        "record_hash": None,
        "details": "",
    }

    if verbose:
        print("=" * 70)
        print(" HH Goa 2026 - Task 3: Face Identification & Blockchain Verification ")
        print("=" * 70)

    # -------------------------------------------------------------------------
    # 0. Pre-Flight Validation
    # -------------------------------------------------------------------------
    path_obj = Path(image_path)
    if not path_obj.exists() or not path_obj.is_file():
        err_msg = f"Input image file not found: '{image_path}'"
        print(f"\n[ERROR] {err_msg}")
        summary["details"] = err_msg
        return summary

    # -------------------------------------------------------------------------
    # STAGE 1: Face Identification
    # -------------------------------------------------------------------------
    if verbose:
        print("\n[STAGE 1] Face Identification")
    
    face_embedding = extract_face_embedding(image_path=str(path_obj), model_name="Facenet")
    
    if face_embedding is None or len(face_embedding) == 0:
        err_msg = f"Face detection failed for '{image_path}'. No face detected or image could not be processed."
        print(f"\n[PIPELINE STOPPED] Stage 1 failed: {err_msg}")
        print("[INFO] Pipeline halted cleanly. Stages 2 and 3 will not be executed.")
        summary["details"] = err_msg
        return summary

    summary["stage1_face_id"] = "SUCCESS"
    summary["face_embedding_dim"] = len(face_embedding)
    if verbose:
        print(f"[SUCCESS] Face detected.")
        print(f"[SUCCESS] Face embedding generated (dimension: {len(face_embedding)}).")

    # -------------------------------------------------------------------------
    # STAGE 2: Web / Social Media Search
    # -------------------------------------------------------------------------
    if verbose:
        print("\n[STAGE 2] Web / Social Media Search")
    
    search_result = search_image(image_path=str(path_obj))
    
    if search_result.get("status") == "ERROR":
        err_msg = f"Stage 2 search error: {search_result.get('error_message')}"
        print(f"\n[PIPELINE STOPPED] Stage 2 failed: {err_msg}")
        print("[INFO] Pipeline halted cleanly. Stage 3 blockchain commitment will not be executed.")
        summary["details"] = err_msg
        return summary

    summary["stage2_web_search"] = "SUCCESS"
    if verbose and search_result.get("image_url"):
        print("[SUCCESS] Image uploaded temporarily.")
        print("[SUCCESS] Google Lens search completed.")

    best_match = search_result.get("best_social_match")
    
    if not best_match or search_result.get("status") == "NO_MATCH":
        print("\n[STAGE 2] NO SOCIAL MEDIA MATCH FOUND")
        print("[INFO] Visual matches may have been found on general web pages, but no verified social-media profile match exists.")
        print("[INFO] Pipeline halted cleanly. No unverified or fabricated data will be committed to the blockchain.")
        summary["details"] = "No social media match found for image."
        return summary

    # Validate that best_match contains required fields
    title = best_match.get("title")
    link = best_match.get("link")
    source = best_match.get("source") or best_match.get("platform")

    if not title or not link or not source:
        print("\n[STAGE 2] INCOMPLETE SOCIAL MATCH DATA")
        print(f"[ERROR] Discovered social match is missing essential fields: title='{title}', link='{link}', source='{source}'")
        print("[INFO] Pipeline halted cleanly. Incomplete records will not be committed to the blockchain.")
        summary["details"] = "Incomplete social match metadata."
        return summary

    summary["stage2_social_match"] = "FOUND"
    summary["best_social_match"] = best_match
    
    if verbose:
        print("[SUCCESS] Social-media match found.")
        print("\n[STAGE 2] Best Match")
        print(f"Platform : {_clean_str(best_match.get('platform', 'Web'))}")
        print(f"Title    : {_clean_str(title)}")
        print(f"Link     : {_clean_str(link)}")
        print(f"Source   : {_clean_str(source)}")

    # -------------------------------------------------------------------------
    # STAGE 3: SHA-256 + Simulated Blockchain Commitment & Verification
    # -------------------------------------------------------------------------
    if verbose:
        print("\n[STAGE 3] Blockchain Verification")

    # 1. Create Privacy-Preserving Verification Record (Face embedding hash only)
    try:
        record = create_verification_record(
            face_embedding=face_embedding,
            social_match=best_match,
            image_path=str(path_obj)
        )
    except Exception as err:
        err_msg = f"Failed to construct verification record: {err}"
        print(f"[ERROR] {err_msg}")
        summary["details"] = err_msg
        return summary

    record_hash = calculate_canonical_hash(record)
    summary["face_embedding_hash"] = record.get("face_embedding_hash")
    summary["record_hash"] = record_hash
    if verbose:
        print(f"[SUCCESS] SHA-256 hash generated (Record Hash: {record_hash[:16]}...).")

    # 2. Commit to Simulated Blockchain
    try:
        commit_res = commit_record(record=record, chain_path=chain_path)
    except Exception as err:
        err_msg = f"Failed to commit record to blockchain: {err}"
        print(f"[ERROR] {err_msg}")
        summary["details"] = err_msg
        return summary

    block_index = commit_res["block_index"]
    block_hash = commit_res["block_hash"]
    summary["stage3_blockchain_commit"] = "SUCCESS"
    summary["block_index"] = block_index
    summary["block_hash"] = block_hash

    if verbose:
        print(f"[SUCCESS] Hash committed to simulated blockchain at Block #{block_index}.")

    # 3. Re-fetch Committed Record from Chain
    chain = SimulatedChain(chain_path=chain_path)
    fetched_block = chain.get_block(block_index)
    if not fetched_block:
        err_msg = f"Failed to re-fetch Block #{block_index} from blockchain."
        print(f"[ERROR] {err_msg}")
        summary["details"] = err_msg
        return summary

    if verbose:
        print(f"[SUCCESS] Record re-fetched from Block #{block_index}.")

    # 4. Recompute Hash & Compare
    recomputed_hash = calculate_canonical_hash(fetched_block.data)
    hashes_match = (recomputed_hash == fetched_block.data_hash == record_hash)
    
    if verbose:
        print(f"[SUCCESS] Hash recomputed.")
        if hashes_match:
            print(f"[SUCCESS] Hashes match.")
        else:
            print(f"[ERROR] Hash mismatch! Expected '{record_hash}', got '{recomputed_hash}'.")

    # 5. Full End-to-End Cryptographic Verification
    verif_result = verify_record(record=record, block_identifier=block_index, chain_path=chain_path)
    chain_audit = chain.validate_chain()

    if verif_result.get("verified") and hashes_match:
        summary["stage3_hash_verification"] = "VERIFIED"
    else:
        summary["stage3_hash_verification"] = "FAILED"

    if chain_audit.get("valid"):
        summary["stage3_chain_integrity"] = "VALID"
        if verbose:
            print(f"[SUCCESS] Chain integrity valid (Total Blocks: {chain_audit['total_blocks']}).")
    else:
        summary["stage3_chain_integrity"] = "INVALID"
        print(f"[ERROR] Blockchain integrity check failed: {chain_audit.get('errors')}")

    # Determine final pipeline success
    summary["success"] = (
        summary["stage1_face_id"] == "SUCCESS" and
        summary["stage2_web_search"] == "SUCCESS" and
        summary["stage2_social_match"] == "FOUND" and
        summary["stage3_blockchain_commit"] == "SUCCESS" and
        summary["stage3_hash_verification"] == "VERIFIED" and
        summary["stage3_chain_integrity"] == "VALID"
    )

    # -------------------------------------------------------------------------
    # FINAL RESULT & HACKATHON SUMMARY
    # -------------------------------------------------------------------------
    if verbose:
        print("\n" + "=" * 70)
        print(" FINAL RESULT ")
        print("=" * 70)
        print(f" Face Identification : {summary['stage1_face_id']}")
        print(f" Web Search          : {summary['stage2_web_search']}")
        print(f" Social Match        : {summary['stage2_social_match']}")
        print(f" Blockchain Commit   : {summary['stage3_blockchain_commit']} (Block #{summary['block_index']})")
        print(f" Hash Verification   : {summary['stage3_hash_verification']}")
        print(f" Chain Integrity     : {summary['stage3_chain_integrity']}")
        print("=" * 70)

        if summary["success"]:
            print(" TASK 3 RESULT: VERIFIED ")
            print("=" * 70)
            print("\n[VERIFICATION NOTICE & SEMANTIC GUARANTEE]")
            print(" - The reverse-image search provides the visual match across public web/social profiles.")
            print(" - Blockchain verification confirms that the discovered post record (title + link + source)")
            print("   matches the exact canonical data that was committed to the immutable chain.")
            print(" - The blockchain provides tamper-evident auditability of the discovery data;")
            print("   it does NOT claim that visual similarity alone proves a person's physical identity.")
            print("=" * 70)
        else:
            print(" TASK 3 RESULT: FAILED / INCOMPLETE ")
            print("=" * 70)

    return summary


def main():
    """
    CLI Entry point to run the complete Face Identification & Blockchain Verification pipeline.
    Usage: python src/main.py path/to/photo.jpg
    """
    parser = argparse.ArgumentParser(
        description="HH Goa 2026 Task 3: Full End-to-End Pipeline (Face Identification -> Social Search -> Blockchain Verification)."
    )
    parser.add_argument(
        "image",
        nargs="?",
        type=str,
        help="Path to the input photograph (e.g., test_images/my_public_photo.jpg)"
    )
    parser.add_argument(
        "--chain",
        type=str,
        default="chain.json",
        help="Path to the blockchain JSON file (default: chain.json)"
    )

    args = parser.parse_args()

    if not args.image:
        print("[USAGE] Please provide an image path.")
        print("Example: python src/main.py test_images/my_public_photo.jpg")
        print("Run 'python src/main.py --help' for options.")
        sys.exit(1)

    result = run_pipeline(image_path=args.image, chain_path=args.chain, verbose=True)

    if not result["success"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
