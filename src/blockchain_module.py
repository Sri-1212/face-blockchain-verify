"""
HH Goa 2026 Task 3: Face Identification & Blockchain Verification
Stage 3: Blockchain Verification Module (Simulated Hash Chain)

This module handles:
1. Canonical, deterministic serialization and SHA-256 hashing.
2. Privacy-preserving verification record creation (storing ONLY the face embedding hash, never raw embeddings).
3. Append-only, tamper-evident simulated blockchain persisted to `chain.json`.
4. Cryptographic record commitment, block linkage, and chain validation.
5. Tamper detection and verification without third-party dependencies or external networks.

Notice:
The blockchain verifies that the recorded verification data has not changed since commitment.
It does NOT claim that visual similarity alone proves a person's physical identity.
"""

import os
import sys
import json
import time
import hashlib
from dataclasses import dataclass
from pathlib import Path

# Ensure safe console output on Windows platforms
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


def calculate_canonical_hash(data: any) -> str:
    """
    Computes a canonical SHA-256 hash over any JSON-serializable Python data structure.
    Uses sorted keys and compact separators (",", ":") to ensure identical inputs
    ALWAYS generate the exact same cryptographic hash.

    Parameters:
        data: Python dictionary, list, string, or primitive to hash.

    Returns:
        str: 64-character hexadecimal SHA-256 string.
    """
    canonical_json = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical_json).hexdigest()


def hash_face_embedding(face_embedding: list | tuple | str) -> str:
    """
    Hashes the facial embedding vector using canonical serialization.
    Ensures sensitive raw biometric data is never stored in plaintext on-chain.

    Parameters:
        face_embedding: 128-d embedding vector (list of floats) or precomputed hash string.

    Returns:
        str: SHA-256 hex string of the embedding vector.
    """
    if face_embedding is None:
        raise ValueError("Face embedding cannot be None.")

    if isinstance(face_embedding, str):
        # If it is already a 64-char hex string, validate and return lowercase
        if len(face_embedding) == 64 and all(c in "0123456789abcdefABCDEF" for c in face_embedding):
            return face_embedding.lower()
        return calculate_canonical_hash(face_embedding)

    if isinstance(face_embedding, (list, tuple)):
        # Normalize list of float values
        normalized = [float(v) for v in face_embedding]
        return calculate_canonical_hash(normalized)

    raise ValueError(f"Unsupported face embedding type: {type(face_embedding)}")


def create_verification_record(
    face_embedding: list | tuple | str,
    social_match: dict,
    image_path: str
) -> dict:
    """
    Creates a privacy-preserving verification record for on-chain commitment.

    Important Privacy Guarantee:
    Only the SHA-256 hash of the face embedding is stored in the record.
    The raw 128-dimensional embedding vector is never included.

    Parameters:
        face_embedding: Embedding vector (list of floats) or hash string.
        social_match (dict): Result dictionary from Stage 2 (containing title, link, source, etc.).
        image_path (str): Path of the verified image file.

    Returns:
        dict: Standardized, deterministically serializable verification record.
    """
    if face_embedding is None:
        raise ValueError("Cannot create verification record: missing face embedding.")

    if not isinstance(social_match, dict) or not social_match:
        raise ValueError("Cannot create verification record: invalid or empty social_match dictionary.")

    title = social_match.get("title")
    link = social_match.get("link")
    source = social_match.get("source")

    if not title or not link or not source:
        raise ValueError("Social match must contain non-empty 'title', 'link', and 'source'.")

    face_hash = hash_face_embedding(face_embedding)

    # Extract only existing fields without fabricating missing data
    clean_social = {
        "platform": str(social_match.get("platform") or "Web").strip(),
        "title": str(title).strip(),
        "link": str(link).strip(),
        "source": str(source).strip(),
    }

    if "position" in social_match and social_match["position"] is not None:
        clean_social["position"] = social_match["position"]

    record = {
        "image_path": str(image_path),
        "face_embedding_hash": face_hash,
        "social_match": clean_social,
    }

    return record


