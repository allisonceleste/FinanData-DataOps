from pathlib import Path

import pandas as pd

from logger.logger import get_logger


lg = get_logger()


def save_data(
    df: pd.DataFrame,
    destino: Path,
    nombre: str
):

    destino.mkdir(
        parents=True,
        exist_ok=True
    )

    archivo = destino / nombre

    df.to_csv(
        archivo,
        index=False
    )

    lg.info(
        f"Archivo generado: {archivo} "
        f"({len(df)} registros)"
    )
