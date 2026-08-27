# FinanData-DataOps

## Descripción

Pipeline ETL financiero implementado con Python,
Prefect, Great Expectations y PostgreSQL.

## Problema

Procesamiento de transacciones provenientes de ATM,
banca móvil y sistemas ACH.

## Arquitectura

Bronze → Validation → Quarantine/Silver → Gold

## Tecnologías

- Python
- Pandas
- Prefect
- Great Expectations
- PostgreSQL
- Docker
- FastAPI

## Fuentes

- ATM CSV
- API bancaria simulada
- ACH CSV

## Data Quality

- No duplicados
- No montos negativos
- Campos obligatorios
- Fechas válidas
- Integridad de identificadores
- Umbral máximo de rechazo: 3%

## Data Warehouse

Modelo estrella:

- fact_transaction
- dim_customer
- dim_account
- dim_date
- dim_channel
- dim_branch

## DataOps

- Orquestación con Prefect
- Reintentos automáticos
- Testing con Great Expectations
- Logs
- Métricas
- Alertas
- Cuarentena
- Auditoría

## Ejecución del generador de datos

docker compose up

## Flujo

Extract → Validate → Quarantine → Transform → Silver → Gold → Tests