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

SENDER_EMAIL    = os.environ.get("SENDER_EMAIL",    "mannathanthanishka07@gmail.com")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD", "paxn gnke ssem kghx")
RECEIVER_EMAIL  = os.environ.get("RECEIVER_EMAIL",  "mannathanthanishka07@gmail.com")
DB_PATH         = "/tmp/alerts.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            latitude  REAL,
            longitude REAL,
            maps_link TEXT,
            address   TEXT,
            timestamp TEXT,
            status    TEXT DEFAULT 'sent'
        )
    """)
    conn.commit()
    conn.close()

def save_alert(lat, lng, maps_link, address, timestamp):
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute(
        "INSERT INTO alerts (latitude,longitude,maps_link,address,timestamp) VALUES (?,?,?,?,?)",
        (lat, lng, maps_link, address, timestamp)
    )
    conn.commit()
    aid = cur.lastrowid
    conn.close()
    return aid

def fetch_all_alerts():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM alerts ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def send_email_alert(lat, lng, maps_link, address, timestamp):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "🚨 EMERGENCY ALERT – Panic Button Triggered"
    msg["From"]    = SENDER_EMAIL
    msg["To"]      = RECEIVER_EMAIL
    plain = f"""
EMERGENCY ALERT
===============
Time      : {timestamp}
Latitude  : {lat}
Longitude : {lng}
Location  : {address or 'Unknown'}
Maps Link : {maps_link}
This is an automated alert. Please respond immediately.
"""
    html = f"""
<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
body{{font-family:Arial,sans-serif;background:#0a0a0a;color:#f0f0f0;margin:0;padding:0}}
.wrap{{max-width:600px;margin:40px auto;background:#111;border-radius:16px;overflow:hidden;border:1px solid #333}}
.hdr{{background:linear-gradient(135deg,#c0392b,#e74c3c);padding:32px;text-align:center}}
.hdr h1{{margin:0;font-size:28px;color:#fff;letter-spacing:2px}}
.ico{{font-size:52px;margin-bottom:12px;display:block}}
.bdy{{padding:32px}}
.row{{display:flex;justify-content:space-between;padding:12px 0;border-bottom:1px solid #222}}
.lbl{{color:#888;font-size:13px;text-transform:uppercase;letter-spacing:1px}}
.val{{color:#f0f0f0;font-size:14px;font-weight:600;text-align:right;max-width:70%}}
.btn{{display:block;margin:28px auto 0;padding:16px 36px;background:linear-gradient(135deg,#c0392b,#e74c3c);color:#fff;font-size:16px;font-weight:700;text-decoration:none;border-radius:50px;text-align:center}}
.ftr{{background:#0d0d0d;padding:16px;text-align:center;color:#555;font-size:12px}}
</style></head><body>
<div class="wrap">
<div class="hdr"><span class="ico">🚨</span><h1>EMERGENCY ALERT</h1>
<p style="margin:8px 0 0;color:#ffcccc;font-size:14px">Panic Button Triggered</p></div>
<div class="bdy">
<div class="row"><span class="lbl">⏰ Time</span><span class="val">{timestamp}</span></div>
<div class="row"><span class="lbl">📍 Latitude</span><span class="val">{lat}</span></div>
<div class="row"><span class="lbl">📍 Longitude</span><span class="val">{lng}</span></div>
<div class="row"><span class="lbl">🏠 Address</span><span class="val">{address or 'Unknown'}</span></div>
<a href="{maps_link}" class="btn">📌 Open in Google Maps</a>
</div>
<div class="ftr">Smart Emergency Alert System | Automated Notification</div>
</div></body></html>
"""
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html,  "html"))
   with smtplib.SMTP("smtp.gmail.com", 587) as s:
        s.ehlo()
        s.starttls()
        s.login(SENDER_EMAIL, SENDER_PASSWORD)
        s.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/history")
def history():
    return render_template("history.html")

@app.route("/api/alert", methods=["POST"])
def trigger_alert():
    try:
        data = request.get_json(force=True)
        lat  = data.get("latitude",  0)
        lng  = data.get("longitude", 0)
        addr = data.get("address",   "")
        timestamp = datetime.now().strftime("%d %B %Y, %I:%M:%S %p")
        maps_link = f"https://www.google.com/maps?q={lat},{lng}"
        try:
            send_email_alert(lat, lng, maps_link, addr, timestamp)
            email_status = "sent"
        except Exception as e:
            email_status = f"failed: {str(e)}"
        alert_id = save_alert(lat, lng, maps_link, addr, timestamp)
        return jsonify({
            "success":   True,
            "alert_id":  alert_id,
            "maps_link": maps_link,
            "timestamp": timestamp,
            "email":     email_status,
            "message":   "Emergency alert triggered successfully!"
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/alerts", methods=["GET"])
def get_alerts():
    try:
        alerts = fetch_all_alerts()
        return jsonify({"success": True, "alerts": alerts, "count": len(alerts)})
    except Exception as e:
        return jsonify({"success": False, "alerts": [], "message": str(e)})

@app.route("/api/alerts/<int:alert_id>", methods=["DELETE"])
def delete_alert(alert_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("DELETE FROM alerts WHERE id=?", (alert_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

init_db()

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
