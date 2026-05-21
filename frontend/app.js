const API_BASE = window.location.port === "8000" ? "" : "/api";
const AUTH_KEY = "paytrend.auth";
let currentAuth = readAuth();

const currency = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0
});

const compactCurrency = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  notation: "compact",
  maximumFractionDigits: 1
});

function setText(id, value) {
  document.getElementById(id).textContent = value;
}

function readAuth() {
  try {
    return JSON.parse(localStorage.getItem(AUTH_KEY));
  } catch (error) {
    return null;
  }
}

function saveAuth(auth) {
  currentAuth = auth;
  localStorage.setItem(AUTH_KEY, JSON.stringify(auth));
}

function clearAuth() {
  currentAuth = null;
  localStorage.removeItem(AUTH_KEY);
}

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

function formatDate(value) {
  return new Intl.DateTimeFormat("en-IN", { day: "2-digit", month: "short", year: "numeric" }).format(new Date(value));
}

function updateStatus(text, className) {
  const status = document.getElementById("apiStatus");
  status.className = `status-pill ${className}`;
  status.textContent = text;
}

async function loadJson(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (currentAuth?.token) {
    headers.Authorization = `Bearer ${currentAuth.token}`;
  }
  const response = await fetch(`${API_BASE}${path}`, {
    headers,
    ...options
  });
  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    const error = new Error(errorBody.detail || `Request failed: ${path}`);
    error.status = response.status;
    throw error;
  }
  if (response.status === 204) return null;
  return response.json();
}

function drawLineChart(canvasId, points, options = {}) {
  const canvas = document.getElementById(canvasId);
  const ctx = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  const padding = { top: 26, right: 24, bottom: 46, left: 58 };
  const values = points.map((point) => point.value);
  const max = Math.max(...values, 1) * 1.12;
  const min = Math.min(0, ...values);
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;

  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, width, height);

  const plotBg = ctx.createLinearGradient(0, padding.top, 0, height - padding.bottom);
  plotBg.addColorStop(0, "rgba(37, 99, 235, 0.035)");
  plotBg.addColorStop(1, "rgba(15, 159, 110, 0.025)");
  ctx.fillStyle = plotBg;
  ctx.fillRect(padding.left, padding.top, plotWidth, plotHeight);

  ctx.strokeStyle = "#d8e0e8";
  ctx.lineWidth = 1;
  ctx.fillStyle = "#6b7785";
  ctx.font = "13px Inter, system-ui, sans-serif";

  for (let i = 0; i < 4; i += 1) {
    const y = padding.top + (plotHeight / 3) * i;
    ctx.beginPath();
    ctx.moveTo(padding.left, y);
    ctx.lineTo(width - padding.right, y);
    ctx.stroke();
  }

  const coords = points.map((point, index) => {
    const x = padding.left + (plotWidth / Math.max(points.length - 1, 1)) * index;
    const y = padding.top + plotHeight - ((point.value - min) / (max - min)) * plotHeight;
    return { ...point, x, y };
  });

  if (!coords.length) return;

  const gradient = ctx.createLinearGradient(0, padding.top, 0, height - padding.bottom);
  gradient.addColorStop(0, "rgba(37, 99, 235, 0.22)");
  gradient.addColorStop(1, "rgba(37, 99, 235, 0)");

  ctx.beginPath();
  coords.forEach((point, index) => {
    if (index === 0) ctx.moveTo(point.x, point.y);
    else ctx.lineTo(point.x, point.y);
  });
  ctx.lineTo(coords[coords.length - 1].x, height - padding.bottom);
  ctx.lineTo(coords[0].x, height - padding.bottom);
  ctx.closePath();
  ctx.fillStyle = gradient;
  ctx.fill();

  ctx.beginPath();
  coords.forEach((point, index) => {
    if (index === 0) ctx.moveTo(point.x, point.y);
    else ctx.lineTo(point.x, point.y);
  });
  ctx.strokeStyle = options.color || "#2563eb";
  ctx.lineWidth = 4;
  ctx.lineJoin = "round";
  ctx.stroke();

  coords.forEach((point) => {
    if (point.projected) {
      ctx.setLineDash([6, 6]);
      ctx.strokeStyle = "#0f9f6e";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(point.x, padding.top);
      ctx.lineTo(point.x, height - padding.bottom);
      ctx.stroke();
      ctx.setLineDash([]);
    }
    ctx.beginPath();
    ctx.arc(point.x, point.y, point.projected ? 4 : 5, 0, Math.PI * 2);
    ctx.fillStyle = point.projected ? "#ffffff" : options.color || "#2563eb";
    ctx.strokeStyle = point.projected ? "#0f9f6e" : "#ffffff";
    ctx.lineWidth = 3;
    ctx.fill();
    ctx.stroke();
  });

  const labelEvery = points.length > 12 ? 3 : 2;
  coords.forEach((point, index) => {
    if (index % labelEvery !== 0 && index !== coords.length - 1) return;
    ctx.fillStyle = "#6b7785";
    ctx.textAlign = "center";
    ctx.fillText(point.label.split(" ")[0], point.x, height - 18);
  });

  ctx.textAlign = "left";
  ctx.fillStyle = "#6b7785";
  ctx.fillText(compactCurrency.format(max), 8, padding.top + 6);
}