@dataclass
class Block:
    """
    Represents a single block in the simulated append-only hash chain.
    """
    index: int
    timestamp: str
    data: dict
    data_hash: str
    previous_hash: str
    block_hash: str

    @classmethod
    def create(cls, index: int, timestamp: str, data: dict, previous_hash: str) -> "Block":
        """
        Creates a new block and calculates its canonical data_hash and block_hash.
        """
        data_hash = calculate_canonical_hash(data)
        header = f"{index}:{timestamp}:{data_hash}:{previous_hash}".encode("utf-8")
        block_hash = hashlib.sha256(header).hexdigest()

        return cls(
            index=index,
            timestamp=timestamp,
            data=data,
            data_hash=data_hash,
            previous_hash=previous_hash,
            block_hash=block_hash,
        )

    def recompute_hash(self) -> str:
        """Recalculates the block hash from its fields to verify block integrity."""
        header = f"{self.index}:{self.timestamp}:{self.data_hash}:{self.previous_hash}".encode("utf-8")
        return hashlib.sha256(header).hexdigest()

    def to_dict(self) -> dict:
        """Serializes block to a dictionary for JSON persistence."""
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "data_hash": self.data_hash,
            "previous_hash": self.previous_hash,
            "block_hash": self.block_hash,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Block":
        """Reconstructs a Block instance from a stored dictionary."""
        required = ["index", "timestamp", "data", "data_hash", "previous_hash", "block_hash"]
        for key in required:
            if key not in d:
                raise ValueError(f"Block dictionary missing required key '{key}'")

        return cls(
            index=d["index"],
            timestamp=d["timestamp"],
            data=d["data"],
            data_hash=d["data_hash"],
            previous_hash=d["previous_hash"],
            block_hash=d["block_hash"],
        )


