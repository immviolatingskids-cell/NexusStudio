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
