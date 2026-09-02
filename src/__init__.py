"""
HH Goa 2026 Task 3: Face Identification & Blockchain Verification
"""

from .face_module import extract_face_embedding
from .search_module import search_image, upload_image_to_imgbb, search_google_lens, find_best_social_match
from .blockchain_module import (
    create_verification_record,
    calculate_canonical_hash,
    hash_face_embedding,
    commit_record,
    verify_record,
    SimulatedChain,
    Block,
)

__all__ = [
    "extract_face_embedding",
    "search_image",
    "upload_image_to_imgbb",
    "search_google_lens",
    "find_best_social_match",
    "create_verification_record",
    "calculate_canonical_hash",
    "hash_face_embedding",
    "commit_record",
    "verify_record",
    "SimulatedChain",
    "Block",
]

