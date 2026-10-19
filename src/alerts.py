import os
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from alert_rules import should_alert
from aqi import pm25_category
from load import connect

load_dotenv()
IST = ZoneInfo("Asia/Kolkata")


def fetch_live_readings(cur):
    """Latest 5 PM2.5 readings for each 'live' station, newest first."""
    cur.execute("""
        SELECT s.station_key, s.name, s.city, f.measured_at, f.value
        FROM fact_air_quality f
        JOIN dim_station s USING (station_key)
        JOIN dim_parameter p USING (parameter_key)
        WHERE s.kind = 'live' AND p.parameter = 'pm25'
        ORDER BY s.station_key, f.measured_at DESC""")
    stations = {}
    for key, name, city, measured_at, value in cur.fetchall():
        st = stations.setdefault(key, {"name": name, "city": city, "readings": []})
        if len(st["readings"]) < 5:
            st["readings"].append((measured_at, float(value)))
    return stations


def last_alert_time(cur, station_key):
    cur.execute("SELECT max(sent_at) FROM alerts_log "
                "WHERE station_key = %s AND delivered", (station_key,))
    return cur.fetchone()[0]


def send_email(subject, body):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = os.getenv("SMTP_USER")
    msg["To"] = os.getenv("ALERT_TO")
    msg.set_content(body)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
        smtp.login(os.getenv("SMTP_USER"), os.getenv("SMTP_APP_PASSWORD"))
        smtp.send_message(msg)


def main():
    dry_run = os.getenv("ALERT_DRY_RUN", "1") != "0"     # safe by default
    now = datetime.now(timezone.utc)
    conn = connect()
    with conn, conn.cursor() as cur:
        for key, st in fetch_live_readings(cur).items():
            ok, reason = should_alert(st["readings"], now, last_alert_time(cur, key))
            when, value = st["readings"][0]
            category = pm25_category(value)
            print(f"{st['city']} | {st['name']} | PM2.5 {value} ({category}) at "
                  f"{when.astimezone(IST):%d %b %H:%M} IST | alert={ok} ({reason})")
            if not ok:
                continue

            subject = f"Air quality alert: {st['city']} PM2.5 is {category}"
            body = (f"{st['name']}, {st['city']}\n"
                    f"PM2.5: {value} ug/m3 ({category})\n"
                    f"Measured: {when.astimezone(IST):%d %b %Y %H:%M} IST\n\n"
                    "This is based on the latest hourly readings and CPCB PM2.5 "
                    "category limits (defined for 24-hour averages). Consider "
                    "limiting outdoor exposure.")
            if dry_run:
                print("   DRY RUN - would send:", subject)
                continue
            try:
                send_email(subject, body)
                delivered = True
            except Exception as exc:                       # keep going, log failure
                print("   email failed:", exc)
                delivered = False
            cur.execute("INSERT INTO alerts_log (station_key, parameter, value, category, delivered) "
                        "VALUES (%s, 'pm25', %s, %s, %s)", (key, value, category, delivered))
    conn.close()


if __name__ == "__main__":
    main()