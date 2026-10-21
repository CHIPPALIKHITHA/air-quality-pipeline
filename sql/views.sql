-- Latest PM2.5 reading per station, with CPCB category.
-- Categories use hourly values against limits defined for 24-hour averages.
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