class SimulatedChain:
    """
    Append-only simulated blockchain persisted to a local JSON file.
    Provides tamper-evident record commitment and verification without external dependencies.
    """

    def __init__(self, chain_path: str = "chain.json"):
        self.chain_path = chain_path
        self.chain: list[Block] = []
        self._initialize_or_load()

    def _create_genesis_block(self) -> Block:
        """Creates the initial genesis block for the chain."""
        genesis_data = {
            "message": "GENESIS_BLOCK",
            "protocol": "HH_GOA_2026_TASK3",
            "description": "Face Identification & Web Verification Immutable Chain"
        }
        return Block.create(
            index=0,
            timestamp="2026-01-01T00:00:00Z",
            data=genesis_data,
            previous_hash="0" * 64,
        )

    def _initialize_or_load(self):
        """Initializes a new chain with Genesis block or loads an existing valid chain."""
        if not os.path.exists(self.chain_path):
            genesis = self._create_genesis_block()
            self.chain = [genesis]
            self._save()
        else:
            self._load()

    def _load(self):
        """Loads and validates the persisted chain from disk."""
        try:
            with open(self.chain_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)

            if not isinstance(raw_data, list) or len(raw_data) == 0:
                raise ValueError(f"Chain file '{self.chain_path}' is empty or invalid format.")

            loaded_chain = [Block.from_dict(item) for item in raw_data]
            self.chain = loaded_chain

            # Validate chain integrity upon load
            validation = self.validate_chain()
            if not validation["valid"]:
                raise ValueError(f"Corrupted blockchain in '{self.chain_path}': {validation['errors']}")

        except json.JSONDecodeError as err:
            raise ValueError(f"Malformed JSON in chain file '{self.chain_path}': {err}")

    def _save(self):
        """Persists the current chain atomically to disk."""
        temp_path = f"{self.chain_path}.tmp"
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump([b.to_dict() for b in self.chain], f, indent=2)
        os.replace(temp_path, self.chain_path)

    def add_block(self, record: dict) -> Block:
        """
        Appends a new verification record block to the chain and saves to disk.

        Parameters:
            record (dict): Validated verification record.

        Returns:
            Block: The newly created and committed block.
        """
        if not isinstance(record, dict) or not record:
            raise ValueError("Record must be a non-empty dictionary.")

        previous_block = self.chain[-1]
        now_ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        new_block = Block.create(
            index=len(self.chain),
            timestamp=now_ts,
            data=record,
            previous_hash=previous_block.block_hash,
        )

        self.chain.append(new_block)
        self._save()
        return new_block

    def get_block(self, identifier: int | str) -> Block | None:
        """
        Retrieves a block by its block index, block hash, or data hash.

        Parameters:
            identifier: int index or str hash.

        Returns:
            Block | None: Found block or None.
        """
        if isinstance(identifier, int):
            if 0 <= identifier < len(self.chain):
                return self.chain[identifier]
            # Attempt reload from disk in case chain was updated
            try:
                self._load()
                if 0 <= identifier < len(self.chain):
                    return self.chain[identifier]
            except Exception:
                pass
            return None

        if isinstance(identifier, str):
            clean_id = identifier.strip().lower()
            for block in self.chain:
                if block.block_hash.lower() == clean_id or block.data_hash.lower() == clean_id:
                    return block
            # Attempt reload from disk in case chain was updated
            try:
                self._load()
                for block in self.chain:
                    if block.block_hash.lower() == clean_id or block.data_hash.lower() == clean_id:
                        return block
            except Exception:
                pass

        return None


    def validate_chain(self) -> dict:
        """
        Performs a full cryptographic audit of the entire blockchain:
        1. Validates Genesis block structure.
        2. Recalculates canonical data_hash for each block.
        3. Recalculates block_hash for each block.
        4. Verifies previous_hash linkage across all adjacent blocks.

        Returns:
            dict: {"valid": bool, "total_blocks": int, "errors": list[str]}
        """
        errors = []
        if not self.chain:
            return {"valid": False, "total_blocks": 0, "errors": ["Chain is empty."]}

        # 1. Validate Genesis Block
        genesis = self.chain[0]
        if genesis.index != 0:
            errors.append(f"Genesis block index is {genesis.index}, expected 0.")
        if genesis.previous_hash != "0" * 64:
            errors.append("Genesis block previous_hash is not 64 zeroes.")
        if genesis.data_hash != calculate_canonical_hash(genesis.data):
            errors.append("Genesis block data_hash mismatch.")
        if genesis.block_hash != genesis.recompute_hash():
            errors.append("Genesis block block_hash mismatch.")

        # 2. Validate Subsequent Blocks
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            prev = self.chain[i - 1]

            if current.index != i:
                errors.append(f"Block #{current.index} has unexpected index (expected {i}).")
            if current.previous_hash != prev.block_hash:
                errors.append(
                    f"Block #{i} previous_hash mismatch: points to '{current.previous_hash[:12]}...', "
                    f"expected '{prev.block_hash[:12]}...'."
                )
            if current.data_hash != calculate_canonical_hash(current.data):
                errors.append(f"Block #{i} data_hash does not match canonical data hash.")
            if current.block_hash != current.recompute_hash():
                errors.append(f"Block #{i} block_hash is invalid.")

        return {
            "valid": len(errors) == 0,
            "total_blocks": len(self.chain),
            "errors": errors,
        }


def commit_record(record: dict, chain_path: str = "chain.json") -> dict:
    """
    High-level API to commit a verification record to the simulated blockchain.

    Parameters:
        record (dict): Standardized verification record.
        chain_path (str): Path to persistence file.

    Returns:
        dict: Commit result summary.
    """
    chain = SimulatedChain(chain_path=chain_path)
    block = chain.add_block(record)

    return {
        "success": True,
        "block_index": block.index,
        "block_hash": block.block_hash,
        "record_hash": block.data_hash,
        "timestamp": block.timestamp,
        "chain_path": chain_path,
    }


