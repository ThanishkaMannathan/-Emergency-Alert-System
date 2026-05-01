/* ── History Page JS ── */

let allAlerts = [];

async function loadAlerts() {
  try {
    const res  = await fetch("/api/alerts");
    const data = await res.json();
    allAlerts  = data.alerts || [];
    renderAlerts(allAlerts);
    updateStats(allAlerts);
  } catch (err) {
    document.getElementById("alertList").innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">⚠️</div>
        <p>Failed to load alerts. Is the server running?</p>
      </div>`;
  }
}

function updateStats(alerts) {
  document.getElementById("totalCount").textContent = alerts.length;
  const today = new Date().toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" });
  const todayAlerts = alerts.filter(a => a.timestamp && a.timestamp.includes(today.split(" ")[1]));
  // Simpler: count alerts from today's date string
  const todayStr = new Date().toLocaleDateString("en-US", { month: "long", day: "numeric" });
  const todayCnt = alerts.filter(a => a.timestamp && a.timestamp.includes(new Date().getDate() + " ")).length;
  document.getElementById("todayCount").textContent = todayCnt;
}

function renderAlerts(alerts) {
  const list = document.getElementById("alertList");
  if (!alerts.length) {
    list.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">📭</div>
        <p>No alerts recorded yet.<br>Press the panic button to create your first alert.</p>
      </div>`;
    return;
  }

  list.innerHTML = alerts.map((a, i) => `
    <div class="alert-card" id="card-${a.id}" style="animation-delay:${i * 0.04}s">
      <div class="alert-num">${alerts.length - i}</div>
      <div class="alert-info">
        <div class="alert-time">🕒 ${a.timestamp}</div>
        <div class="alert-coords">📍 ${Number(a.latitude).toFixed(6)}, ${Number(a.longitude).toFixed(6)}</div>
        <div class="alert-addr">🏠 ${a.address || 'Address not captured'}</div>
      </div>
      <div class="alert-actions">
        <a class="action-btn" href="${a.maps_link}" target="_blank" title="Open in Maps">🗺️</a>
        <button class="action-btn del" onclick="deleteAlert(${a.id})" title="Delete">🗑️</button>
      </div>
    </div>
  `).join("");
}

async function deleteAlert(id) {
  if (!confirm("Delete this alert record?")) return;
  try {
    await fetch(`/api/alerts/${id}`, { method: "DELETE" });
    allAlerts = allAlerts.filter(a => a.id !== id);
    renderAlerts(allAlerts);
    updateStats(allAlerts);
    showToast("Alert deleted", "success");
  } catch (err) {
    showToast("Delete failed", "error");
  }
}

async function confirmClearAll() {
  if (!allAlerts.length) { showToast("No alerts to clear", ""); return; }
  if (!confirm(`Delete ALL ${allAlerts.length} alert(s)? This cannot be undone.`)) return;
  for (const a of allAlerts) {
    await fetch(`/api/alerts/${a.id}`, { method: "DELETE" });
  }
  allAlerts = [];
  renderAlerts([]);
  updateStats([]);
  showToast("All alerts cleared", "success");
}

// Search filter
document.getElementById("searchInput").addEventListener("input", function () {
  const q = this.value.toLowerCase();
  const filtered = allAlerts.filter(a =>
    (a.timestamp || "").toLowerCase().includes(q) ||
    (a.address   || "").toLowerCase().includes(q) ||
    String(a.latitude).includes(q) ||
    String(a.longitude).includes(q)
  );
  renderAlerts(filtered);
});

function showToast(msg, type) {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.className   = "toast show" + (type ? " " + type : "");
  setTimeout(() => { t.className = "toast"; }, 3000);
}

// Load on page ready
loadAlerts();
