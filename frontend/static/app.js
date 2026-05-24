/* ============================================
   Pickleball HQ — frontend logic
   ============================================ */

const $ = (s, root = document) => root.querySelector(s);
const $$ = (s, root = document) => [...root.querySelectorAll(s)];

const api = {
  async get(path) {
    const r = await fetch(path);
    return r.json();
  },
  async post(path, data, isForm = false) {
    const opts = { method: "POST" };
    if (isForm) {
      opts.body = data;
    } else {
      opts.headers = { "Content-Type": "application/json" };
      opts.body = JSON.stringify(data);
    }
    return fetch(path, opts);
  },
  async patch(path, data) {
    return fetch(path, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
  },
  async del(path) {
    return fetch(path, { method: "DELETE" });
  },
};

function toast(msg, isError = false) {
  const el = document.createElement("div");
  el.className = "toast" + (isError ? " error" : "");
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 3200);
}

function fmtDate(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

/* ---------- Tabs ---------- */
$$(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    $$(".tab").forEach((t) => t.classList.remove("active"));
    $$(".panel").forEach((p) => p.classList.remove("active"));
    tab.classList.add("active");
    $(`#panel-${tab.dataset.tab}`).classList.add("active");
  });
});

/* ---------- AI Status ---------- */
async function checkAIStatus() {
  const status = $("#ai-status");
  const text = $(".ai-status-text", status);
  try {
    const r = await api.get("/api/ai/status");
    if (r.connected) {
      status.classList.add("online");
      status.classList.remove("offline");
      text.textContent = "AI online";
    } else {
      status.classList.add("offline");
      status.classList.remove("online");
      text.textContent = "LM Studio offline";
    }
  } catch {
    status.classList.add("offline");
    text.textContent = "AI offline";
  }
}

/* ============================================
   GEAR
   ============================================ */
async function loadGear() {
  const items = await api.get("/api/gear");
  const list = $("#gear-list");
  if (!items.length) {
    list.innerHTML = `<div class="empty-state">// no gear logged yet</div>`;
    return;
  }
  list.innerHTML = items
    .map(
      (g) => `
    <div class="gear-card">
      <div class="gear-photo ${g.photo_url ? "" : "empty"}" ${g.photo_url ? `style="background-image:url('${g.photo_url}')"` : ""}>
        ${g.photo_url ? "" : "◆"}
        <span class="gear-cat">${g.category}</span>
      </div>
      <div class="gear-body">
        <div class="gear-brand">${g.brand || "—"}</div>
        <div class="gear-name">${g.name}</div>
        ${g.specs ? `<div class="gear-specs">${g.specs}</div>` : ""}
        ${g.notes ? `<div class="gear-notes">${g.notes}</div>` : ""}
        <div class="gear-footer">
          <span>${g.started_using || "—"}</span>
          <button class="btn danger small" data-del-gear="${g.id}">remove</button>
        </div>
      </div>
    </div>
  `
    )
    .join("");

  $$("[data-del-gear]").forEach((b) =>
    b.addEventListener("click", async () => {
      if (!confirm("Remove this gear?")) return;
      await api.del(`/api/gear/${b.dataset.delGear}`);
      toast("Removed");
      loadGear();
    })
  );
}

$("#gear-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const r = await api.post("/api/gear", fd, true);
  if (r.ok) {
    toast("Added to bag");
    e.target.reset();
    loadGear();
  } else {
    toast("Failed to add", true);
  }
});

/* ============================================
   FILM ROOM
   ============================================ */
