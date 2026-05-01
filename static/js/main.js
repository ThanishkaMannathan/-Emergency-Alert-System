/* ── Smart Emergency Alert System – main.js (GPS Fix) ── */

const HOLD_DURATION = 2500;

const panicBtn     = document.getElementById("panicBtn");
const ringFill     = document.getElementById("ringFill");
const pulseBg      = document.getElementById("pulseBg");
const statusBadge  = document.getElementById("statusBadge");
const gpsStatus    = document.getElementById("gpsStatus");
const emailStatus  = document.getElementById("emailStatus");
const dbStatus     = document.getElementById("dbStatus");
const modalOverlay = document.getElementById("modalOverlay");

const CIRCUMFERENCE = 2 * Math.PI * 88;
ringFill.style.strokeDasharray  = CIRCUMFERENCE;
ringFill.style.strokeDashoffset = CIRCUMFERENCE;

let startTime    = null;
let animFrame    = null;
let isTriggering = false;

// ── Hold interaction ──────────────────────────────────────────
function startHold(e) {
  if (isTriggering) return;
  e.preventDefault();
  panicBtn.classList.add("pressing");
  pulseBg.classList.add("active");
  startTime = Date.now();
  animFrame = requestAnimationFrame(updateRing);
  showToast("Hold for 2 seconds to trigger alert…", "");
}

function endHold() {
  if (isTriggering) return;
  panicBtn.classList.remove("pressing");
  pulseBg.classList.remove("active");
  cancelAnimationFrame(animFrame);
  resetRing();
}

function updateRing() {
  const elapsed  = Date.now() - startTime;
  const progress = Math.min(elapsed / HOLD_DURATION, 1);
  ringFill.style.strokeDashoffset = CIRCUMFERENCE * (1 - progress);
  if (progress >= 1) triggerAlert();
  else animFrame = requestAnimationFrame(updateRing);
}

function resetRing() {
  ringFill.style.strokeDashoffset = CIRCUMFERENCE;
}

panicBtn.addEventListener("mousedown",  startHold);
panicBtn.addEventListener("touchstart", startHold, { passive: false });
window.addEventListener("mouseup",  endHold);
window.addEventListener("touchend", endHold);

// ── GPS — tries up to 3 times for best accuracy ───────────────
function getGPS() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error("Geolocation not supported by this browser"));
      return;
    }

    let attempts = 0;
    const maxAttempts = 3;
    let bestPosition = null;

    function tryGet() {
      attempts++;
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          // Keep the most accurate reading across attempts
          if (!bestPosition || pos.coords.accuracy < bestPosition.coords.accuracy) {
            bestPosition = pos;
          }
          // If accuracy is good enough (within 100m) or we've tried 3 times, use it
          if (bestPosition.coords.accuracy <= 100 || attempts >= maxAttempts) {
            resolve(bestPosition);
          } else {
            // Wait 1 second and try again for better accuracy
            setTimeout(tryGet, 1000);
          }
        },
        (err) => {
          if (attempts < maxAttempts) {
            setTimeout(tryGet, 1000);
          } else if (bestPosition) {
            resolve(bestPosition); // use best we got
          } else {
            reject(err);
          }
        },
        {
          enableHighAccuracy: true,  // Forces GPS chip if available
          timeout: 15000,            // Wait up to 15 sec per attempt
          maximumAge: 0              // Never use cached location
        }
      );
    }

    tryGet();
  });
}

// ── Reverse geocode using Nominatim (free, no API key) ────────
async function reverseGeocode(lat, lng) {
  try {
    const url = `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lng}&format=json&zoom=16&addressdetails=1`;
    const res = await fetch(url, {
      headers: { "Accept-Language": "en-US,en" }
    });
    const data = await res.json();

    if (data && data.address) {
      const a = data.address;
      // Build a clean address: neighbourhood, suburb, city, state
      const parts = [
        a.neighbourhood || a.suburb || a.village || a.hamlet,
        a.city          || a.town   || a.county,
        a.state,
        a.country
      ].filter(Boolean);
      return parts.join(", ");
    }
    return data.display_name || "";
  } catch (e) {
    console.warn("Reverse geocode failed:", e);
    return "";
  }
}

