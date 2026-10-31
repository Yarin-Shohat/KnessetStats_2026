"""Static configuration: paths, URLs and constants."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESOURCES_DIR = PROJECT_ROOT / "resources"
CACHE_DIR = PROJECT_ROOT / ".cache"

BASE_URL = "https://elections.kaplanopensource.co.il"
REQUEST_HEADERS = {"User-Agent": "Mozilla/5.0 (KnessetStats research dashboard)"}
KNESSETS = (25, 26)
TOTAL_MANDATES = 120
