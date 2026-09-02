"""
HH Goa 2026 Task 3: Face Identification & Blockchain Verification
Stage 2: Web / Social Media Search Module

This module handles:
1. Validating local input face images.
2. Uploading the image temporarily to ImgBB to generate a public URL.
3. Querying SerpApi's Google Lens engine with the public image URL.
4. Parsing and standardizing visual matches (title, link, source, thumbnail, position).
5. Identifying social media profiles (LinkedIn, X/Twitter, Instagram, Facebook, YouTube, TikTok, GitHub, etc.).
6. Deterministically selecting the best social-media match.
7. Returning structured Python data for downstream verification (Stage 3).
"""

import os
import sys
import argparse
from pathlib import Path
from urllib.parse import urlparse
import requests
from dotenv import load_dotenv

# Ensure safe console output for special Unicode characters / emojis on Windows (cp1252)
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

# Recognized social media platforms and their domain signatures
KNOWN_SOCIAL_PLATFORMS = {
    "linkedin.com": "LinkedIn",
    "instagram.com": "Instagram",
    "facebook.com": "Facebook",
    "fb.com": "Facebook",
    "fb.me": "Facebook",
    "twitter.com": "X (Twitter)",
    "x.com": "X (Twitter)",
    "t.co": "X (Twitter)",
    "youtube.com": "YouTube",
    "youtu.be": "YouTube",
    "tiktok.com": "TikTok",
    "github.com": "GitHub",
    "threads.net": "Threads",
    "reddit.com": "Reddit",
    "pinterest.com": "Pinterest",
    "medium.com": "Medium",
    "quora.com": "Quora",
    "flickr.com": "Flickr",
    "snapchat.com": "Snapchat",
    "bsky.app": "Bluesky",
    "mastodon.social": "Mastodon",
    "tumblr.com": "Tumblr",
    "kaggle.com": "Kaggle",
    "behance.net": "Behance",
    "dribbble.com": "Dribbble",
}

# Platform baseline priority weight for deterministic profile ranking
PLATFORM_PRIORITY = {
    "LinkedIn": 100,
    "X (Twitter)": 90,
    "Instagram": 85,
    "Facebook": 80,
    "GitHub": 75,
    "YouTube": 70,
    "TikTok": 65,
    "Threads": 60,
    "Bluesky": 55,
    "Reddit": 40,
    "Medium": 40,
    "Pinterest": 35,
    "Quora": 30,
}


def load_api_keys() -> tuple[str | None, str | None]:
    """
    Loads and validates required API keys from environment variables / .env file.

    Returns:
        tuple: (imgbb_api_key, serpapi_api_key)
    """
    # Load .env file if present
    load_dotenv(override=False)

    imgbb_key = os.getenv("IMGBB_API_KEY")
    # Support both SERPAPI_API_KEY and SERPAPI_KEY
    serpapi_key = os.getenv("SERPAPI_API_KEY") or os.getenv("SERPAPI_KEY")

    # Clean leading/trailing whitespaces if present
    imgbb_key = imgbb_key.strip() if imgbb_key else None
    serpapi_key = serpapi_key.strip() if serpapi_key else None

    # Check for placeholder values
    if imgbb_key and "your_imgbb_key" in imgbb_key.lower():
        imgbb_key = None
    if serpapi_key and "your_serpapi_key" in serpapi_key.lower():
        serpapi_key = None

    return imgbb_key, serpapi_key


def validate_image(image_path: str) -> bool:
    """
    Validates that the input image path exists, is a file, is non-empty,
    and has a valid supported image extension.

    Parameters:
        image_path (str): Path to local image file.

    Returns:
        bool: True if valid, False otherwise.
    """
    path_obj = Path(image_path)

    if not path_obj.exists():
        print(f"[ERROR] Image file not found: '{image_path}'")
        return False

    if not path_obj.is_file():
        print(f"[ERROR] Path provided is not a file: '{image_path}'")
        return False

    # Check file size
    if path_obj.stat().st_size == 0:
        print(f"[ERROR] Image file is empty (0 bytes): '{image_path}'")
        return False

    # Check extension
    valid_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}
    if path_obj.suffix.lower() not in valid_extensions:
        print(f"[WARNING] File extension '{path_obj.suffix}' may not be supported by ImgBB.")

    return True


