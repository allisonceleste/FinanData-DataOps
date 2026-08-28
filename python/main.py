from pathlib import Path
import sys

import pandas as pd

import config.paths as pth
from loading.loading_gold import load_fact_transaction
from loading.loading_quarantine import load_quarantine
from transformation.dimensions import resolve_dimension_keys
from transformation.transactions import transform_transactions

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

# ==============================================================
# MAIN
# ==============================================================

def main():

    lg.info("*" * 70)
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

        atm_valid = process_validation(
            atm_df,
            "ATM"
        )

        ach_valid = process_validation(
            ach_df,
            "ACH"
        )

        api_valid = process_validation(
            api_df,
            "API"
        )

        # ======================================================
        # TRANSFORMACIÓN
        # ======================================================

        lg.info("=" * 70)
        lg.info("INICIANDO TRANSFORMACIÓN")
        lg.info("=" * 70)

        transactions_df = transform_transactions(
            atm_valid,
            ach_valid,
            api_valid
        )

        lg.info(
            f"TRANSFORMACIÓN FINALIZADA: "
            f"{len(transactions_df)} registros"
        )

        # ======================================================
        # RESOLUCIÓN DE DIMENSIONES
        # ======================================================

        lg.info("=" * 70)
        lg.info("INICIANDO RESOLUCIÓN DE DIMENSIONES")
        lg.info("=" * 70)

        fact_ready_df, dimensional_rejected_df = resolve_dimension_keys(
            transactions_df
        )

        lg.info(
            f"RESOLUCIÓN DE DIMENSIONES FINALIZADA: "
            f"{len(fact_ready_df)} registros"
        )

        # ======================================================
        # CUARENTENA POR INTEGRIDAD DIMENSIONAL
        # ======================================================

        if not dimensional_rejected_df.empty:

            save_data(
                dimensional_rejected_df,
                pth.REJECTED_DIR / "dimensions",
                "dimensional_rejected.csv"
            )

            load_quarantine(
                dimensional_rejected_df
            )

            lg.warning(
                f"{len(dimensional_rejected_df)} registros "
                f"enviados a cuarentena por integridad dimensional"
            )

        else:

            lg.info(
                "No existen registros rechazados "
                "por integridad dimensional"
            )

        # ======================================================
        # GOLD
        # ======================================================

        lg.info("=" * 70)
        lg.info("INICIANDO CARGA GOLD")
        lg.info("=" * 70)

        load_fact_transaction(
            fact_ready_df
        )

        lg.info(
            f"CARGA GOLD FINALIZADA: "
            f"{len(fact_ready_df)} registros procesados"
        )

        # ======================================================
        # FIN
        # ======================================================

        lg.info("=" * 70)
        lg.info(
            "PIPELINE FINALIZADO"
        )
        lg.info("*" * 70)

    except Exception as e:

        lg.error(
            f"ERROR CRÍTICO DEL PIPELINE: {e}"
        )

        raise


if __name__ == "__main__":
    main()