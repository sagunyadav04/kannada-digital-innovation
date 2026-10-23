const $ = (id) => document.getElementById(id);
const clientId = (() => {
  let id = localStorage.getItem("kde_client");
  if (!id) { id = crypto.randomUUID(); localStorage.setItem("kde_client", id); }
  return id;
})();
const headers = { "X-Client-Id": clientId };
let current = null; // {text, explanation}

const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const reEsc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

function setStatus(msg, isError = false) {
  const el = $("status");
  el.hidden = !msg; el.textContent = msg || ""; el.className = "status" + (isError ? " error" : "");
}

function renderText(terms = []) {
  const clean = terms.filter(Boolean);
  let html = esc(current.text);
  if (clean.length) {
    const re = new RegExp("(" + clean.map((t) => reEsc(esc(t))).join("|") + ")", "gi");
    html = html.replace(re, "<mark>$1</mark>");
  }
  $("kn-text").innerHTML = html;
  const first = $("kn-text").querySelector("mark");
  if (first) first.scrollIntoView({ block: "nearest", behavior: "smooth" });
}

function renderResult(data) {
  current = data;
  const ex = data.explanation;
  $("result").hidden = false;
  $("doctype").textContent = ex.doc_type_label;
  $("summary").textContent = ex.summary;
  $("actions-list").innerHTML = (ex.action_items.length ? ex.action_items : ["No specific actions detected."]).map((a) => `<li>${esc(a)}</li>`).join("");
  $("facts").innerHTML = ex.key_facts.length
    ? ex.key_facts.map((f) => `<dt>${esc(f.label)}</dt><dd>${esc(f.value)}</dd>`).join("")
    : "<dd class='muted'>No dates, amounts or numbers detected.</dd>";
  const g = $("glossary");
  g.innerHTML = ex.glossary.length
    ? ex.glossary.map((w) => `<li tabindex="0" data-kn="${esc(w.kn)}"><b>${esc(w.kn)}</b>${esc(w.en)}</li>`).join("")
    : "<li class='muted'>No known terms found.</li>";
  g.querySelectorAll("li[data-kn]").forEach((li) => {
    const on = () => renderText([li.dataset.kn]), off = () => renderText([$("find").value]);
    li.addEventListener("mouseenter", on); li.addEventListener("focus", on);
    li.addEventListener("mouseleave", off); li.addEventListener("blur", off);
  });
  $("translation").textContent = ex.translation_en || "A full translation needs the AI engine (set GEMINI_API_KEY on the server). The explanation and glossary work without it.";
  $("find").value = "";
  renderText();
  $("result").scrollIntoView({ behavior: "smooth", block: "start" });
}

async function handleFile(file) {
  if (!file) return;
  setStatus("Reading your document… this can take up to 20 seconds.");
  $("result").hidden = true;
  const form = new FormData();
  form.append("file", file);
  form.append("save", "true"); // every scan is saved to the library
  try {
    const res = await fetch("/api/process", { method: "POST", body: form, headers });
    const body = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(body.detail || "Something went wrong. Try again.");
    setStatus("");
    renderResult(body);
    current.filename = file.name;
    if (body.id) { setStatus("Saved to your library."); loadLibrary(); }
    else saveCurrent();
  } catch (e) {
    setStatus(e.message, true);
  }
}

// upload
const drop = $("drop");
$("file").addEventListener("change", (e) => handleFile(e.target.files[0]));
drop.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); $("file").click(); } });
["dragenter", "dragover"].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add("over"); }));
["dragleave", "drop"].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.remove("over"); }));
drop.addEventListener("drop", (e) => handleFile(e.dataTransfer.files[0]));

// text tools
$("find").addEventListener("input", (e) => current && renderText([e.target.value.trim()]));
$("copy").addEventListener("click", async () => { await navigator.clipboard.writeText(current.text); setStatus("Text copied."); });
$("download").addEventListener("click", () => {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([current.text], { type: "text/plain;charset=utf-8" }));
  a.download = "kannada-document.txt"; a.click(); URL.revokeObjectURL(a.href);
});
$("speak").addEventListener("click", () => {
  if (!("speechSynthesis" in window)) return setStatus("Read aloud is not supported in this browser.", true);
  speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(current.text);
  u.lang = "kn-IN";
  const kn = speechSynthesis.getVoices().find((v) => v.lang.startsWith("kn"));
  if (!kn) setStatus("No Kannada voice installed on this device; it may read with a default voice.");
  else u.voice = kn;
  speechSynthesis.speak(u);
});

