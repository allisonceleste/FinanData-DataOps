from logger.logger import get_logger


lg = get_logger()

MAX_REJECTION_RATE = 0.03


def apply_quality_gate(
    rejection_rate: float,
    source: str
) -> bool:
    """
    Aplica el umbral de rechazo del pipeline.

    Great Expectations se encarga de validar la calidad
    de los registros.

    Este módulo únicamente decide si el porcentaje
    de rechazo permite continuar hacia Processed.
    """

    if rejection_rate <= MAX_REJECTION_RATE:

        lg.info(
            f"{source}: QUALITY GATE APROBADO"
        )

        lg.info(
            f"{source}: porcentaje de rechazo "
            f"{rejection_rate:.2%} dentro del límite "
            f"permitido ({MAX_REJECTION_RATE:.2%})"
        )

        return True

    lg.error(
        f"{source}: QUALITY GATE RECHAZADO. "
        f"El porcentaje de rechazo "
        f"({rejection_rate:.2%}) supera "
        f"el máximo permitido "
        f"({MAX_REJECTION_RATE:.2%})"
    )

    return False