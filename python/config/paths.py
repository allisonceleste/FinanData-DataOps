from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "data"

BRONZE_DIR = DATA_DIR / "bronze"
PROCESSED_DIR = DATA_DIR / "processed"
REJECTED_DIR = DATA_DIR / "rejected"

ATM_DIR = BRONZE_DIR / "atm"
ACH_DIR = BRONZE_DIR / "ach"
API_DIR = BRONZE_DIR / "api"