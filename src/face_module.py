"""
HH Goa 2026 Task 3: Face Identification & Blockchain Verification
Stage 1: Face Identification Module

This module handles:
1. Validating and loading an input image.
2. Detecting if a human face is present.
3. Generating a face embedding vector using DeepFace with the Facenet model.
4. Displaying clear status messages and embedding dimensions.
"""

import sys
import argparse
from pathlib import Path
from deepface import DeepFace


def extract_face_embedding(image_path: str, model_name: str = "Facenet") -> list | None:
    """
    Extracts a facial embedding vector from a given image using DeepFace.

    Parameters:
        image_path (str): Path to the target image file.
        model_name (str): The face recognition model to use (default: 'Facenet').

    Returns:
        list: The embedding vector (list of floats) if a face is detected.
        None: If the image cannot be found, cannot be loaded, or no face is detected.
    """
    # 1. Verify that the image path exists
    path_obj = Path(image_path)
    if not path_obj.is_file():
        print(f"[ERROR] Image file not found at: '{image_path}'")
        return None

    print(f"[INFO] Loading image from: '{image_path}'...")
    print(f"[INFO] Using DeepFace model: '{model_name}'...")

    try:
        # 2. Extract embedding using DeepFace
        # enforce_detection=True ensures an exception is raised if no face is detected in the image
        results = DeepFace.represent(
            img_path=str(path_obj.resolve()),
            model_name=model_name,
            enforce_detection=True
        )

        # DeepFace.represent returns a list of dictionaries (one per detected face)
        if results and len(results) > 0:
            face_data = results[0]
            embedding = face_data.get("embedding", [])

            print("[SUCCESS] Face detected successfully!")
            print(f"[SUCCESS] Generated embedding vector with dimension: {len(embedding)}")
            return embedding
        else:
            print(f"[ERROR] No face data could be extracted from: '{image_path}'")
            return None

    except ValueError as val_err:
        # DeepFace raises ValueError when enforce_detection=True and no face is found
        print(f"[ERROR] Face detection failed: No face detected in '{image_path}'.")
        print(f"[DETAILS] {val_err}")
        return None

    except Exception as err:
        # Handle any other unexpected errors (e.g., corrupted file, network issue during weight download)
        print(f"[ERROR] An unexpected error occurred while processing the image: {err}")
        return None


def main():
    """
    CLI Entry point to test face embedding extraction from the command line.
    """
    parser = argparse.ArgumentParser(
        description="Stage 1: Face Identification using DeepFace (Facenet model)."
    )
    parser.add_argument(
        "image",
        nargs="?",
        type=str,
        help="Path to the image file to analyze (e.g., test_images/sample.jpg)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="Facenet",
        help="DeepFace model name to use (default: Facenet)"
    )

    args = parser.parse_args()

    # If no image path was passed, show usage help
    if not args.image:
        print("[USAGE] Please provide an image path.")
        print("Example: python src/face_module.py test_images/sample.jpg")
        print("Run 'python src/face_module.py --help' for options.")
        sys.exit(1)

    print("=" * 60)
    print(" HH Goa 2026 - Stage 1: Face Identification ")
    print("=" * 60)

    embedding = extract_face_embedding(image_path=args.image, model_name=args.model)

    if embedding is not None:
        print("=" * 60)
        print("[RESULT] Process completed successfully.")
        print(f"[RESULT] Embedding Dimension (Vector Length): {len(embedding)}")
        print(f"[RESULT] Sample Vector Values (first 5 values): {embedding[:5]}...")
        print("=" * 60)
    else:
        print("=" * 60)
        print("[RESULT] Face identification failed. Please check the errors above.")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