// tabs + nav
document.querySelectorAll(".tab").forEach((t) => t.addEventListener("click", () => {
  document.querySelectorAll(".tab").forEach((x) => x.classList.toggle("active", x === t));
  $("tab-explain").hidden = t.dataset.tab !== "explain";
  $("tab-translation").hidden = t.dataset.tab !== "translation";
}));
function show(view) {
  $("scan").hidden = view !== "scan"; $("library").hidden = view !== "lib";
  $("nav-scan").classList.toggle("active", view === "scan"); $("nav-lib").classList.toggle("active", view === "lib");
  if (view === "lib") loadLibrary();
}
$("nav-scan").onclick = () => show("scan"); $("nav-lib").onclick = () => show("lib");

// library
async function loadLibrary() {
  const q = $("lib-q").value.trim();
  let docs = [];
  try {
    const res = await fetch("/api/documents?q=" + encodeURIComponent(q), { headers });
    if (!res.ok) throw new Error("HTTP " + res.status);
    docs = await res.json();
  } catch (e) {
    $("lib-list").innerHTML = "<li class='muted'>Could not load your library. Check that the server is running.</li>";
    return;
  }
  $("lib-list").innerHTML = docs.length
    ? docs.map((d) => `<li><div class="meta"><strong>${esc(d.filename || "Document")}</strong> <span class="muted small">${esc(new Date(d.created).toLocaleString())}</span><p>${esc(d.snippet)}</p></div>
        <span><button data-open="${esc(d.id)}">Open</button> <button data-del="${esc(d.id)}">Delete</button></span></li>`).join("")
    : "<li class='muted'>Nothing here yet. Tick “Save to my library” when you scan a document.</li>";
}
$("lib-q").addEventListener("input", loadLibrary);

// Saves the document on screen (used if the server did not save it during the scan).
async function saveCurrent() {
  if (!current || current.id) return;
  try {
    const res = await fetch("/api/documents", {
      method: "POST",
      headers: { ...headers, "Content-Type": "application/json" },
      body: JSON.stringify({
        filename: current.filename || "Document",
        engine: current.engine || "tesseract",
        text: current.text,
        explanation: current.explanation,
      }),
    });
    const out = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(out.detail || "Could not save this document.");
    current.id = out.id;
    setStatus("Saved to your library.");
    loadLibrary();
  } catch (e) {
    setStatus(e.message, true);
  }
}

// Saving is automatic, so the checkbox is no longer needed.
$("save").checked = true;
const saveLabel = $("save").closest("label");
if (saveLabel) saveLabel.style.display = "none";
$("lib-list").addEventListener("click", async (e) => {
  const open = e.target.dataset.open, del = e.target.dataset.del;
  if (open) {
    const res = await fetch("/api/documents/" + open, { headers });
    if (res.ok) { show("scan"); renderResult(await res.json()); }
  } else if (del) { await fetch("/api/documents/" + del, { method: "DELETE", headers }); loadLibrary(); }
});

fetch("/api/health").then((r) => r.json()).then((h) => {
  $("engine-note").textContent = h.ai ? "AI reading enabled (handles photos and handwriting)" : "Offline reading (Tesseract). Add a Gemini key for better accuracy.";
}).catch(() => {});

// Dark / light theme toggle. Load after the page body, before app.js.
// - Adds the toggle button itself if the page doesn't have one.
// - If app.js already has its own theme-toggle code, delete that code so the button isn't handled twice.
(function () {
  var root = document.documentElement;
  var btn = document.getElementById('theme-toggle');

  if (!btn) {
    var nav = document.querySelector('nav') || document.querySelector('header');
    if (nav) {
      btn = document.createElement('button');
      btn.id = 'theme-toggle';
      btn.type = 'button';
      btn.className = 'navbtn';
      btn.title = 'Switch color theme';
      nav.appendChild(btn);
    }
  }

  function systemDark() {
    try { return window.matchMedia('(prefers-color-scheme: dark)').matches; } catch (e) { return false; }
  }

  function current() {
    var t = root.getAttribute('data-theme');
    return t ? t : (systemDark() ? 'dark' : 'light');
  }

  function apply(theme) {
    root.setAttribute('data-theme', theme);
    if (btn) {
      btn.setAttribute('aria-pressed', theme === 'dark' ? 'true' : 'false');
      btn.textContent = theme === 'dark' ? '☀️ Light mode' : '🌙 Dark mode';
    }
  }

  var saved = null;
  try { saved = localStorage.getItem('theme'); } catch (e) { /* ignore */ }
  apply(saved === 'dark' || saved === 'light' ? saved : current());

  if (btn) {
    btn.addEventListener('click', function () {
      var next = current() === 'dark' ? 'light' : 'dark';
      apply(next);
      try { localStorage.setItem('theme', next); } catch (e) { /* storage blocked; still works for this visit */ }
    });
  }

  // Follow the system setting until the user picks one themselves.
  try {
    var mq = window.matchMedia('(prefers-color-scheme: dark)');
    var onChange = function (e) {
      if (!localStorage.getItem('theme')) apply(e.matches ? 'dark' : 'light');
    };
    if (mq.addEventListener) mq.addEventListener('change', onChange);
  } catch (e) { /* ignore */ }
})();