async function loadFilms() {
  const films = await api.get("/api/films");
  const list = $("#film-list");
  if (!films.length) {
    list.innerHTML = `<div class="empty-state">// no film uploaded yet</div>`;
    return;
  }
  list.innerHTML = films
    .map((f) => `
      <div class="film-card" data-film="${f.id}">
        <div class="film-header">
          <div>
            <div class="film-title">${f.title}</div>
            <div class="post-meta">${fmtDate(f.created_at)}</div>
          </div>
          <button class="btn danger small" data-del-film="${f.id}">delete</button>
        </div>
        ${f.context ? `<div class="film-context">${f.context}</div>` : ""}
        <video class="film-video" controls src="${f.video_url}"></video>

        <div class="notes-section">
          <h3 class="section-title">Timestamped notes</h3>
          <div class="note-form" data-note-form="${f.id}">
            <input type="text" placeholder="0:00" data-time pattern="[0-9]+:[0-5][0-9]" />
            <input type="text" placeholder="What happened…" data-text />
            <select data-tag>
              <option value="general">General</option>
              <option value="error">Error</option>
              <option value="opportunity">Opportunity</option>
              <option value="win">Win</option>
            </select>
            <button class="btn ghost small" data-add-note="${f.id}">add</button>
          </div>
          <div class="note-list" data-notes="${f.id}">
            ${(f.notes || []).map(n => `
              <div class="note-item tag-${n.tag}">
                <span class="note-time">${n.timestamp}</span>
                <span class="note-tag">${n.tag}</span>
                <span>${n.text}</span>
              </div>
            `).join("")}
          </div>
        </div>

        <div style="margin-top: 1.25rem">
          <button class="btn primary" data-analyze="${f.id}">Generate AI breakdown</button>
        </div>
        ${f.ai_summary ? `
          <div class="ai-summary">
            <div class="ai-summary-head">◆ AI Breakdown — ${fmtDate(f.ai_summary.generated_at)}</div>
            ${f.ai_summary.text}
          </div>
        ` : ""}
      </div>
    `).join("");

  $$("[data-del-film]").forEach((b) =>
    b.addEventListener("click", async () => {
      if (!confirm("Delete this film and its video file?")) return;
      await api.del(`/api/films/${b.dataset.delFilm}`);
      toast("Film deleted");
      loadFilms();
    })
  );

  $$("[data-add-note]").forEach((b) =>
    b.addEventListener("click", async () => {
      const id = b.dataset.addNote;
      const form = $(`[data-note-form="${id}"]`);
      const timestamp = $("[data-time]", form).value.trim() || "0:00";
      const text = $("[data-text]", form).value.trim();
      const tag = $("[data-tag]", form).value;
      if (!text) return toast("Add a note first", true);
      await api.post(`/api/films/${id}/notes`, { timestamp, text, tag });
      $("[data-text]", form).value = "";
      $("[data-time]", form).value = "";
      loadFilms();
    })
  );

  $$("[data-analyze]").forEach((b) =>
    b.addEventListener("click", async () => {
      const id = b.dataset.analyze;
      b.textContent = "Analyzing…";
      b.disabled = true;
      try {
        const r = await fetch(`/api/films/${id}/analyze`, { method: "POST" });
        const data = await r.json();
        if (!r.ok) {
          toast(data.error || "Analysis failed", true);
        } else {
          toast("Breakdown ready");
          loadFilms();
        }
      } catch (e) {
        toast("Request failed", true);
      } finally {
        b.disabled = false;
        b.textContent = "Generate AI breakdown";
      }
    })
  );
}

$("#film-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const btn = e.target.querySelector("button[type=submit]");
  btn.disabled = true;
  btn.textContent = "Uploading…";
  try {
    const r = await api.post("/api/films", fd, true);
    if (r.ok) {
      toast("Film uploaded");
      e.target.reset();
      loadFilms();
    } else {
      toast("Upload failed", true);
    }
  } finally {
    btn.disabled = false;
    btn.textContent = "Upload film";
  }
});

/* ============================================
   CALENDAR
   ============================================ */
