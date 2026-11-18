const API = "";

function getToken() {
  return localStorage.getItem("token");
}

function setToken(token) {
  localStorage.setItem("token", token);
}

function logout() {
  localStorage.removeItem("token");
  window.location.href = "index.html";
}

function requireLogin() {
  if (!getToken()) {
    window.location.href = "login.html";
  }
}

// Escape text before putting it into HTML
function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

// Small popup message
function toast(message, type = "ok") {
  const t = document.getElementById("toast");
  if (!t) return;
  t.textContent = message;
  t.className = "show " + (type === "error" ? "error" : "");
  setTimeout(() => (t.className = ""), 2800);
}

// Call any API endpoint
async function api(path, method = "GET", body = null) {
  const headers = { "Content-Type": "application/json" };

  if (getToken()) {
    headers["Authorization"] = "Bearer " + getToken();
  }

  const response = await fetch(API + path, {
    method: method,
    headers: headers,
    body: body ? JSON.stringify(body) : null,
  });

  const data = await response.json().catch(() => ({}));

  if (response.status === 401 && path !== "/auth/login") {
    logout();
  }

  if (!response.ok) {
    let message = "Something went wrong";
    if (typeof data.detail === "string") {
      message = data.detail;
    } else if (Array.isArray(data.detail)) {
      message = data.detail.map((e) => e.msg).join(", ");
    }
    throw new Error(message);
  }

  return data;
}