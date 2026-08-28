from pathlib import Path
import pandas as pd
import requests

from logger.logger import get_logger

lg = get_logger()


def API_extract(origen: str) -> pd.DataFrame:

    lg.info(f"Iniciando la extracción API desde {origen}")

    try:

        response = requests.get(origen, timeout=30)

        lg.info(
            f"Petición enviada a {origen} "
            f"Código de estado: {response.status_code}"
        )

        response.raise_for_status()

        data = response.json()

        transactions = data["transactions"]

        lg.info(
            f"Extracción exitosa de datos. "
            f"Cantidad de transacciones: {len(transactions)}"
        )

        df = pd.DataFrame(transactions)

        lg.info(
            f"Creación exitosa del data frame, "
            f"con {df.shape[0]} filas y "
            f"{df.shape[1]} columnas"
        )

        return df

    except requests.RequestException as e:

        lg.error(
            f"Error de conexión con la API bancaria: {e}"
        )

        raise
    
    except Exception as e:

        lg.error(
            f"Error durante la extracción API: {e}"
        )

        raise