async function loadCalendar() {
  const cal = await api.get("/api/calendar");
  $("#target-name").value = cal.target_name || "";
  $("#target-date").value = cal.target_date || "";

  // Countdown
  const cd = $("#countdown-display");
  if (cal.target_date) {
    const target = new Date(cal.target_date);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const days = Math.ceil((target - today) / (1000 * 60 * 60 * 24));
    cd.innerHTML = `
      <div class="countdown-num">${days >= 0 ? days : "—"}</div>
      <div class="countdown-label">${days > 1 ? "days until" : days === 1 ? "day until" : days === 0 ? "today is" : "days since"}</div>
      ${cal.target_name ? `<div class="countdown-target">${cal.target_name}</div>` : ""}
    `;
  } else {
    cd.innerHTML = `<div class="countdown-num">—</div><div class="countdown-label">set your target</div>`;
  }

  // Posts
  const list = $("#post-list");
  const posts = (cal.posts || []).sort((a, b) => (a.date || "").localeCompare(b.date || ""));
  if (!posts.length) {
    list.innerHTML = `<div class="empty-state">// no posts planned yet</div>`;
  } else {
    list.innerHTML = posts.map(p => `
      <div class="post-card">
        <div class="post-date">${p.date ? fmtDate(p.date) : "—"}</div>
        <div>
          <div class="post-topic">${p.topic}</div>
          <div class="post-meta">${p.platform} · ${p.format} · ${p.post_type}</div>
          ${p.notes ? `<div class="gear-notes" style="margin-top:0.4rem">${p.notes}</div>` : ""}
        </div>
        <select data-status="${p.id}" class="post-status status-${p.status}">
          ${["planned", "filmed", "edited", "posted"].map(s => `<option value="${s}" ${s === p.status ? "selected" : ""}>${s}</option>`).join("")}
        </select>
        <button class="btn danger small" data-del-post="${p.id}">×</button>
      </div>
    `).join("");

    $$("[data-status]").forEach(sel =>
      sel.addEventListener("change", async (e) => {
        await api.patch(`/api/calendar/posts/${sel.dataset.status}`, { status: e.target.value });
        loadCalendar();
      })
    );

    $$("[data-del-post]").forEach(b =>
      b.addEventListener("click", async () => {
        await api.del(`/api/calendar/posts/${b.dataset.delPost}`);
        toast("Removed");
        loadCalendar();
      })
    );
  }

  // Split meter
  const tips = posts.filter(p => p.post_type === "tip").length;
  const highlights = posts.filter(p => p.post_type === "highlight").length;
  const total = tips + highlights;
  const tipsPct = total ? Math.round((tips / total) * 100) : 0;
  const hlPct = total ? 100 - tipsPct : 0;

  $("#split-meter").innerHTML = `
    <div class="split-half">
      <div class="split-fill" style="transform: scaleX(${tipsPct / 100})"></div>
      <span class="split-label">Tips · target 70%</span>
      <span class="split-pct">${tipsPct}%</span>
    </div>
    <div class="split-half highlight">
      <div class="split-fill" style="transform: scaleX(${hlPct / 100})"></div>
      <span class="split-label">Highlights · target 30%</span>
      <span class="split-pct">${hlPct}%</span>
    </div>
  `;
}

$("#save-target").addEventListener("click", async () => {
  await api.post("/api/calendar/target", {
    target_date: $("#target-date").value,
    target_name: $("#target-name").value,
  });
  toast("Target locked");
  loadCalendar();
});

$("#post-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const data = Object.fromEntries(fd);
  const r = await api.post("/api/calendar/posts", data);
  if (r.ok) {
    toast("Post planned");
    e.target.reset();
    loadCalendar();
  }
});

/* ============================================
   ANALYTICS
   ============================================ */
