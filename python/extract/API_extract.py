from pathlib import Path
import pandas as pd
from logger.logger import get_logger
import requests

lg=get_logger()
def API_extract(origen: str) -> pd.DataFrame:

    lg.info(f"Iniciando la extracción API desde {origen}")
    try:
        response = requests.get(origen)
        lg.info(f"Peticion enviada a {origen} Codigo de estado: {response.status_code}")

        response.raise_for_status()
        data = response.json()
        lg.info(f"Extracción exitosa de datos. Cantidad de datos: {len(response.json())}")

        df = pd.DataFrame(data)
        lg.info(f"Creación exitosa del data frame, con {df.shape[0]} filas y {df.shape[1]} columnas")
        return df
    except Exception as e:
        lg.error(f"Error durante la extracción API: {e}")
        raise
