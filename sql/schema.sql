-- Dimensions
CREATE TABLE IF NOT EXISTS dim_station (
    station_key  SERIAL PRIMARY KEY,
    station_id   INT UNIQUE NOT NULL,      -- OpenAQ location id
    name         TEXT NOT NULL,
    city         TEXT NOT NULL,
    kind         TEXT NOT NULL             -- 'live' or 'full'
);

CREATE TABLE IF NOT EXISTS dim_parameter (
    parameter_key SERIAL PRIMARY KEY,
    parameter     TEXT NOT NULL,           -- pm25, no2, ...
    units         TEXT NOT NULL,
    UNIQUE (parameter, units)
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_key     INT PRIMARY KEY,          -- 20261018
    full_date    DATE NOT NULL,
    year         SMALLINT NOT NULL,
    month        SMALLINT NOT NULL,
    day_of_week  SMALLINT NOT NULL         -- 1 = Monday ... 7 = Sunday
);

INSERT INTO dim_date (date_key, full_date, year, month, day_of_week)
SELECT to_char(d, 'YYYYMMDD')::int, d::date,
       EXTRACT(YEAR FROM d), EXTRACT(MONTH FROM d), EXTRACT(ISODOW FROM d)
FROM generate_series('2026-01-01'::date, '2027-12-31'::date, interval '1 day') AS d
ON CONFLICT (date_key) DO NOTHING;

-- Fact table
CREATE TABLE IF NOT EXISTS fact_air_quality (
    reading_id    BIGSERIAL PRIMARY KEY,
    station_key   INT NOT NULL REFERENCES dim_station(station_key),
    parameter_key INT NOT NULL REFERENCES dim_parameter(parameter_key),
    date_key      INT NOT NULL REFERENCES dim_date(date_key),
    value         NUMERIC NOT NULL,
    measured_at   TIMESTAMPTZ NOT NULL,
    ingested_at   TIMESTAMPTZ NOT NULL,
    lag_hours     NUMERIC(10,2) NOT NULL,
    UNIQUE (station_key, parameter_key, measured_at)   -- no duplicate readings
);

CREATE INDEX IF NOT EXISTS idx_fact_station_time
    ON fact_air_quality (station_key, measured_at DESC);
CREATE INDEX IF NOT EXISTS idx_fact_date
    ON fact_air_quality (date_key);

-- Rows removed by the cleaning step, with the reason
CREATE TABLE IF NOT EXISTS rejected_readings (
    id          BIGSERIAL PRIMARY KEY,
    station_id  INT,
    sensor_id   BIGINT,
    parameter   TEXT,
    units       TEXT,
    value       NUMERIC,
    measured_at TIMESTAMPTZ,
    reason      TEXT NOT NULL,
    loaded_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);


-- Every alert we decided to send
CREATE TABLE IF NOT EXISTS alerts_log (
    id          BIGSERIAL PRIMARY KEY,
    station_key INT NOT NULL REFERENCES dim_station(station_key),
    parameter   TEXT NOT NULL,
    value       NUMERIC NOT NULL,
    category    TEXT NOT NULL,
    sent_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    delivered   BOOLEAN NOT NULL DEFAULT false
);