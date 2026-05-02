"""
Smart Emergency Alert System
Flask Backend - app.py  (Production / Render ready)
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# ─── CONFIG ───────────────────────────────────────────────────────────────────
SENDER_EMAIL    = os.environ.get("SENDER_EMAIL",    "mannathanthanishka07@gmail.com")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD", "mail password")
RECEIVER_EMAIL  = os.environ.get("RECEIVER_EMAIL",  "mannathanthanishka07@gmail.com")

# On Render, use /tmp for writable storage (SQLite)
if os.environ.get("RENDER"):
    DB_PATH = "/tmp/alerts.db"
else:
    DB_PATH = os.path.join(os.path.dirname(__file__), "instance", "alerts.db")

# ─── DATABASE ─────────────────────────────────────────────────────────────────
def init_db():
    os.makedirs(os.path.dirname(DB_PATH) if os.path.dirname(DB_PATH) else ".", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            latitude  REAL    NOT NULL,
            longitude REAL    NOT NULL,
            maps_link TEXT    NOT NULL,
            address   TEXT,
            timestamp TEXT    NOT NULL,
            status    TEXT    DEFAULT 'sent'
        )
    """)
    conn.commit()
    conn.close()
    print("✅  Database initialised at", DB_PATH)


def save_alert(lat, lng, maps_link, address, timestamp):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO alerts (latitude, longitude, maps_link, address, timestamp) VALUES (?,?,?,?,?)",
        (lat, lng, maps_link, address, timestamp)
    )
    conn.commit()
    alert_id = cursor.lastrowid
    conn.close()
    return alert_id


def fetch_all_alerts():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM alerts ORDER BY id DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


# ─── EMAIL ────────────────────────────────────────────────────────────────────
def send_email_alert(lat, lng, maps_link, address, timestamp):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "🚨 EMERGENCY ALERT – Panic Button Triggered"
    msg["From"]    = SENDER_EMAIL
    msg["To"]      = RECEIVER_EMAIL

    plain = f"""
EMERGENCY ALERT
===============
A panic button was triggered.

Time      : {timestamp}
Latitude  : {lat}
Longitude : {lng}
Location  : {address or 'Unknown'}
Maps Link : {maps_link}

This is an automated alert. Please respond immediately.
"""

    html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #0a0a0a; color: #f0f0f0; margin: 0; padding: 0; }}
    .wrapper {{ max-width: 600px; margin: 40px auto; background: #111; border-radius: 16px; overflow: hidden; border: 1px solid #333; }}
    .header {{ background: linear-gradient(135deg, #c0392b, #e74c3c); padding: 32px; text-align: center; }}
    .header h1 {{ margin: 0; font-size: 28px; color: #fff; letter-spacing: 2px; }}
    .header .icon {{ font-size: 52px; margin-bottom: 12px; display: block; }}
    .body {{ padding: 32px; }}
    .row {{ display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #222; }}
    .label {{ color: #888; font-size: 13px; text-transform: uppercase; letter-spacing: 1px; }}
    .value {{ color: #f0f0f0; font-size: 14px; font-weight: 600; text-align: right; max-width: 70%; }}
    .btn {{ display: block; margin: 28px auto 0; padding: 16px 36px; background: linear-gradient(135deg, #c0392b, #e74c3c);
             color: #fff; font-size: 16px; font-weight: 700; text-decoration: none; border-radius: 50px;
             text-align: center; letter-spacing: 1px; }}
    .footer {{ background: #0d0d0d; padding: 16px; text-align: center; color: #555; font-size: 12px; }}
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="header">
      <span class="icon">🚨</span>
      <h1>EMERGENCY ALERT</h1>
      <p style="margin:8px 0 0;color:#ffcccc;font-size:14px;">Panic Button Triggered</p>
    </div>
    <div class="body">
      <div class="row"><span class="label">⏰ Time</span><span class="value">{timestamp}</span></div>
      <div class="row"><span class="label">📍 Latitude</span><span class="value">{lat}</span></div>
      <div class="row"><span class="label">📍 Longitude</span><span class="value">{lng}</span></div>
      <div class="row"><span class="label">🏠 Address</span><span class="value">{address or 'Fetching...'}</span></div>
      <a href="{maps_link}" class="btn">📌 Open in Google Maps</a>
    </div>
    <div class="footer">Smart Emergency Alert System &nbsp;|&nbsp; Automated Notification</div>
  </div>
</body>
</html>
"""

    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
    print(f"✅  Email sent to {RECEIVER_EMAIL}")


# ─── ROUTES ───────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/history")
def history():
    return render_template("history.html")


@app.route("/api/alert", methods=["POST"])
def trigger_alert():
    data = request.get_json()
    lat  = data.get("latitude")
    lng  = data.get("longitude")
    addr = data.get("address", "")

    if lat is None or lng is None:
        return jsonify({"success": False, "message": "GPS coordinates missing"}), 400

    timestamp = datetime.now().strftime("%d %B %Y, %I:%M:%S %p")
    maps_link = f"https://www.google.com/maps?q={lat},{lng}"

    try:
        send_email_alert(lat, lng, maps_link, addr, timestamp)
        email_status = "sent"
    except Exception as e:
        print(f"❌  Email error: {e}")
        email_status = f"failed: {str(e)}"

    alert_id = save_alert(lat, lng, maps_link, addr, timestamp)

    return jsonify({
        "success":    True,
        "alert_id":   alert_id,
        "maps_link":  maps_link,
        "timestamp":  timestamp,
        "email":      email_status,
        "message":    "Emergency alert triggered successfully!"
    })


@app.route("/api/alerts", methods=["GET"])
def get_alerts():
    alerts = fetch_all_alerts()
    return jsonify({"success": True, "alerts": alerts, "count": len(alerts)})


@app.route("/api/alerts/<int:alert_id>", methods=["DELETE"])
def delete_alert(alert_id):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM alerts WHERE id = ?", (alert_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": f"Alert {alert_id} deleted"})


# ─── MAIN ─────────────────────────────────────────────────────────────────────
init_db()

if __name__ == "__main__":
    print("🚀  Smart Emergency Alert System running at http://127.0.0.1:5000")
    app.run(debug=False, host="0.0.0.0", port=5000)