def upload_image_to_imgbb(image_path: str, api_key: str | None = None, expiration: int = 600) -> str | None:
    """
    Uploads a local image temporarily to ImgBB using the ImgBB V1 Upload API.

    Parameters:
        image_path (str): Path to the local image file.
        api_key (str): ImgBB API Key. If None, loaded from environment.
        expiration (int): Expiration time in seconds (default: 600s / 10 minutes).

    Returns:
        str | None: The public URL of the uploaded image if successful, None otherwise.
    """
    if not api_key:
        api_key, _ = load_api_keys()

    if not api_key:
        print("[ERROR] Missing IMGBB_API_KEY. Please set IMGBB_API_KEY in your .env file.")
        return None

    if not validate_image(image_path):
        return None

    url = "https://api.imgbb.com/1/upload"
    params = {
        "key": api_key,
        "expiration": expiration  # Automatically expire image after expiration seconds
    }

    print(f"[INFO] Uploading '{image_path}' temporarily to ImgBB...")

    try:
        with open(image_path, "rb") as file_handle:
            files = {"image": file_handle}
            response = requests.post(url, params=params, files=files, timeout=30)

        # Check HTTP status
        if response.status_code != 200:
            print(f"[ERROR] ImgBB upload failed with HTTP {response.status_code}")
            try:
                error_data = response.json()
                error_msg = error_data.get("error", {}).get("message", response.text)
                print(f"[DETAILS] ImgBB API error: {error_msg}")
            except Exception:
                print(f"[DETAILS] Response: {response.text[:200]}")
            return None

        data = response.json()
        if data.get("success"):
            image_url = data.get("data", {}).get("url") or data.get("data", {}).get("display_url")
            if image_url:
                print(f"[SUCCESS] Image uploaded successfully to ImgBB.")
                print(f"[INFO] Public Image URL: {image_url}")
                return image_url
            else:
                print("[ERROR] ImgBB response succeeded but did not contain an image URL.")
                return None
        else:
            error_msg = data.get("error", {}).get("message", "Unknown error")
            print(f"[ERROR] ImgBB returned failure: {error_msg}")
            return None

    except requests.exceptions.Timeout:
        print("[ERROR] Network timeout while uploading image to ImgBB.")
        return None
    except requests.exceptions.ConnectionError:
        print("[ERROR] Failed to connect to ImgBB API. Check your internet connection.")
        return None
    except requests.exceptions.RequestException as req_err:
        print(f"[ERROR] Network error during ImgBB upload: {req_err}")
        return None
    except Exception as exc:
        print(f"[ERROR] Unexpected error during ImgBB upload: {exc}")
        return None


