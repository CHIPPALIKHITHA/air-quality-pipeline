-- 1. Latest PM2.5 reading per station, with CPCB category
CREATE OR REPLACE VIEW v_latest_by_station AS
SELECT DISTINCT ON (s.station_key)
    s.city,
    s.name        AS station,
    s.kind,
    f.value       AS pm25,
    f.measured_at,
    f.lag_hours,
    CASE
        WHEN f.value <= 30  THEN 'Good'
        WHEN f.value <= 60  THEN 'Satisfactory'
        WHEN f.value <= 90  THEN 'Moderate'
        WHEN f.value <= 120 THEN 'Poor'
        WHEN f.value <= 250 THEN 'Very Poor'
        ELSE 'Severe'
    END           AS category
FROM fact_air_quality f
JOIN dim_station   s ON s.station_key   = f.station_key
JOIN dim_parameter p ON p.parameter_key = f.parameter_key
WHERE p.parameter = 'pm25'
ORDER BY s.station_key, f.measured_at DESC;

-- 2. Daily PM2.5 per city (uses the reading's own date, so it works even if date_key is not filled)
CREATE OR REPLACE VIEW v_daily_city_pm25 AS
SELECT s.city,
       (f.measured_at AT TIME ZONE 'Asia/Kolkata')::date AS full_date,
       ROUND(AVG(f.value)::numeric, 1) AS avg_pm25,
       MAX(f.value) AS max_pm25,
       COUNT(*) AS readings
FROM fact_air_quality f
JOIN dim_station   s ON s.station_key   = f.station_key
JOIN dim_parameter p ON p.parameter_key = f.parameter_key
WHERE p.parameter = 'pm25'
GROUP BY s.city, full_date;

-- 3. Average PM2.5 by hour of day (IST)
CREATE OR REPLACE VIEW v_hourly_pattern AS
SELECT s.city,
       EXTRACT(HOUR FROM f.measured_at AT TIME ZONE 'Asia/Kolkata')::int AS hour_ist,
       ROUND(AVG(f.value)::numeric, 1) AS avg_pm25,
       COUNT(*) AS readings
FROM fact_air_quality f
JOIN dim_station   s ON s.station_key   = f.station_key
JOIN dim_parameter p ON p.parameter_key = f.parameter_key
WHERE p.parameter = 'pm25'
GROUP BY s.city, hour_ist;

-- 4. Loaded versus rejected, by reason
CREATE OR REPLACE VIEW v_data_quality AS
SELECT 'loaded' AS status, 'accepted' AS reason, COUNT(*) AS rows FROM fact_air_quality
UNION ALL
SELECT 'rejected', reason, COUNT(*) FROM rejected_readings GROUP BY reason;