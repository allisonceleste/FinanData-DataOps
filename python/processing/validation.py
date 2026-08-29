import pandas as pd

import config.paths as pth

from loading.loading_quarantine import load_quarantine
from logger.logger import get_logger
from utils.file_handler import save_data

from validate.validator import validate_dataframe
from validate.quality_gate import apply_quality_gate


lg = get_logger()

def process_validation(
    df: pd.DataFrame,
    source: str
) -> pd.DataFrame:

    lg.info(
        f"Procesando validación de {source}"
    )

    valid_df, rejected_df, ge_passed, rejection_rate = (
        validate_dataframe(
            df,
            source
        )
    )

    # ==========================================================
    # REJECTED
    # ==========================================================

    if not rejected_df.empty:

        save_data(
            rejected_df,
            pth.REJECTED_DIR / source.lower(),
            f"{source.lower()}_rejected.csv"
        )

        load_quarantine(
            rejected_df
        )

        lg.warning(
            f"{source}: {len(rejected_df)} registros "
            f"enviados a cuarentena"
        )

    # ==========================================================
    # QUALITY GATE
    # ==========================================================

    quality_status = apply_quality_gate(
        rejection_rate,
        source
    )

    # ==========================================================
    # QUALITY GATE CRITICAL
    # ==========================================================

    if quality_status == "CRITICAL":

        lg.error(
            f"{source}: QUALITY GATE CRÍTICO"
        )

        lg.error(
            f"{source}: los datos válidos "
            f"NO continúan a Processed"
        )

        return pd.DataFrame()

    # ==========================================================
    # WARNING
    # ==========================================================

    if quality_status == "WARNING":

        lg.warning(
            f"{source}: QUALITY GATE EN WARNING"
        )

        lg.warning(
            f"{source}: los registros válidos "
            f"CONTINÚAN a Processed"
        )

    # ==========================================================
    # OK
    # ==========================================================

    elif quality_status == "OK":

        lg.info(
            f"{source}: QUALITY GATE OK"
        )

        lg.info(
            f"{source}: los registros válidos "
            f"continúan a Processed"
        )

    # ==========================================================
    # PROCESSED
    # ==========================================================

    if not valid_df.empty:

        save_data(
            valid_df,
            pth.PROCESSED_DIR / source.lower(),
            f"{source.lower()}_validated.csv"
        )

        lg.info(
            f"{source}: {len(valid_df)} registros "
            f"enviados a Processed"
        )

    else:

        lg.warning(
            f"{source}: no existen registros válidos "
            f"para enviar a Processed"
        )

    # ==========================================================
    # RETORNAR DATOS VÁLIDOS
    # ==========================================================

    return valid_df
