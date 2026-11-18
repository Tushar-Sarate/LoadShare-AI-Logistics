// Orders near the partner, with an Accept button.
// Longer trips pay more, so the best paying order is listed first.

function rs(n) {
  return "Rs " + parseFloat(n || 0).toFixed(0);
}

function availCard(o) {
  const longTrip = o.trip_km >= 10;
  return `
    <div class="order">
      <div class="order-top">
        <div><b>${esc(o.restaurant_name || "Parcel")}</b>
          <div class="muted">${esc(o.order_number)}</div></div>
        <span class="pill ${longTrip ? "done" : "pending"}">${longTrip ? "Long trip" : "Short trip"}</span>
      </div>
      <div class="route">
        <div><small>PICK UP</small><p>${esc(o.pickup_address)}</p></div>
        <div class="arrow">➜</div>
        <div><small>DELIVER TO</small><p>${esc(o.delivery_address)}</p></div>
      </div>
      <div class="eta">🛵 ${o.pickup_km} km to pickup · ${o.trip_km} km trip · about ${esc(o.eta_minutes ?? "-")} min</div>
      <div class="order-foot">
        <div><b>You earn ${rs(o.earn)}</b>
          <span class="muted"> · Order value ${rs(o.order_value)}
          ${o.payment_method === "COD" ? " · 💵 cash on delivery" : ""}</span></div>
        <button class="btn" onclick="acceptOrder(${o.id})">Accept</button>
      </div>
    </div>`;
}

async function loadAvailable() {
  // only on the partner screen
  const active = document.getElementById("active");
  if (!active) return;

  let box = document.getElementById("avail");

  if (!box) {
    const grid = active.closest(".grid2");
    if (!grid) return;
    const card = document.createElement("div");
    card.className = "card";
    card.innerHTML = `<h2>🆕 Orders near you</h2>
      <p class="muted" style="margin-bottom:10px">Longer trips pay more: Rs 20 for the first 2 km, then Rs 7 per km.</p>
      <div id="avail"></div>`;
    grid.parentNode.insertBefore(card, grid);
    box = document.getElementById("avail");
  }

  try {
    const rows = await api("/orders/available");
    box.innerHTML = rows.length
      ? rows.map(availCard).join("")
      : `<div class="empty">No new orders within 20 km right now. This list refreshes every 10 seconds.</div>`;
  } catch (e) { /* ignore refresh errors */ }
}

async function acceptOrder(id) {
  try {
    await api(`/orders/${id}/accept`, "POST");
    toast("Order accepted. Head to the pickup.");
    loadAvailable();
    if (typeof loadPartnerOrders === "function") loadPartnerOrders();
  } catch (e) {
    toast(e.message, "error");
    loadAvailable();
  }
}

setInterval(loadAvailable, 10000);
setTimeout(loadAvailable, 1500);