from pathlib import Path
import sys

import pandas as pd

import config.paths as pth

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent)
)

from extract.ACH_extract import ACH_extract
from extract.ATM_extract import ATM_extract
from extract.API_extract import API_extract

from cdc.cdc_handler import apply_cdc

from validate.validator import validate_dataframe
from validate.quality_gate import apply_quality_gate

from logger.logger import get_logger


lg = get_logger()


# ==============================================================
# GUARDAR DATA
# ==============================================================

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


# ==============================================================
# PROCESAR CDC
# ==============================================================

def process_cdc(
    df: pd.DataFrame,
    source: str,
    bronze_file: Path
):

    lg.info(
        f"{source}: iniciando CDC"
    )

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


# ==============================================================
# VALIDACIÓN
# ==============================================================

def process_validation(
    df: pd.DataFrame,
    source: str
):

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

    # ==========================================================
    # GREAT EXPECTATIONS
    # ==========================================================

    if not ge_passed:

        lg.error(
            f"{source}: validación Great Expectations "
            f"RECHAZADA"
        )

        lg.error(
            f"{source}: los registros válidos "
            f"NO continúan a Processed"
        )

        return False

    # ==========================================================
    # QUALITY GATE
    # ==========================================================

    quality_gate_passed = apply_quality_gate(
        rejection_rate,
        source
    )

    if not quality_gate_passed:

        lg.error(
            f"{source}: QUALITY GATE RECHAZADO"
        )

        lg.error(
            f"{source}: los registros válidos "
            f"NO continúan a Processed"
        )

        return False

    # ==========================================================
    # PROCESSED
    # ==========================================================

    save_data(
        valid_df,
        pth.PROCESSED_DIR / source.lower(),
        f"{source.lower()}_validated.csv"
    )

    lg.info(
        f"{source}: datos enviados a Processed"
    )

    return True


# ==============================================================
# MAIN
# ==============================================================

def main():

    lg.info("=" * 70)
    lg.info(
        "INICIO DEL PIPELINE FINANDATA-DATAOPS"
    )
    lg.info("=" * 70)

    try:

        # ======================================================
        # EXTRACCIÓN
        # ======================================================

        lg.info("=" * 70)
        lg.info("INICIANDO EXTRACCIÓN")
        lg.info("=" * 70)

        # ------------------------------------------------------
        # ATM
        # ------------------------------------------------------

        lg.info("Extrayendo ATM")

        atm_df = ATM_extract(
            pth.ATM_SOURCE_DIR
        )

        lg.info(
            f"Extracción ATM finalizada: "
            f"{len(atm_df)} registros"
        )

        # ------------------------------------------------------
        # ACH
        # ------------------------------------------------------

        lg.info("Extrayendo ACH")

        ach_df = ACH_extract(
            pth.ACH_SOURCE_DIR
        )

        lg.info(
            f"Extracción ACH finalizada: "
            f"{len(ach_df)} registros"
        )

        # ------------------------------------------------------
        # API
        # ------------------------------------------------------

        lg.info("Extrayendo API")

        api_df = API_extract(
            pth.API_URL
        )

        lg.info(
            f"Extracción API finalizada: "
            f"{len(api_df)} registros"
        )

        lg.info(
            "EXTRACCIÓN FINALIZADA CORRECTAMENTE"
        )

        # ======================================================
        # CDC + BRONZE
        # ======================================================

        lg.info("=" * 70)
        lg.info("INICIANDO CDC + BRONZE")
        lg.info("=" * 70)

        process_cdc(
            atm_df,
            "ATM",
            pth.BRONZE_DIR
            / "atm"
            / "atm_transactions.csv"
        )

        process_cdc(
            ach_df,
            "ACH",
            pth.BRONZE_DIR
            / "ach"
            / "ach_transactions.csv"
        )

        process_cdc(
            api_df,
            "API",
            pth.BRONZE_DIR
            / "api"
            / "api_transactions.csv"
        )

        # ======================================================
        # VALIDACIÓN
        # ======================================================

        lg.info("=" * 70)
        lg.info("INICIANDO VALIDACIÓN")
        lg.info("=" * 70)

        process_validation(
            atm_df,
            "ATM"
        )

        process_validation(
            ach_df,
            "ACH"
        )

        process_validation(
            api_df,
            "API"
        )

        # ======================================================
        # FIN
        # ======================================================

        lg.info("=" * 70)
        lg.info(
            "PIPELINE FINALIZADO"
        )
        lg.info("=" * 70)

    except Exception as e:

        lg.error(
            f"ERROR CRÍTICO DEL PIPELINE: {e}"
        )

        raise


if __name__ == "__main__":
    main()