function renderBars(id, items) {
  const target = document.getElementById(id);
  const max = Math.max(...items.map((item) => item.value), 1);
  target.innerHTML = items.map((item) => {
    const width = Math.max(6, (item.value / max) * 100);
    return `
      <div class="bar-row">
        <div class="bar-meta">
          <strong>${item.label}</strong>
          <span>${compactCurrency.format(item.value)}</span>
        </div>
        <div class="bar-track"><div class="bar-fill" style="width: ${width}%"></div></div>
      </div>
    `;
  }).join("");
}

function renderRegions(items) {
  document.getElementById("regionMix").innerHTML = items.map((item) => `
    <div class="region-card">
      <span>${item.label}</span>
      <strong>${compactCurrency.format(item.value)}</strong>
    </div>
  `).join("");
}

function renderTransactions(rows) {
  document.getElementById("transactionRows").innerHTML = rows.map((row) => `
    <tr>
      <td>${formatDate(row.date)}</td>
      <td>${row.merchant}</td>
      <td>${row.category}</td>
      <td>${row.method}</td>
      <td>${row.region}</td>
      <td>${currency.format(row.amount)}</td>
    </tr>
  `).join("");
}

function render(summary, forecast) {
  setText("workspaceName", `${currentAuth.user.name}'s Workspace`);
  setText("totalVolume", compactCurrency.format(summary.total_volume));
  setText("transactionCount", summary.transaction_count.toLocaleString("en-IN"));
  setText("averageTransaction", compactCurrency.format(summary.average_transaction));
  setText("cagr", `${summary.cagr}%`);
  setText("heroVolume", compactCurrency.format(summary.total_volume));
  setText("heroGrowth", `${summary.cagr}%`);
  setText("heroRecords", summary.transaction_count.toLocaleString("en-IN"));
  setText("projectedGrowth", `${forecast.projected_growth}% projected`);
  setText("lastUpdated", `Live data refreshed ${new Date().toLocaleTimeString("en-IN")}`);
  if (summary.monthly_volume.length) {
    const first = summary.monthly_volume[0].label;
    const last = summary.monthly_volume[summary.monthly_volume.length - 1].label;
    setText("trendScope", `${first} - ${last}`);
  }

  drawLineChart("monthlyChart", summary.monthly_volume, { color: "#2563eb" });
  drawLineChart("forecastChart", forecast.series, { color: "#0f9f6e" });
  renderBars("methodMix", summary.method_mix);
  renderBars("categoryMix", summary.category_mix);
  renderRegions(summary.region_mix);
  renderTransactions(summary.recent_transactions);
}

function showAuth() {
  document.getElementById("authScreen").classList.remove("hidden");
  document.getElementById("appShell").classList.add("hidden");
}

