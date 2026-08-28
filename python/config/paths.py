from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "data"

BRONZE_DIR = DATA_DIR / "bronze"
PROCESSED_DIR = DATA_DIR / "processed"
REJECTED_DIR = DATA_DIR / "rejected"

ATM_DIR = BRONZE_DIR / "atm"
ACH_DIR = BRONZE_DIR / "ach"
API_DIR = BRONZE_DIR / "api"


GENERATOR_DIR = Path(
    os.getenv("DATA_GENERATOR_DIR")
)

ATM_SOURCE_DIR = (
    GENERATOR_DIR / "data" / "transactions" / "atm"
)

ACH_SOURCE_DIR = (
    GENERATOR_DIR / "data" / "transactions" / "ach"
)

API_URL = os.getenv(
    "API",
    "http://localhost:8000/transactions"
)