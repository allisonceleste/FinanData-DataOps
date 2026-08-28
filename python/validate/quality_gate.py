from logger.logger import get_logger


lg = get_logger()


WARNING_REJECTION_RATE = 0.03
CRITICAL_REJECTION_RATE = 0.05

def apply_quality_gate(
    rejection_rate: float,
    source: str
) -> str:
    """
    Aplica el umbral de rechazo del pipeline.

    Great Expectations se encarga de validar la calidad
    de los registros.

    Este módulo únicamente decide si el porcentaje
    de rechazo permite continuar hacia Processed.
    """

    if rejection_rate <= WARNING_REJECTION_RATE:

        lg.info(
            f"{source}: QUALITY GATE APROBADO"
        )

        lg.info(
            f"{source}: porcentaje de rechazo "
            f"{rejection_rate:.2%} dentro del límite "
            f"permitido ({WARNING_REJECTION_RATE:.2%})"
        )

        return "OK"

    if rejection_rate <= CRITICAL_REJECTION_RATE:
        lg.warning(
            f"{source}: QUALITY GATE ALERTA - "
            f"rechazo={rejection_rate:.2%}"
        )

        lg.warning(
            f"{source}: los registros válidos "
            f"continúan hacia Processed"
        )

        return "WARNING"

    lg.error(
        f"{source}: QUALITY GATE RECHAZADO. "
        f"El porcentaje de rechazo "
        f"({rejection_rate:.2%}) supera "
        f"el máximo permitido "
        f"({CRITICAL_REJECTION_RATE:.2%})"
    )

    return "CRITICAL"