def verify_record(
    record: dict,
    block_identifier: int | str | None = None,
    chain_path: str = "chain.json"
) -> dict:
    """
    Cryptographically verifies a record against the blockchain:
    1. Recomputes the canonical SHA-256 hash of the record.
    2. Fetches the on-chain block.
    3. Verifies that the on-chain data_hash matches the record hash.
    4. Validates block hash and chain-wide integrity.

    Parameters:
        record (dict): Record to verify.
        block_identifier: Optional index or block hash. If None, queries by record hash.
        chain_path (str): Path to persistence file.

    Returns:
        dict: Detailed verification results.
    """
    if not os.path.exists(chain_path):
        return {
            "verified": False,
            "record_hash_match": False,
            "block_hash_valid": False,
            "chain_integrity_valid": False,
            "block_index": None,
            "block_hash": None,
            "expected_record_hash": calculate_canonical_hash(record) if isinstance(record, dict) else "",
            "onchain_record_hash": None,
            "details": f"Chain file '{chain_path}' does not exist.",
        }

    try:
        chain = SimulatedChain(chain_path=chain_path)
    except Exception as err:
        return {
            "verified": False,
            "record_hash_match": False,
            "block_hash_valid": False,
            "chain_integrity_valid": False,
            "block_index": None,
            "block_hash": None,
            "expected_record_hash": calculate_canonical_hash(record) if isinstance(record, dict) else "",
            "onchain_record_hash": None,
            "details": f"Failed to load blockchain: {err}",
        }

    chain_audit = chain.validate_chain()
    chain_integrity_valid = chain_audit["valid"]

    expected_record_hash = calculate_canonical_hash(record)

    # Retrieve matching block
    if block_identifier is not None:
        block = chain.get_block(block_identifier)
    else:
        block = chain.get_block(expected_record_hash)

    if not block:
        return {
            "verified": False,
            "record_hash_match": False,
            "block_hash_valid": False,
            "chain_integrity_valid": chain_integrity_valid,
            "block_index": None,
            "block_hash": None,
            "expected_record_hash": expected_record_hash,
            "onchain_record_hash": None,
            "details": "Record hash not found on the blockchain.",
        }

    record_hash_match = (block.data_hash == expected_record_hash)
    block_hash_valid = (block.block_hash == block.recompute_hash())

    is_verified = record_hash_match and block_hash_valid and chain_integrity_valid

    if is_verified:
        details = "Cryptographic integrity verified: record matches on-chain commitment."
    elif not record_hash_match:
        details = "Verification failed: record data does not match on-chain hash."
    elif not block_hash_valid:
        details = "Verification failed: block header hash is invalid/tampered."
    else:
        details = f"Verification failed: chain integrity violated ({', '.join(chain_audit['errors'])})."

    return {
        "verified": is_verified,
        "record_hash_match": record_hash_match,
        "block_hash_valid": block_hash_valid,
        "chain_integrity_valid": chain_integrity_valid,
        "block_index": block.index,
        "block_hash": block.block_hash,
        "expected_record_hash": expected_record_hash,
        "onchain_record_hash": block.data_hash,
        "details": details,
    }


