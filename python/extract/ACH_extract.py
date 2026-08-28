from pathlib import Path
import pandas as pd
from logger.logger import get_logger

lg = get_logger()

def ACH_extract(origen: Path) -> pd.DataFrame:
    lg.info(f"Iniciando extracción ACH desde: {origen}")
    try:
        files = list(origen.glob("*.csv"))
        if not files:
            raise FileNotFoundError(
                f"No se encontraron archivos CSV en {origen}"
            )
        dataframes = []
        for file in files:
            lg.info(f"Leyendo archivo: {file.name}")
            df = pd.read_csv(file, delimiter=";")
            dataframes.append(df)
            lg.info(
                f"Archivo {file.name}: "
                f"{len(df)} registros"
            )
        ach_df = pd.concat(
            dataframes,
            ignore_index=True
        )
        lg.info(
            f"Extracción ACH exitosa. "
            f"Total registros: {len(ach_df)}"
        )
        return ach_df
    except Exception as e:
        lg.error(
            f"Error durante la extracción ACH: {e}"
        )
        raise