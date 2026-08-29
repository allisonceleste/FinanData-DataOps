from pathlib import Path
import sys

from prefect import flow, task


# ==============================================================
# PATH DEL PROYECTO
# ==============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(PROJECT_ROOT)
)


# ==============================================================
# IMPORTS DEL PROYECTO
# ==============================================================

import config.paths as pth

from logger.logger import get_logger

from extract.ACH_extract import ACH_extract
from extract.ATM_extract import ATM_extract
from extract.API_extract import API_extract

from processing.cdc_bronze import process_cdc
from processing.validation import process_validation

from transformation.transactions import transform_transactions
from transformation.dimensions import resolve_dimension_keys

from loading.loading_quarantine import load_quarantine
from loading.loading_gold import load_fact_transaction

from utils.file_handler import save_data


# ==============================================================
# LOGGER
# ==============================================================

lg = get_logger()


# ==============================================================
# EXTRACCIÓN ATM
# ==============================================================

@task(
    name="Extracción ATM",
    retries=2,
    retry_delay_seconds=10
)
def extract_atm():

    lg.info("Extrayendo ATM")

    df = ATM_extract(
        pth.ATM_SOURCE_DIR
    )

    lg.info(
        f"Extracción ATM finalizada: "
        f"{len(df)} registros"
    )

    return df


# ==============================================================
# EXTRACCIÓN ACH
# ==============================================================

@task(
    name="Extracción ACH",
    retries=2,
    retry_delay_seconds=10
)
def extract_ach():

    lg.info("Extrayendo ACH")

    df = ACH_extract(
        pth.ACH_SOURCE_DIR
    )

    lg.info(
        f"Extracción ACH finalizada: "
        f"{len(df)} registros"
    )

    return df


# ==============================================================
# EXTRACCIÓN API
# ==============================================================

@task(
    name="Extracción API",
    retries=2,
    retry_delay_seconds=10
)
def extract_api():

    lg.info("Extrayendo API")

    df = API_extract(
        pth.API_URL
    )

    lg.info(
        f"Extracción API finalizada: "
        f"{len(df)} registros"
    )

    return df


# ==============================================================
# CDC + BRONZE
# ==============================================================

@task(
    name="CDC + Bronze"
)
def cdc_bronze(
    df,
    source,
    bronze_file
):

    lg.info(
        f"Procesando CDC + Bronze: {source}"
    )

    result = process_cdc(
        df,
        source,
        bronze_file
    )

    lg.info(
        f"CDC + Bronze finalizado: {source}"
    )

    return result


# ==============================================================
# VALIDACIÓN
# ==============================================================

@task(
    name="Validación"
)
def validate(
    df,
    source
):

    lg.info(
        f"Iniciando validación: {source}"
    )

    valid_df = process_validation(
        df,
        source
    )

    lg.info(
        f"Validación finalizada: {source} | "
        f"{len(valid_df)} registros válidos"
    )

    return valid_df


# ==============================================================
# TRANSFORMACIÓN
# ==============================================================

@task(
    name="Transformación"
)
def transform(
    atm_valid,
    ach_valid,
    api_valid
):


    transactions_df = transform_transactions(
        atm_valid,
        ach_valid,
        api_valid
    )



    return transactions_df


# ==============================================================
# RESOLUCIÓN DE DIMENSIONES
# ==============================================================

@task(
    name="Resolución de dimensiones"
)
def resolve_dimensions(
    transactions_df
):

    lg.info(
        "Iniciando resolución de dimensiones"
    )

    fact_ready_df, dimensional_rejected_df = (
        resolve_dimension_keys(
            transactions_df
        )
    )

    lg.info(
        f"Registros listos para Gold: "
        f"{len(fact_ready_df)}"
    )

    lg.info(
        f"Registros rechazados por dimensiones: "
        f"{len(dimensional_rejected_df)}"
    )

    return (
        fact_ready_df,
        dimensional_rejected_df
    )


# ==============================================================
# CUARENTENA DIMENSIONAL
# ==============================================================

