import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

CHARACTERS_DIR = PROJECT_ROOT / "characters"
REFERENCE_IMAGES_DIR = PROJECT_ROOT / "reference_images"
# Backwards-compatible name for callers introduced before the folder contract
# was settled.
REFERENCES_DIR = REFERENCE_IMAGES_DIR
POOLS_DIR = PROJECT_ROOT / "pools"
STYLES_DIR = PROJECT_ROOT / "styles"
OUTPUT_DIR = PROJECT_ROOT / "output"

# Image execution remains optional and is configured entirely from the host
# environment.  No credential is ever represented in application data.
DEFAULT_IMAGE_PROVIDER = os.getenv("CHARACTERSTUDIO_IMAGE_PROVIDER", "fake")
GEMINI_IMAGE_MODEL = os.getenv("CHARACTERSTUDIO_GEMINI_IMAGE_MODEL", "gemini-3.1-flash-image")
GEMINI_API_KEY_ENV = "GEMINI_API_KEY"

# Reference assets are presentation inputs, but the mapping is canonical.  Do
# not infer it from a character ID: canonical IDs intentionally need not match
# asset file stems.
CHARACTER_REFERENCE_IMAGES = {
    "ayami_tanaka": "ayami.png",
    "charlotte_taylor_rose": "charlotte.png",
    "idun_braten": "idun.png",
    "luna_campbell": "luna.png",
    "naomi": "naomi.png",
    "zara": "zara.png",
}


def reference_image_for(character_id: str) -> Path | None:
    """Return the explicitly approved reference image for a canonical ID."""
    filename = CHARACTER_REFERENCE_IMAGES.get(character_id)
    return REFERENCE_IMAGES_DIR / filename if filename else None
