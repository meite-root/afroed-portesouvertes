const form = document.getElementById("pathwayForm");
const statusEl = document.getElementById("status");
const resultsEl = document.getElementById("results");
const cardsEl = document.getElementById("cards");

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"
  }[c]));
}

function renderCards(payload) {
  const items = payload.pathways || [];
  if (!items.length) {
    cardsEl.innerHTML = "<p>No suggestions returned.</p>";
    resultsEl.style.display = "block";
    return;
  }

  cardsEl.innerHTML = items.map(p => `
    <div style="margin-top:14px; padding:16px; border-radius:14px; border:1px solid rgba(255,255,255,0.10); background: rgba(255,255,255,0.04);">
      <div style="display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap;">
        <strong style="font-size:18px;">${escapeHtml(p.title || "")}</strong>
        <span style="opacity:0.8;">Fit score: ${escapeHtml(p.fit_score ?? "")}/100</span>
      </div>
      <p style="margin:10px 0; opacity:0.9;">${escapeHtml(p.why_this_fits || "")}</p>

      <div style="margin-top:10px;">
        <strong>Typical education</strong>
        <ul>${(p.typical_education_path || []).map(x => `<li>${escapeHtml(x)}</li>`).join("")}</ul>
      </div>

      <div style="margin-top:10px;">
        <strong>Example roles</strong>
        <ul>${(p.example_roles || []).map(x => `<li>${escapeHtml(x)}</li>`).join("")}</ul>
      </div>

      ${p.first_next_step ? `<p style="margin-top:10px;"><strong>First next step:</strong> ${escapeHtml(p.first_next_step)}</p>` : ""}
    </div>
  `).join("");

  resultsEl.style.display = "block";
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const subjects = [
    document.getElementById("s1").value,
    document.getElementById("s2").value,
    document.getElementById("s3").value
  ];

  statusEl.textContent = "Thinking…";
  resultsEl.style.display = "none";
  cardsEl.innerHTML = "";

  try {
    const res = await fetch("/api/pathways", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({ subjects })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Request failed");

    statusEl.textContent = `Suggestions for: ${subjects.join(", ")}`;
    renderCards(data);
  } catch (err) {
    statusEl.textContent = "Error: " + err.message;
  }
});