function showApp() {
  document.getElementById("authScreen").classList.add("hidden");
  document.getElementById("appShell").classList.remove("hidden");
}

function switchAuthMode(mode) {
  const signingIn = mode === "signin";
  document.getElementById("signinForm").classList.toggle("hidden", !signingIn);
  document.getElementById("signupForm").classList.toggle("hidden", signingIn);
  document.getElementById("signinTab").classList.toggle("active", signingIn);
  document.getElementById("signupTab").classList.toggle("active", !signingIn);
  document.getElementById("authStatus").textContent = signingIn
    ? "Use demo@paytrend.local / password123 to open the seeded demo workspace."
    : "Create an account to start with a separate empty workspace.";
}

async function submitAuth(path, form) {
  const authStatus = document.getElementById("authStatus");
  const button = form.querySelector("button");
  const payload = Object.fromEntries(new FormData(form).entries());
  authStatus.textContent = "Checking account...";
  button.disabled = true;
  try {
    const auth = await loadJson(path, {
      method: "POST",
      body: JSON.stringify(payload)
    });
    saveAuth(auth);
    form.reset();
    showApp();
    await refreshDashboard();
  } catch (error) {
    authStatus.textContent = error.message || "Authentication failed";
  } finally {
    button.disabled = false;
  }
}

function wireAuth() {
  document.getElementById("signinTab").addEventListener("click", () => switchAuthMode("signin"));
  document.getElementById("signupTab").addEventListener("click", () => switchAuthMode("signup"));
  document.getElementById("signinForm").addEventListener("submit", (event) => {
    event.preventDefault();
    submitAuth("/auth/signin", event.currentTarget);
  });
  document.getElementById("signupForm").addEventListener("submit", (event) => {
    event.preventDefault();
    submitAuth("/auth/signup", event.currentTarget);
  });
  document.getElementById("signoutButton").addEventListener("click", async () => {
    await loadJson("/auth/signout", { method: "POST" }).catch(() => null);
    clearAuth();
    showAuth();
  });
}

async function refreshDashboard() {
  if (!currentAuth?.token) {
    showAuth();
    return;
  }
  updateStatus("Syncing", "");
  try {
    const [summary, forecast] = await Promise.all([
      loadJson("/analytics/summary"),
      loadJson("/forecasting/growth?horizon_months=6")
    ]);
    updateStatus("Live Data", "online");
    render(summary, forecast);
  } catch (error) {
    if (error.status === 401) {
      clearAuth();
      showAuth();
      document.getElementById("authStatus").textContent = "Please sign in again.";
      return;
    }
    throw error;
  }
}

async function addTransaction(payload) {
  return loadJson("/transactions", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

function wireForm() {
  const form = document.getElementById("transactionForm");
  const formStatus = document.getElementById("formStatus");
  form.elements.date.value = todayIso();

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    formStatus.textContent = "Saving...";
    form.querySelector("button").disabled = true;
    const formData = new FormData(form);
    const payload = Object.fromEntries(formData.entries());
    payload.amount = Number(payload.amount);
    try {
      await addTransaction(payload);
      formStatus.textContent = "Saved";
      await refreshDashboard();
    } catch (error) {
      formStatus.textContent = "Save failed";
      updateStatus("API Error", "offline");
    } finally {
      form.querySelector("button").disabled = false;
    }
  });
}

async function boot() {
  wireAuth();
  wireForm();

  if (!currentAuth?.token) {
    showAuth();
  } else {
    try {
      const user = await loadJson("/auth/me");
      currentAuth.user = user;
      saveAuth(currentAuth);
      showApp();
      await refreshDashboard();
    } catch (error) {
      if (error.status === 401) {
        clearAuth();
        showAuth();
      } else {
        showApp();
        updateStatus("API Offline", "offline");
        setText("lastUpdated", "Backend is not reachable");
      }
    }
  }

  setInterval(() => {
    if (currentAuth?.token) {
      refreshDashboard().catch(() => updateStatus("API Offline", "offline"));
    }
  }, 10000);
}

boot();
