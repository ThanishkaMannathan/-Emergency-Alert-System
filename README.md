# 🚨 Smart Emergency Alert System

A professional panic-button web application that captures live GPS location, sends an emergency email alert via Gmail SMTP, and stores all alert history in a local SQLite database.

---

## 📁 Project Folder Structure

```
smart-emergency-alert/
├── app.py                    ← Flask backend (main server)
├── init_db.py                ← Standalone DB setup script
├── requirements.txt          ← Python dependencies
├── instance/
│   └── alerts.db             ← SQLite database (auto-created)
├── templates/
│   ├── index.html            ← Panic button page
│   └── history.html          ← Alert history page
└── static/
    ├── css/
    │   ├── style.css         ← Main stylesheet
    │   └── history.css       ← History page styles
    └── js/
        ├── main.js           ← Panic button logic + GPS
        ├── history.js        ← History page logic
        └── grain.js          ← Visual grain effect
```

---

## ⚙️ How Data Flows

```
BROWSER (User presses button)
  │
  ▼
navigator.geolocation.getCurrentPosition()
  │  ← GPS coordinates (lat, lng)
  ▼
fetch("/api/alert", { lat, lng, address })   ← HTTP POST to Flask
  │
  ├──► send_email_alert()  ────────────────► Gmail SMTP → Your inbox
  │                                           (HTML + plain text)
  │
  ├──► save_alert()  ──────────────────────► SQLite Database
  │                                           (lat, lng, time, maps link)
  │
  └──► JSON response back to browser
         ├── alert_id
         ├── maps_link
         ├── timestamp
         └── email status
```

---

## 🛠️ Step-by-Step Setup

### 1. Install Python (if not installed)
Download from https://python.org/downloads  
Make sure to check **"Add Python to PATH"** during installation.

### 2. Open terminal in the project folder
```bash
cd smart-emergency-alert
```

### 3. Create a virtual environment (recommended)
```bash
python -m venv venv

# Activate it:
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### 4. Install dependencies
```bash
pip install -r requirements.txt
```

### 5. Initialise the database (optional – app.py does this automatically)
```bash
python init_db.py
```

### 6. Run the application
```bash
python app.py
```

You should see:
```
✅  Database initialised at .../instance/alerts.db
🚀  Smart Emergency Alert System running at http://127.0.0.1:5000
```

### 7. Open in browser
- **Panic Button:** http://127.0.0.1:5000
- **Alert History:** http://127.0.0.1:5000/history

---

## 📧 Gmail App Password – Explained

Gmail blocks normal password login for scripts. You need an **App Password**.

### What is an App Password?
A 16-character password Google generates specifically for your app. It bypasses 2-step verification for that single app only.

### How to generate one (already done for you):
1. Go to https://myaccount.google.com/security
2. Enable **2-Step Verification**
3. Search for **"App passwords"**
4. Select app → "Mail", device → "Other (custom)"
5. Name it "EmergencyAlert" → Generate
6. Copy the 16-character code

### In this project:
The App Password `wzpa mtuo eisd jiyp` is stored in `app.py`:
```python
SENDER_PASSWORD = "wzpamtuoeisdjiyp"   # spaces removed
```
The spaces in the App Password are cosmetic – remove them before using.

### ⚠️ Security Note for Submission
For a final year project, this is acceptable. In production, use environment variables:
```python
import os
SENDER_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")
```

---

## 📍 How GPS Works in the Browser

```javascript
navigator.geolocation.getCurrentPosition(
  (position) => {
    const lat = position.coords.latitude;   // e.g. 13.0827
    const lng = position.coords.longitude;  // e.g. 80.2707
  },
  (error) => { /* handle denied/unavailable */ },
  { enableHighAccuracy: true, timeout: 10000 }
);
```

- **Requires HTTPS in production** (works on `localhost` without HTTPS)
- Browser shows a permission prompt the first time
- If denied, the app still sends an alert (with 0,0 coordinates)
- Reverse geocoding uses **OpenStreetMap Nominatim** (free, no API key needed)

---

## 🌐 Deployment Options

### Option A: ngrok (Fastest – for demos)

ngrok creates a public HTTPS URL that tunnels to your localhost.

1. Download ngrok from https://ngrok.com/download
2. Sign up for a free account and get your auth token
3. Run your Flask app:  `python app.py`
4. In a new terminal:
   ```bash
   ngrok http 5000
   ```
5. Copy the URL like `https://abc123.ngrok.io`
6. Share this URL – anyone can access your app!

**Note:** GPS works on ngrok URLs because they are HTTPS.

---

### Option B: Render (Free cloud hosting)

1. Push your project to GitHub
2. Go to https://render.com and sign up
3. Click **New → Web Service**
4. Connect your GitHub repo
5. Settings:
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
6. Add environment variables (optional but recommended):
   - `GMAIL_APP_PASSWORD` = your app password
7. Deploy → get a live URL like `https://your-app.onrender.com`

Add gunicorn to requirements:
```
gunicorn>=21.0.0
```

---

## 🔌 API Endpoints

| Method | URL              | Description                    |
|--------|------------------|--------------------------------|
| GET    | `/`              | Panic button page              |
| GET    | `/history`       | Alert history page             |
| POST   | `/api/alert`     | Trigger emergency alert        |
| GET    | `/api/alerts`    | Fetch all alerts (JSON)        |
| DELETE | `/api/alerts/ID` | Delete a specific alert        |

### POST /api/alert – Request body:
```json
{
  "latitude":  13.0827,
  "longitude": 80.2707,
  "address":   "Chennai, Tamil Nadu, India"
}
```

### POST /api/alert – Response:
```json
{
  "success":   true,
  "alert_id":  3,
  "maps_link": "https://www.google.com/maps?q=13.0827,80.2707",
  "timestamp": "28 April 2025, 10:30:45 AM",
  "email":     "sent",
  "message":   "Emergency alert triggered successfully!"
}
```

---

## 🗄️ Database Schema

```sql
CREATE TABLE alerts (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    latitude  REAL    NOT NULL,
    longitude REAL    NOT NULL,
    maps_link TEXT    NOT NULL,
    address   TEXT,
    timestamp TEXT    NOT NULL,
    status    TEXT    DEFAULT 'sent'
);
```

The database file is at `instance/alerts.db` (SQLite – no separate server needed).

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: flask` | Run `pip install -r requirements.txt` |
| Email not received | Check spam folder; verify App Password has no spaces |
| GPS not working | Allow location in browser; use HTTPS or localhost |
| Port 5000 in use | Change `port=5000` to `port=5001` in app.py |
| `smtplib.SMTPAuthenticationError` | Regenerate App Password; ensure 2FA is enabled |

---

## 📋 Features Summary

- ✅ Hold-to-trigger panic button (prevents accidental presses)
- ✅ Live GPS via browser Geolocation API
- ✅ Reverse geocoding (address from coordinates) – free, no API key
- ✅ Google Maps link auto-generated
- ✅ Beautiful HTML email with map link
- ✅ SQLite database storage
- ✅ Alert history page with search & delete
- ✅ No Twilio, no paid APIs
- ✅ Fully offline-capable (except email sending)

---

*Built for final year project submission – Smart Emergency Alert System*