def run_standalone_test() -> bool:
    """
    Executes a complete standalone verification flow and tamper-detection test.
    """
    print("=" * 70)
    print(" HH Goa 2026 - Stage 3: Blockchain Verification ")
    print("=" * 70)

    # 1. Initialize SimulatedChain
    print("\n[INFO] Initializing simulated blockchain...")
    chain = SimulatedChain(chain_path="chain.json")
    print(f"[SUCCESS] Simulated blockchain ready. Current length: {len(chain.chain)} block(s).")

    # 2. Create sample verification record
    print("\n[INFO] Creating privacy-preserving verification record...")
    # 128-dimensional mock embedding vector (representative of Facenet output)
    sample_embedding = [0.0123 * (i % 7 - 3) for i in range(128)]
    sample_social = {
        "platform": "Instagram",
        "title": "Sample Verified Social Post",
        "link": "https://www.instagram.com/p/sample_post_123/",
        "source": "Instagram",
        "position": 1
    }
    sample_image = "test_images/my_public_photo.jpg"

    record = create_verification_record(
        face_embedding=sample_embedding,
        social_match=sample_social,
        image_path=sample_image
    )
    print("[SUCCESS] Verification record created.")
    print(f"[INFO] Face Embedding SHA-256 Hash: {record['face_embedding_hash']}")

    # 3. Calculate canonical hash
    print("\n[INFO] Calculating canonical SHA-256 record hash...")
    record_hash = calculate_canonical_hash(record)
    print(f"[SUCCESS] Canonical Record Hash: {record_hash}")

    # 4. Commit record
    print("\n[INFO] Committing record to simulated blockchain...")
    commit_res = commit_record(record, chain_path="chain.json")
    print(f"[SUCCESS] Record committed at Block #{commit_res['block_index']} -> Block Hash: {commit_res['block_hash']}")

    # 5. Re-fetch and verify committed record
    print("\n[INFO] Re-fetching committed record by block index...")
    fetched_block = chain.get_block(commit_res["block_index"])
    print(f"[SUCCESS] Block #{fetched_block.index} retrieved.")

    print("\n[INFO] Recomputing SHA-256 hash from retrieved data...")
    recomputed_hash = calculate_canonical_hash(fetched_block.data)
    print(f"[SUCCESS] Recomputed Hash: {recomputed_hash}")

    print("\n[INFO] Comparing record hashes...")
    if recomputed_hash == fetched_block.data_hash:
        print("[SUCCESS] Record hash matches on-chain commitment perfectly.")
    else:
        print("[ERROR] Record hash mismatch!")

    # 6. Full cryptographic verification
    print("\n[INFO] Performing end-to-end cryptographic verification...")
    verif_result = verify_record(record, block_identifier=commit_res["block_index"], chain_path="chain.json")
    print(f"[SUCCESS] Verification Status: {'VERIFIED' if verif_result['verified'] else 'FAILED'}")
    print(f"[INFO] Record Hash Match      : {verif_result['record_hash_match']}")
    print(f"[INFO] Block Hash Valid        : {verif_result['block_hash_valid']}")
    print(f"[INFO] Chain Integrity Valid   : {verif_result['chain_integrity_valid']}")

    # 7. Validate entire chain
    print("\n[INFO] Validating entire blockchain integrity...")
    chain_audit = chain.validate_chain()
    print(f"[SUCCESS] Total Blocks Checked : {chain_audit['total_blocks']}")
    print(f"[SUCCESS] Blockchain Integrity : {'VALID' if chain_audit['valid'] else 'CORRUPTED'}")

    print("=" * 70)
    print(f"[RESULT] BLOCKCHAIN VERIFICATION: {'VERIFIED' if verif_result['verified'] else 'FAILED'}")
    print(f"[RESULT] CHAIN INTEGRITY: {'VALID' if chain_audit['valid'] else 'CORRUPTED'}")
    print("=" * 70)

    # -------------------------------------------------------------------------
    # 8. Safe Tamper-Detection Demonstration (in-memory / temporary test)
    # -------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print(" STAGE 3: TAMPER-DETECTION DEMONSTRATION ")
    print("=" * 70)
    print("[INFO] Simulating unauthorized data alteration...")

    # Create a tampered copy of the record (e.g., altered URL or title)
    tampered_record = json.loads(json.dumps(record))
    tampered_record["social_match"]["link"] = "https://www.instagram.com/p/FAKE_TAMPERED_URL/"

    tampered_hash = calculate_canonical_hash(tampered_record)
    print(f"[INFO] Original Record Hash : {record_hash}")
    print(f"[INFO] Tampered Record Hash : {tampered_hash}")

    print("\n[INFO] Verifying tampered record against original Block #{}...".format(commit_res["block_index"]))
    tamper_verif = verify_record(tampered_record, block_identifier=commit_res["block_index"], chain_path="chain.json")

    if not tamper_verif["verified"] and not tamper_verif["record_hash_match"]:
        print("[SUCCESS] Tampering successfully detected!")
        print(f"[SUCCESS] Verification Outcome: REJECTED ({tamper_verif['details']})")
    else:
        print("[ERROR] Tampering was not caught!")

    print("=" * 70)
    print("[RESULT] TAMPER DETECTION: PASSED (Alterations are immediately rejected)")
    print("=" * 70)

    return verif_result["verified"] and (not tamper_verif["verified"])


def main():
    """CLI Entry point for standalone testing of Stage 3."""
    run_standalone_test()


if __name__ == "__main__":
    main()
