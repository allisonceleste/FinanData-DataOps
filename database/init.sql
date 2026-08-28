-- =========================================================
-- FinanData
-- Database initialization
-- =========================================================

-- =========================================================
-- SCHEMAS
-- =========================================================

CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;
CREATE SCHEMA IF NOT EXISTS quarantine;
CREATE SCHEMA IF NOT EXISTS audit;


-- =========================================================
-- SILVER
-- =========================================================

CREATE TABLE IF NOT EXISTS silver.transactions (
    silver_transaction_id BIGSERIAL PRIMARY KEY,

    transaction_id VARCHAR(100) NOT NULL,
    source VARCHAR(20) NOT NULL,

    customer_id VARCHAR(50),
    account_id VARCHAR(50),

    transaction_date TIMESTAMP,
    transaction_type VARCHAR(50),

    amount NUMERIC(18,2),
    currency VARCHAR(10),

    status VARCHAR(30),

    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- =========================================================
-- GOLD - DIMENSIONS
-- =========================================================

CREATE TABLE IF NOT EXISTS gold.dim_customer (
    customer_key BIGSERIAL PRIMARY KEY,

    customer_id VARCHAR(50) NOT NULL UNIQUE,

    name VARCHAR(150),
    document_type VARCHAR(20),
    document_number VARCHAR(50),

    segment VARCHAR(30),
    birth_date DATE,
    status VARCHAR(30),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS gold.dim_account (
    account_key BIGSERIAL PRIMARY KEY,

    account_id VARCHAR(50) NOT NULL UNIQUE,

    customer_id VARCHAR(50) NOT NULL,

    account_type VARCHAR(30),
    currency VARCHAR(10),

    opening_date DATE,
    status VARCHAR(30),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS gold.dim_date (
    date_key INTEGER PRIMARY KEY,

    full_date DATE NOT NULL UNIQUE,

    day INTEGER,
    month INTEGER,
    month_name VARCHAR(20),

    quarter INTEGER,
    year INTEGER,

    day_of_week INTEGER,
    day_name VARCHAR(20),

    is_weekend BOOLEAN
);


CREATE TABLE IF NOT EXISTS gold.dim_channel (
    channel_key BIGSERIAL PRIMARY KEY,

    channel_id VARCHAR(50) NOT NULL UNIQUE,

    channel_code VARCHAR(30) NOT NULL,
    channel_name VARCHAR(100) NOT NULL
);


CREATE TABLE IF NOT EXISTS gold.dim_branch (
    branch_key BIGSERIAL PRIMARY KEY,

    branch_id VARCHAR(50) NOT NULL UNIQUE,

    branch_name VARCHAR(150),
    city VARCHAR(100),
    region VARCHAR(100),

    status VARCHAR(30)
);


CREATE TABLE IF NOT EXISTS gold.dim_atm (
    atm_key BIGSERIAL PRIMARY KEY,

    atm_id VARCHAR(50) NOT NULL UNIQUE,

    branch_id VARCHAR(50),

    location VARCHAR(200),
    status VARCHAR(30)
);


-- =========================================================
-- GOLD - FACT
-- =========================================================

CREATE TABLE IF NOT EXISTS gold.fact_transaction (
    transaction_key BIGSERIAL PRIMARY KEY,

    transaction_id VARCHAR(100) NOT NULL,

    customer_key BIGINT NOT NULL,
    account_key BIGINT NOT NULL,
    date_key INTEGER NOT NULL,
    channel_key BIGINT NOT NULL,
    branch_key BIGINT,
    atm_key BIGINT,

    transaction_type VARCHAR(50),

    amount NUMERIC(18,2) NOT NULL,
    currency VARCHAR(10),

    status VARCHAR(30),

    source VARCHAR(20),

    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    update_at TIMESTAMP,

    CONSTRAINT uq_fact_transaction
        UNIQUE (transaction_id, source),

    CONSTRAINT fk_fact_customer
        FOREIGN KEY (customer_key)
        REFERENCES gold.dim_customer(customer_key),

    CONSTRAINT fk_fact_account
        FOREIGN KEY (account_key)
        REFERENCES gold.dim_account(account_key),

    CONSTRAINT fk_fact_date
        FOREIGN KEY (date_key)
        REFERENCES gold.dim_date(date_key),

    CONSTRAINT fk_fact_channel
        FOREIGN KEY (channel_key)
        REFERENCES gold.dim_channel(channel_key),

    CONSTRAINT fk_fact_branch
        FOREIGN KEY (branch_key)
        REFERENCES gold.dim_branch(branch_key),

    CONSTRAINT fk_fact_atm
        FOREIGN KEY (atm_key)
        REFERENCES gold.dim_atm(atm_key)
);


-- =========================================================
-- QUARANTINE
-- =========================================================

CREATE TABLE IF NOT EXISTS quarantine.rejected_transaction (
    quarantine_id BIGSERIAL PRIMARY KEY,

    transaction_id VARCHAR(100),

    source VARCHAR(20),

    rejection_reason VARCHAR(255) NOT NULL,

    raw_data JSONB,

    rejected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    pipeline_run_id VARCHAR(100)
);


-- =========================================================
-- AUDIT - PIPELINE EXECUTION
-- =========================================================

CREATE TABLE IF NOT EXISTS audit.pipeline_execution (
    pipeline_run_id VARCHAR(100) PRIMARY KEY,

    pipeline_name VARCHAR(100),

    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,

    status VARCHAR(30),

    records_extracted INTEGER DEFAULT 0,
    records_valid INTEGER DEFAULT 0,
    records_rejected INTEGER DEFAULT 0,

    rejection_percentage NUMERIC(5,2),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- =========================================================
-- AUDIT - DATA QUALITY
-- =========================================================

CREATE TABLE IF NOT EXISTS audit.data_quality_errors (
    error_id BIGSERIAL PRIMARY KEY,

    pipeline_run_id VARCHAR(100),

    source VARCHAR(20),

    rule_name VARCHAR(100),
    error_type VARCHAR(100),

    records_affected INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- =========================================================
-- INDEXES
-- =========================================================

CREATE INDEX IF NOT EXISTS idx_silver_transaction_id
    ON silver.transactions(transaction_id);

CREATE INDEX IF NOT EXISTS idx_silver_source
    ON silver.transactions(source);

CREATE INDEX IF NOT EXISTS idx_silver_transaction_date
    ON silver.transactions(transaction_date);

CREATE INDEX IF NOT EXISTS idx_fact_customer
    ON gold.fact_transaction(customer_key);

CREATE INDEX IF NOT EXISTS idx_fact_account
    ON gold.fact_transaction(account_key);

CREATE INDEX IF NOT EXISTS idx_fact_date
    ON gold.fact_transaction(date_key);

CREATE INDEX IF NOT EXISTS idx_fact_channel
    ON gold.fact_transaction(channel_key);

CREATE INDEX IF NOT EXISTS idx_quarantine_transaction
    ON quarantine.rejected_transaction(transaction_id);

CREATE INDEX IF NOT EXISTS idx_audit_pipeline
    ON audit.data_quality_errors(pipeline_run_id);