-- Energy Monitoring Schema
-- Run against Railway Postgres to set up tables

-- Raw 15-minute interval readings from Enphase API
CREATE TABLE IF NOT EXISTS energy_readings (
    id              BIGSERIAL PRIMARY KEY,
    timestamp       TIMESTAMPTZ NOT NULL,
    metric_type     VARCHAR(20) NOT NULL,   -- 'production' or 'consumption'
    watt_hours      INTEGER NOT NULL,       -- wh for the interval
    watts           INTEGER,                -- instantaneous power if available
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_reading UNIQUE (timestamp, metric_type)
);

CREATE INDEX IF NOT EXISTS idx_readings_timestamp ON energy_readings (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_readings_type_timestamp ON energy_readings (metric_type, timestamp DESC);

-- Pre-computed daily aggregates
CREATE TABLE IF NOT EXISTS daily_energy_summary (
    id                      SERIAL PRIMARY KEY,
    date                    DATE NOT NULL,

    -- Production
    production_wh           INTEGER NOT NULL DEFAULT 0,
    production_peak_w       INTEGER,

    -- Consumption
    consumption_wh          INTEGER NOT NULL DEFAULT 0,
    consumption_peak_w      INTEGER,
    consumption_min_w       INTEGER,

    -- Derived
    net_wh                  INTEGER GENERATED ALWAYS AS (production_wh - consumption_wh) STORED,
    self_consumption_pct    NUMERIC(5,2),
    grid_independence_pct   NUMERIC(5,2),

    -- Baseline analysis
    baseline_min_wh         INTEGER,        -- lowest single-interval consumption Wh
    baseline_avg_night_wh   INTEGER,        -- avg consumption Wh during 11pm-5am

    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_daily_date UNIQUE (date)
);

CREATE INDEX IF NOT EXISTS idx_daily_date ON daily_energy_summary (date DESC);

-- Detected anomalies
CREATE TABLE IF NOT EXISTS energy_anomalies (
    id              SERIAL PRIMARY KEY,
    detected_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    anomaly_type    VARCHAR(50) NOT NULL,   -- 'high_baseline', 'consumption_spike', 'night_usage_high'
    severity        VARCHAR(10) NOT NULL,   -- 'info', 'warning', 'critical'
    date            DATE NOT NULL,
    metric_value    NUMERIC(10,2),
    baseline_value  NUMERIC(10,2),
    deviation_pct   NUMERIC(6,2),
    description     TEXT,
    resolved        BOOLEAN NOT NULL DEFAULT FALSE,

    CONSTRAINT uq_anomaly UNIQUE (anomaly_type, date)
);

CREATE INDEX IF NOT EXISTS idx_anomalies_date ON energy_anomalies (date DESC);
CREATE INDEX IF NOT EXISTS idx_anomalies_unresolved ON energy_anomalies (resolved, detected_at DESC) WHERE NOT resolved;

-- OAuth token storage (survives across GitHub Actions runs)
CREATE TABLE IF NOT EXISTS key_value_store (
    key         VARCHAR(100) PRIMARY KEY,
    value       TEXT NOT NULL,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