def search_google_lens(image_url: str, api_key: str | None = None) -> dict | None:
    """
    Performs a reverse image search using SerpApi's Google Lens engine.

    Parameters:
        image_url (str): Publicly accessible URL of the image to search.
        api_key (str): SerpApi API key. If None, loaded from environment.

    Returns:
        dict | None: Raw JSON response dictionary from SerpApi, or None on failure.
    """
    if not api_key:
        _, api_key = load_api_keys()

    if not api_key:
        print("[ERROR] Missing SERPAPI_API_KEY. Please set SERPAPI_API_KEY in your .env file.")
        return None

    if not image_url or not image_url.startswith("http"):
        print(f"[ERROR] Invalid image URL provided for Google Lens search: '{image_url}'")
        return None

    endpoint = "https://serpapi.com/search"
    params = {
        "engine": "google_lens",
        "url": image_url,
        "api_key": api_key,
    }

    print("[INFO] Querying SerpApi Google Lens engine for visual matches...")

    try:
        response = requests.get(endpoint, params=params, timeout=45)

        if response.status_code != 200:
            print(f"[ERROR] SerpApi search failed with HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"[DETAILS] SerpApi Error: {error_data.get('error', response.text)}")
            except Exception:
                print(f"[DETAILS] Response: {response.text[:200]}")
            return None

        data = response.json()

        # Check for SerpApi error key in response
        if "error" in data:
            print(f"[ERROR] SerpApi returned error: {data.get('error')}")
            return None

        print("[SUCCESS] Google Lens search completed successfully.")
        return data

    except requests.exceptions.Timeout:
        print("[ERROR] Network timeout while querying SerpApi Google Lens.")
        return None
    except requests.exceptions.ConnectionError:
        print("[ERROR] Failed to connect to SerpApi. Check your internet connection.")
        return None
    except requests.exceptions.RequestException as req_err:
        print(f"[ERROR] Network error during SerpApi search: {req_err}")
        return None
    except Exception as exc:
        print(f"[ERROR] Unexpected error during SerpApi search: {exc}")
        return None


def identify_platform(url: str, source_name: str = "") -> tuple[bool, str]:
    """
    Identifies if a URL or source name corresponds to a known social media platform.
    Uses exact domain and subdomain matching to avoid false positives.

    Parameters:
        url (str): The result URL link.
        source_name (str): The reported source name / domain from search.

    Returns:
        tuple: (is_social: bool, platform_name: str)
    """
    if not url:
        return False, ""

    try:
        netloc = urlparse(url).netloc.lower()
        host = netloc.split(":")[0]  # Remove port if present
    except Exception:
        host = ""

    # 1. Match by domain host (exact match or subdomain)
    if host:
        for known_domain, platform_name in KNOWN_SOCIAL_PLATFORMS.items():
            if host == known_domain or host.endswith("." + known_domain):
                return True, platform_name

    # 2. Match by source string if domain matching did not catch it
    if source_name:
        clean_source = source_name.strip().lower()
        # Direct lookup for common social source titles
        source_mapping = {
            "instagram": "Instagram",
            "linkedin": "LinkedIn",
            "facebook": "Facebook",
            "twitter": "X (Twitter)",
            "x": "X (Twitter)",
            "youtube": "YouTube",
            "tiktok": "TikTok",
            "github": "GitHub",
            "threads": "Threads",
            "reddit": "Reddit",
            "pinterest": "Pinterest",
            "medium": "Medium",
            "quora": "Quora",
            "flickr": "Flickr",
            "snapchat": "Snapchat",
            "bluesky": "Bluesky",
            "mastodon": "Mastodon",
            "tumblr": "Tumblr",
        }
        for key, val in source_mapping.items():
            if clean_source == key or clean_source.startswith(f"{key} ") or clean_source.endswith(f" {key}"):
                return True, val

    return False, ""



def extract_matches(lens_data: dict | None) -> list[dict]:
    """
    Safely extracts and normalizes visual matching results from SerpApi's Google Lens response.

    Parameters:
        lens_data (dict): Raw SerpApi JSON response.

    Returns:
        list[dict]: Standardized list of match dictionaries with fields:
                    [position, title, link, source, domain, thumbnail, is_social, platform]
    """
    if not lens_data or not isinstance(lens_data, dict):
        return []

    # Visual matches is the primary container in Google Lens results
    raw_matches = lens_data.get("visual_matches", [])

    # Also inspect exact_matches or knowledge_graph if available
    exact_matches = lens_data.get("exact_matches", [])
    if isinstance(exact_matches, list):
        # Place exact matches first if any exist
        raw_matches = exact_matches + [m for m in raw_matches if m not in exact_matches]

    if not raw_matches or not isinstance(raw_matches, list):
        return []

    extracted: list[dict] = []

    for index, item in enumerate(raw_matches, start=1):
        if not isinstance(item, dict):
            continue

        title = str(item.get("title") or "").strip()
        link = str(item.get("link") or "").strip()
        source = str(item.get("source") or "").strip()
        thumbnail = str(item.get("thumbnail") or "").strip()
        position = item.get("position", index)

        # Determine domain from URL
        try:
            domain = urlparse(link).netloc.lower() if link else ""
        except Exception:
            domain = ""

        # Identify if this match is on a social media platform
        is_social, platform = identify_platform(url=link, source_name=source)

        match_record = {
            "position": position,
            "title": title,
            "link": link,
            "source": source or domain,
            "domain": domain,
            "thumbnail": thumbnail,
            "is_social": is_social,
            "platform": platform if is_social else None,
        }
        extracted.append(match_record)

    return extracted


def find_best_social_match(matches: list[dict]) -> dict | None:
    """
    Deterministically selects the best social media match from a list of matches.

    Ranking Method:
    - Only considers entries where `is_social == True` and valid `link` exists.
    - Balances visual similarity rank (Google Lens position) and platform authority:
      score = (max(0, 100 - position) * 2) + platform_priority_weight
    - Returns the match with the highest score.

    Parameters:
        matches (list[dict]): List of extracted match dictionaries.

    Returns:
        dict | None: The best social match record, or None if no social matches exist.
    """
    social_candidates = [m for m in matches if m.get("is_social") and m.get("link")]

    if not social_candidates:
        return None

    def rank_score(item: dict) -> float:
        platform = item.get("platform", "")
        # Base platform weight (defaults to 20 for unlisted social platforms)
        platform_weight = PLATFORM_PRIORITY.get(platform, 20)
        position = item.get("position", 100)
        try:
            pos_int = int(position)
        except (ValueError, TypeError):
            pos_int = 100

        # Visual proximity weight (higher for earlier positions in Google Lens)
        visual_rank_score = max(0, 100 - pos_int)
        return (visual_rank_score * 2) + platform_weight

    # Sort candidates deterministically in descending order of score
    sorted_candidates = sorted(social_candidates, key=rank_score, reverse=True)
    return sorted_candidates[0]


def search_image(image_path: str) -> dict:
    """
    High-level orchestrator for Stage 2 Web / Social Media Search.

    Pipeline:
    1. Validates local image file.
    2. Reads API keys from environment.
    3. Uploads image to ImgBB to obtain public URL.
    4. Executes Google Lens reverse image search via SerpApi.
    5. Extracts and parses visual matches.
    6. Identifies social media results and deterministically picks the best match.

    Parameters:
        image_path (str): Local path to target face image.

    Returns:
        dict: Structured result dictionary containing:
              - status: "SUCCESS" | "NO_MATCH" | "ERROR"
              - image_path: str
              - image_url: str | None
              - all_matches: list[dict]
              - social_matches: list[dict]
              - best_social_match: dict | None
              - error_message: str | None
    """
    result = {
        "status": "ERROR",
        "image_path": str(image_path),
        "image_url": None,
        "all_matches": [],
        "social_matches": [],
        "best_social_match": None,
        "error_message": None,
    }

    # 1. Validate image
    if not validate_image(image_path):
        result["error_message"] = f"Invalid or non-existent image path: '{image_path}'"
        return result

    # 2. Check API keys
    imgbb_key, serpapi_key = load_api_keys()
    if not imgbb_key:
        result["error_message"] = "Missing or empty IMGBB_API_KEY in .env"
        print(f"[ERROR] {result['error_message']}")
        return result
    if not serpapi_key:
        result["error_message"] = "Missing or empty SERPAPI_API_KEY in .env"
        print(f"[ERROR] {result['error_message']}")
        return result

    # 3. Upload to ImgBB
    image_url = upload_image_to_imgbb(image_path=image_path, api_key=imgbb_key)
    if not image_url:
        result["error_message"] = "Failed to upload image to ImgBB."
        return result

    result["image_url"] = image_url

    # 4. Search via Google Lens on SerpApi
    lens_data = search_google_lens(image_url=image_url, api_key=serpapi_key)
    if not lens_data:
        result["error_message"] = "Google Lens search returned no response or failed."
        return result

    # 5. Extract all matches
    all_matches = extract_matches(lens_data)
    result["all_matches"] = all_matches

    if not all_matches:
        result["status"] = "NO_MATCH"
        print("[WARNING] Google Lens returned 0 visual matches for this image.")
        return result

    print(f"[SUCCESS] Extracted {len(all_matches)} total visual matches from Google Lens.")

    # 6. Filter social matches and pick best match
    social_matches = [m for m in all_matches if m.get("is_social")]
    result["social_matches"] = social_matches

    best_social = find_best_social_match(all_matches)
    result["best_social_match"] = best_social

    if best_social:
        result["status"] = "SUCCESS"
        print(f"[SUCCESS] Found {len(social_matches)} social media match(es).")
    else:
        result["status"] = "NO_MATCH"
        print("[INFO] Web matches were found, but no social-media profile match exists.")

    return result


def _clean_str(text: str) -> str:
    """Safely sanitizes text for terminal output on Windows."""
    if not text:
        return ""
    # Replace non-ascii characters or characters that might fail in legacy consoles
    return text.encode("ascii", errors="replace").decode("ascii")


def main():
    """
    CLI Entry point to test Stage 2 search module from the command line.
    """
    parser = argparse.ArgumentParser(
        description="Stage 2: Reverse Image Web & Social Media Search (ImgBB + SerpApi Google Lens)."
    )
    parser.add_argument(
        "image",
        nargs="?",
        type=str,
        help="Path to the local image file to search (e.g. test_images/my_public_photo.jpg)"
    )
    parser.add_argument(
        "--upload-only",
        action="store_true",
        help="Upload image to ImgBB only and print the public URL without querying SerpApi"
    )

    args = parser.parse_args()

    # If no image path was passed, show usage help
    if not args.image:
        print("[USAGE] Please provide a local image path.")
        print("Example: python src/search_module.py test_images/my_public_photo.jpg")
        print("Example (ImgBB only): python src/search_module.py test_images/my_public_photo.jpg --upload-only")
        print("Run 'python src/search_module.py --help' for options.")
        sys.exit(1)

    # Standalone ImgBB Upload Test (without SerpApi)
    if args.upload_only:
        print("=" * 70)
        print(" HH Goa 2026 - ImgBB Upload Test (Standalone) ")
        print("=" * 70)
        url = upload_image_to_imgbb(args.image)
        print("=" * 70)
        if url:
            print("[RESULT] ImgBB Upload: SUCCESS")
            print(f"[RESULT] Public Image URL: {url}")
            print("=" * 70)
        else:
            print("[RESULT] ImgBB Upload: FAILED")
            print("=" * 70)
            sys.exit(1)
        return

    print("=" * 70)
    print(" HH Goa 2026 - Stage 2: Web / Social Media Search ")
    print("=" * 70)

    search_result = search_image(args.image)

    print("=" * 70)
    print(f"[RESULT] Overall Status: {search_result['status']}")
    print(f"[RESULT] Target Image: {search_result['image_path']}")
    if search_result.get("image_url"):
        print(f"[RESULT] Hosted Image URL: {search_result['image_url']}")

    total_matches = len(search_result.get("all_matches", []))
    social_matches = len(search_result.get("social_matches", []))
    print(f"[RESULT] Total Visual Matches: {total_matches}")
    print(f"[RESULT] Social Media Matches: {social_matches}")

    # Display best social match if found
    best_match = search_result.get("best_social_match")
    if best_match:
        print("-" * 70)
        print("[RESULT] BEST SOCIAL MEDIA MATCH:")
        print(f"  * Platform : {best_match.get('platform')}")
        print(f"  * Title    : {_clean_str(best_match.get('title', ''))}")
        print(f"  * Link     : {best_match.get('link')}")
        print(f"  * Source   : {_clean_str(best_match.get('source', ''))}")
        print(f"  * Position : #{best_match.get('position')}")
        print("-" * 70)
    else:
        print("-" * 70)
        print("[RESULT] BEST SOCIAL MEDIA MATCH: No social-media match found.")
        print("-" * 70)

    # Display top web matches overview
    if total_matches > 0:
        print("\n--- TOP WEB MATCHES OVERVIEW ---")
        for match in search_result["all_matches"][:5]:
            social_tag = f"[{match['platform']}]" if match.get("is_social") else "[Web]"
            clean_title = _clean_str(match.get("title", "No title"))
            print(f"#{match['position']} {social_tag} {clean_title} -> {match.get('link', 'No link')}")

    if search_result["status"] == "ERROR":
        print(f"\n[ERROR] Search failed: {search_result.get('error_message')}")
        sys.exit(1)

    print("=" * 70)


if __name__ == "__main__":
    main()

