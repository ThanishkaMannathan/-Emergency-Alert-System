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

SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "mannathanthanishka07@gmail.com")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD", "oamn nqwg veka tbzb")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL", "mannathanthanishka07@gmail.com")
DB_PATH = "/tmp/alerts.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            latitude REAL,
            longitude REAL,
            maps_link TEXT,
            address TEXT,
            timestamp TEXT,
            status TEXT DEFAULT 'sent'
        )
    """)
    conn.commit()
    conn.close()


def save_alert(lat, lng, maps_link, address, timestamp):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
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
    msg["Subject"] = "EMERGENCY ALERT - Panic Button Triggered"
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL

    plain_body = "\n".join([
        "EMERGENCY ALERT",
        "===============",
        "Time      : " + timestamp,
        "Latitude  : " + str(lat),
        "Longitude : " + str(lng),
        "Location  : " + (address or "Unknown"),
        "Maps Link : " + maps_link,
        "",
        "This is an automated alert. Please respond immediately."
    ])

    html_body = """<!DOCTYPE html>
<html>
<head><meta charset="UTF-8">
<style>
body { font-family: Arial, sans-serif; background: #111; color: #f0f0f0; margin: 0; padding: 20px; }
.card { max-width: 500px; margin: auto; background: #1a1a1a; border-radius: 12px; overflow: hidden; border: 1px solid #333; }
.top { background: #c0392b; padding: 24px; text-align: center; }
.top h1 { margin: 0; color: white; font-size: 24px; }
.top p { margin: 6px 0 0; color: #ffcccc; font-size: 14px; }
.body { padding: 24px; }
.row { padding: 10px 0; border-bottom: 1px solid #333; display: flex; justify-content: space-between; }
.label { color: #888; font-size: 13px; }
.value { color: #fff; font-size: 13px; font-weight: bold; text-align: right; max-width: 65%; }
.mapbtn { display: block; margin: 20px auto 0; padding: 14px 32px; background: #c0392b; color: white; text-decoration: none; border-radius: 40px; text-align: center; font-weight: bold; }
.foot { padding: 14px; text-align: center; color: #555; font-size: 11px; }
</style>
</head>
<body>
<div class="card">
<div class="top"><h1>EMERGENCY ALERT</h1><p>Panic Button Triggered</p></div>
<div class="body">
<div class="row"><span class="label">Time</span><span class="value">TIME_VAL</span></div>
<div class="row"><span class="label">Latitude</span><span class="value">LAT_VAL</span></div>
<div class="row"><span class="label">Longitude</span><span class="value">LNG_VAL</span></div>
<div class="row"><span class="label">Address</span><span class="value">ADDR_VAL</span></div>
<a href="MAP_URL" class="mapbtn">Open in Google Maps</a>
</div>
<div class="foot">Smart Emergency Alert System</div>
</div>
</body>
</html>""".replace("TIME_VAL", timestamp).replace("LAT_VAL", str(lat)).replace("LNG_VAL", str(lng)).replace("ADDR_VAL", address or "Unknown").replace("MAP_URL", maps_link)

    msg.attach(MIMEText(plain_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
    server.quit()


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
        lat = data.get("latitude", 0)
        lng = data.get("longitude", 0)
        addr = data.get("address", "")
        timestamp = datetime.now().strftime("%d %B %Y, %I:%M:%S %p")
        maps_link = "https://www.google.com/maps?q=" + str(lat) + "," + str(lng)

        try:
            send_email_alert(lat, lng, maps_link, addr, timestamp)
            email_status = "sent"
        except Exception as email_err:
            email_status = "failed: " + str(email_err)

        alert_id = save_alert(lat, lng, maps_link, addr, timestamp)

        return jsonify({
            "success": True,
            "alert_id": alert_id,
            "maps_link": maps_link,
            "timestamp": timestamp,
            "email": email_status,
            "message": "Emergency alert triggered successfully!"
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