// ── Trigger alert ─────────────────────────────────────────────
async function triggerAlert() {
  if (isTriggering) return;
  isTriggering = true;
  panicBtn.classList.remove("pressing");
  cancelAnimationFrame(animFrame);

  setStatus("alerting", "🔴 LOCATING…");
  setCard("gpsStatus",   "active", "Acquiring GPS… (may take 10s)");
  setCard("emailStatus", "",       "Standby");
  setCard("dbStatus",    "",       "Standby");

  let lat, lng, address = "";

  try {
    const pos = await getGPS();
    lat = pos.coords.latitude;
    lng = pos.coords.longitude;
    const accuracy = Math.round(pos.coords.accuracy);

    setCard("gpsStatus", "done", `${lat.toFixed(6)}, ${lng.toFixed(6)} (±${accuracy}m)`);
    setStatus("alerting", "🔴 RESOLVING ADDRESS…");

    // Get real address from coordinates
    address = await reverseGeocode(lat, lng);
    if (address) {
      setCard("gpsStatus", "done", address);
    }

  } catch (err) {
    lat = 0; lng = 0;
    address = "GPS unavailable – location permission denied";
    setCard("gpsStatus", "active", "GPS denied – sending alert anyway");
    showToast("⚠️ Allow location access for accurate GPS", "error");
  }

  setStatus("alerting", "🔴 SENDING ALERT…");
  setCard("emailStatus", "active", "Sending email…");
  setCard("dbStatus",    "active", "Saving…");

  try {
    const res = await fetch("/api/alert", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ latitude: lat, longitude: lng, address })
    });
    const data = await res.json();

    if (data.success) {
      setCard("emailStatus", "done", data.email === "sent" ? "Delivered ✓" : "Check server logs");
      setCard("dbStatus",    "done", `Alert #${data.alert_id} saved`);
      setStatus("success", "✅ ALERT SENT");
      pulseBg.classList.remove("active");
      showModal(true, lat, lng, data, address);
    } else {
      throw new Error(data.message);
    }
  } catch (err) {
    setCard("emailStatus", "", "Failed");
    setCard("dbStatus",    "", "Failed");
    setStatus("error", "⚠️ ERROR");
    showToast("❌ " + err.message, "error");
  }

  isTriggering = false;
  setTimeout(() => {
    resetRing();
    setStatus("ready", "● SYSTEM READY");
  }, 6000);
}

// ── Helpers ───────────────────────────────────────────────────
function setStatus(type, text) {
  statusBadge.className = "status-badge " + type;
  statusBadge.innerHTML = `<span class="dot"></span> ${text}`;
}

function setCard(elemId, cls, text) {
  const span = document.getElementById(elemId);
  const card = span.closest(".card");
  card.className = "card" + (cls ? " " + cls : "");
  span.textContent = text;
}

function showToast(msg, type) {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.className   = "toast show" + (type ? " " + type : "");
  setTimeout(() => { t.className = "toast"; }, 4000);
}

function showModal(success, lat, lng, data, address) {
  document.getElementById("modalIcon").textContent  = "🚨";
  document.getElementById("modalTitle").textContent = "Alert Sent!";
  document.getElementById("modalMsg").textContent   =
    "Your emergency alert has been dispatched. Help is on the way.";

  document.getElementById("modalMeta").innerHTML = `
    <strong>📍 Location:</strong> ${address || "Unknown"}<br>
    <strong>🌐 Coordinates:</strong> ${lat.toFixed(6)}, ${lng.toFixed(6)}<br>
    <strong>🕒 Time:</strong> ${data.timestamp}<br>
    <strong>✉️ Email:</strong> ${data.email === "sent" ? "Delivered ✓" : data.email}<br>
    <strong>🗄️ Alert ID:</strong> #${data.alert_id}
  `;

  const ml = document.getElementById("mapsLink");
  ml.href = data.maps_link;
  modalOverlay.classList.add("open");
}

function closeModal() {
  modalOverlay.classList.remove("open");
}
modalOverlay.addEventListener("click", e => {
  if (e.target === modalOverlay) closeModal();
});
