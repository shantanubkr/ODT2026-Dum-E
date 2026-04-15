const POLL_MS = 1500;

function el(id) {
  return document.getElementById(id);
}

async function fetchStatus() {
  const r = await fetch("/status");
  if (!r.ok) throw new Error("status failed");
  return r.json();
}

function formatPose(pose) {
  if (pose == null) return "—";
  if (Array.isArray(pose)) return JSON.stringify(pose);
  if (typeof pose === "object") return JSON.stringify(pose);
  return String(pose);
}

function renderStatus(data) {
  el("st-state").textContent = data.state ?? "—";
  el("st-ros").textContent =
    data.ros_state != null && data.ros_state !== "" ? String(data.ros_state) : "—";
  el("st-behavior").textContent = data.behavior ?? "—";
  el("st-pose").textContent = formatPose(data.pose);
  el("st-safety").textContent = data.safety ? JSON.stringify(data.safety) : "—";
  el("st-sim").textContent = String(data.simulation ?? "—");
  const logs = data.recent_logs || [];
  el("logs").textContent = logs.length ? logs.join("\n") : "(no logs)";
}

async function refresh() {
  try {
    const data = await fetchStatus();
    renderStatus(data);
  } catch (e) {
    el("st-state").textContent = "error";
    el("logs").textContent = String(e);
  }
}

async function postCommand(body) {
  const r = await fetch("/command", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  await r.json().catch(() => ({}));
  await refresh();
}

function wireQuickButtons() {
  document.querySelectorAll("[data-quick]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const q = btn.getAttribute("data-quick");
      let body;
      if (q === "home") body = { action: "move_home" };
      else if (q === "stop") body = { action: "stop" };
      else if (q === "reset") body = { action: "reset" };
      else if (q === "hello") body = { action: "greet" };
      else if (q === "ready" || q === "down") body = { text: q };
      await postCommand(body);
    });
  });
}

function wireForm() {
  const input = el("cmd-input");
  const send = el("cmd-send");
  const submit = async () => {
    const text = (input.value || "").trim();
    if (!text) return;
    await postCommand({ text });
    input.value = "";
  };
  send.addEventListener("click", submit);
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") submit();
  });
}

document.addEventListener("DOMContentLoaded", () => {
  wireForm();
  wireQuickButtons();
  refresh();
  setInterval(refresh, POLL_MS);
});
