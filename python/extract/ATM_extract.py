from pathlib import Path
import pandas as pd
from logger.logger import get_logger

lg = get_logger()

def ATM_extract(origen: Path) -> pd.DataFrame:
    lg.info(f"Iniciando extracción ATM desde: {origen}")
    try:
        files = list(origen.glob("*.csv"))
        if not files:
            raise FileNotFoundError(
                f"No se encontraron archivos CSV en {origen}"
            )
        dataframes = []
        for file in files:
            lg.info(f"Leyendo archivo: {file.name}")
            df = pd.read_csv(file)
            dataframes.append(df)
            lg.info(
                f"Archivo {file.name}: "
                f"{len(df)} registros"
            )
        atm_df = pd.concat(
            dataframes,
            ignore_index=True
        )
        lg.info(
            f"Extracción ATM exitosa. "
            f"Total registros: {len(atm_df)}"
        )
        return atm_df
    except Exception as e:
        lg.error(
            f"Error durante la extracción ATM: {e}"
        )
        raise