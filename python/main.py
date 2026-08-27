from extract.ATM_extract import ATM_extract
from logger.logger import get_logger
import config.paths as pth

lg = get_logger()

def main():

    lg.info("-_" * 60)
    lg.info("Iniciando extracción")
    atm_df = ATM_extract(pth.ATM_DIR)
    lg.info(
        f"Extracción ATM finalizada: "
        f"{len(atm_df)} registros"
    )

if __name__ == "__main__":
    main()