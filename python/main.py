import os
import config.paths as pth

from extract.ACH_extract import ACH_extract
from extract.ATM_extract import ATM_extract
from extract.API_extract import API_extract

from logger.logger import get_logger
from dotenv import load_dotenv

load_dotenv()
API = os.getenv("API")
lg = get_logger()

def main():

    lg.info("-_" * 60)
    lg.info("Iniciando extracción")

    atm_df = ATM_extract(pth.ATM_DIR)
    lg.info(f"Extracción ATM finalizada: {len(atm_df)} registros")

    api_df = API_extract(API)
    lg.info(f"Extracción API finalizada: {len(api_df)} registros")

    ach_df = ACH_extract(pth.ACH_DIR)
    lg.info(f"Extracción ACH finalizada: {len(ach_df)} registros")




if __name__ == "__main__":
    main()