async function loadAnalytics() {
  const entries = await api.get("/api/analytics");
  const insights = await api.get("/api/analytics/insights");
  const list = $("#analytics-list");
  const insightsEl = $("#insights");

  if (insights.empty) {
    insightsEl.innerHTML = `<div class="empty-state">// log a post to see insights</div>`;
  } else {
    const t = insights.totals;
    const renderBars = (obj, label) => {
      const items = Object.entries(obj).sort((a, b) => b[1].avg_views - a[1].avg_views);
      const max = Math.max(...items.map(([, v]) => v.avg_views), 1);
      return `
        <div class="card">
          <h3 class="section-title">${label}</h3>
          ${items.map(([k, v]) => `
            <div class="bar-row">
              <span class="bar-label">${k}</span>
              <div class="bar-track"><div class="bar-fill" style="width:${(v.avg_views / max) * 100}%"></div></div>
              <span class="bar-val">${v.avg_views.toLocaleString()} avg</span>
            </div>
          `).join("")}
        </div>
      `;
    };

    insightsEl.innerHTML = `
      <div class="insights-grid">
        <div class="stat-block">
          <div class="stat-label">Posts logged</div>
          <div class="stat-value">${t.posts}</div>
        </div>
        <div class="stat-block">
          <div class="stat-label">Total views</div>
          <div class="stat-value">${t.views.toLocaleString()}</div>
        </div>
        <div class="stat-block">
          <div class="stat-label">Total likes</div>
          <div class="stat-value">${t.likes.toLocaleString()}</div>
        </div>
        <div class="stat-block">
          <div class="stat-label">Saves</div>
          <div class="stat-value">${t.saves.toLocaleString()}</div>
          <div class="stat-sub">strongest signal</div>
        </div>
      </div>

      <div class="card" style="margin-bottom:1.5rem">
        <h3 class="section-title">Tips vs Highlights — actual mix</h3>
        <div class="split-meter" style="margin-bottom:0">
          <div class="split-half">
            <div class="split-fill" style="transform: scaleX(${insights.actual_split.tips_pct / 100})"></div>
            <span class="split-label">Tips · actual</span>
            <span class="split-pct">${insights.actual_split.tips_pct}%</span>
          </div>
          <div class="split-half highlight">
            <div class="split-fill" style="transform: scaleX(${insights.actual_split.highlights_pct / 100})"></div>
            <span class="split-label">Highlights · actual</span>
            <span class="split-pct">${insights.actual_split.highlights_pct}%</span>
          </div>
        </div>
        <div class="post-meta" style="margin-top:0.75rem">Target: 70% tips · 30% highlights</div>
      </div>

      <div class="insights-row">
        ${renderBars(insights.by_platform, "Avg views by platform")}
        ${renderBars(insights.by_post_type, "Avg views by post type")}
      </div>

      <div class="insights-row">
        <div class="card">
          <h3 class="section-title">Top by views</h3>
          ${insights.top_views.map(p => `
            <div class="bar-row">
              <span class="bar-label">${p.platform}</span>
              <span style="font-size:0.9rem">${p.topic}</span>
              <span class="bar-val">${p.views.toLocaleString()}</span>
            </div>
          `).join("")}
        </div>
        <div class="card">
          <h3 class="section-title">Top by engagement</h3>
          ${insights.top_engagement.map(p => `
            <div class="bar-row">
              <span class="bar-label">${p.platform}</span>
              <span style="font-size:0.9rem">${p.topic}</span>
              <span class="bar-val">${p.rate}%</span>
            </div>
          `).join("")}
        </div>
      </div>
    `;
  }

  if (!entries.length) {
    list.innerHTML = "";
    return;
  }
  list.innerHTML = `<h3 class="section-title" style="margin-top:2rem">Log</h3>` +
    entries.sort((a, b) => (b.date || "").localeCompare(a.date || "")).map(e => `
      <div class="analytics-row">
        <div class="meta">${e.date ? fmtDate(e.date) : "—"}</div>
        <div>
          <div>${e.topic}</div>
          <div class="meta">${e.platform} · ${e.format} · ${e.post_type}</div>
        </div>
        <div class="meta">${(e.views || 0).toLocaleString()} v</div>
        <div class="meta">${(e.likes || 0).toLocaleString()} ♥</div>
        <div class="meta">${(e.saves || 0).toLocaleString()} ▼</div>
        <button class="btn danger small" data-del-analytics="${e.id}">×</button>
      </div>
    `).join("");

  $$("[data-del-analytics]").forEach(b =>
    b.addEventListener("click", async () => {
      await api.del(`/api/analytics/${b.dataset.delAnalytics}`);
      loadAnalytics();
    })
  );
}

$("#analytics-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(e.target));
  const r = await api.post("/api/analytics", data);
  if (r.ok) {
    toast("Post logged");
    e.target.reset();
    loadAnalytics();
  }
});

/* ---------- Boot ---------- */
checkAIStatus();
setInterval(checkAIStatus, 30000);
loadGear();
loadFilms();
loadCalendar();
loadAnalytics();