@task(
    name="Cuarentena dimensional"
)
def quarantine_dimensions(
    rejected_df
):

    if rejected_df.empty:

        lg.info(
            "No existen registros rechazados "
            "por integridad dimensional"
        )

        return

    save_data(
        rejected_df,
        pth.REJECTED_DIR / "dimensions",
        "dimensional_rejected.csv"
    )

    load_quarantine(
        rejected_df
    )

    lg.warning(
        f"{len(rejected_df)} registros "
        f"enviados a cuarentena dimensional"
    )


# ==============================================================
# GOLD
# ==============================================================

@task(
    name="Carga Gold"
)
def load_gold(
    fact_ready_df
):

    if fact_ready_df.empty:

        lg.warning(
            "No existen registros para cargar en Gold"
        )

        return 0, 0

    inserted, updated = load_fact_transaction(
        fact_ready_df
    )

    lg.info(
        f"Carga Gold finalizada | "
        f"Insertados: {inserted} | "
        f"Actualizados: {updated}"
    )

    return inserted, updated


# ==============================================================
# FLOW PRINCIPAL
# ==============================================================

@flow(
    name="FinanData DataOps Pipeline"
)
def finandata_pipeline():

    lg.info("*" * 70)
    lg.info(
        "INICIO DEL PIPELINE FINANDATA-DATAOPS"
    )
    lg.info("*" * 70)

    try:

        # ======================================================
        # 1. EXTRACCIÓN
        # ======================================================

        lg.info("=" * 70)
        lg.info("INICIANDO EXTRACCIÓN")
        lg.info("=" * 70)

        atm_df = extract_atm()

        ach_df = extract_ach()

        api_df = extract_api()

        # ======================================================
        # 2. CDC + BRONZE
        # ======================================================

        lg.info("=" * 70)
        lg.info("INICIANDO CDC + BRONZE")
        lg.info("=" * 70)

        cdc_bronze(
            atm_df,
            "ATM",
            pth.BRONZE_DIR
            / "atm"
            / "atm_transactions.csv"
        )

        cdc_bronze(
            ach_df,
            "ACH",
            pth.BRONZE_DIR
            / "ach"
            / "ach_transactions.csv"
        )

        cdc_bronze(
            api_df,
            "API",
            pth.BRONZE_DIR
            / "api"
            / "api_transactions.csv"
        )

        # ======================================================
        # 3. VALIDACIÓN
        # ======================================================

        lg.info("=" * 70)
        lg.info("INICIANDO VALIDACIÓN")
        lg.info("=" * 70)

        atm_valid = validate(
            atm_df,
            "ATM"
        )

        ach_valid = validate(
            ach_df,
            "ACH"
        )

        api_valid = validate(
            api_df,
            "API"
        )

        # ======================================================
        # 4. TRANSFORMACIÓN
        # ======================================================

        lg.info("=" * 70)
        lg.info("INICIANDO TRANSFORMACIÓN")
        lg.info("=" * 70)

        transactions_df = transform(
            atm_valid,
            ach_valid,
            api_valid
        )

        # ======================================================
        # 5. RESOLUCIÓN DE DIMENSIONES
        # ======================================================

        lg.info("=" * 70)
        lg.info(
            "INICIANDO RESOLUCIÓN DE DIMENSIONES"
        )
        lg.info("=" * 70)

        (
            fact_ready_df,
            dimensional_rejected_df
        ) = resolve_dimensions(
            transactions_df
        )

        # ======================================================
        # 6. CUARENTENA DIMENSIONAL
        # ======================================================

        quarantine_dimensions(
            dimensional_rejected_df
        )

        # ======================================================
        # 7. GOLD
        # ======================================================

        lg.info("=" * 70)
        lg.info("INICIANDO CARGA GOLD")
        lg.info("=" * 70)

        inserted, updated = load_gold(
            fact_ready_df
        )

        # ======================================================
        # RESUMEN FINAL
        # ======================================================

        lg.info("=" * 70)
        lg.info("PIPELINE FINALIZADO")
        lg.info(
            f"Registros insertados en Gold: {inserted}"
        )
        lg.info(
            f"Registros actualizados en Gold: {updated}"
        )
        lg.info("=" * 70)

    except Exception as e:

        lg.error(
            f"ERROR CRÍTICO DEL PIPELINE: {e}"
        )

        raise
