from pathlib import Path

import pandas as pd

import config.paths as pth

from cdc.cdc_handler import apply_cdc
from logger.logger import get_logger
from utils.file_handler import save_data
lg = get_logger()
def process_cdc(
    df: pd.DataFrame,
    source: str,
    bronze_file: Path
):


    cdc_df = apply_cdc(
        df,
        bronze_file,
        source
    )

    if not cdc_df.empty:

        save_data(
            cdc_df,
            pth.BRONZE_DIR / source.lower(),
            f"{source.lower()}_cdc.csv"
        )

    # Bronze siempre representa la extracción actual
    save_data(
        df,
        pth.BRONZE_DIR / source.lower(),
        f"{source.lower()}_transactions.csv"
    )

    return cdc_df
