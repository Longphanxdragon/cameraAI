/**
 * Chart2Code App — Frontend Logic
 * Handles: auth, file upload, API calls, code display, history, billing
 */

const API = '';   // same-origin (FastAPI serves frontend)
let authToken = localStorage.getItem('c2c_token') || '';

// ── Toast ─────────────────────────────────────────────────────────────────────
function toast(msg, type = 'info') {
  const ct = document.getElementById('toast-container');
  const t  = document.createElement('div');
  t.className = `toast ${type}`;
  t.textContent = msg;
  ct.appendChild(t);
  setTimeout(() => t.remove(), 4000);
}

// ── Auth helpers ──────────────────────────────────────────────────────────────
function setToken(tok) {
  authToken = tok;
  localStorage.setItem('c2c_token', tok);
}
function clearToken() {
  authToken = '';
  localStorage.removeItem('c2c_token');
}
function authHeaders() {
  return { Authorization: `Bearer ${authToken}` };
}

// ── Fetch wrapper ─────────────────────────────────────────────────────────────
async function api(path, opts = {}) {
  opts.headers = { ...authHeaders(), ...(opts.headers || {}) };
  const res = await fetch(API + path, opts);
  if (res.status === 401) { logout(); return null; }
  return res;
}

// ── User state ────────────────────────────────────────────────────────────────
let currentUser = null;

async function loadUser() {
  if (!authToken) { showAuth(); return; }
  const res = await api('/api/auth/me');
  if (!res || !res.ok) { logout(); return; }
  currentUser = await res.json();
  renderUserBar();
  hideAuth();
  loadHistory();
  checkUrlParams();
}

function renderUserBar() {
  if (!currentUser) return;
  const el = document.getElementById('user-bar');
  if (!el) return;
  const remaining = currentUser.credits_remaining;
  const pct = Math.round((remaining / currentUser.credits_limit) * 100);
  el.innerHTML = `
    <div class="user-info">
      <span class="user-email">${currentUser.email}</span>
      <span class="badge badge-${currentUser.plan === 'free' ? 'blue' : 'purple'}">${currentUser.plan.toUpperCase()}</span>
    </div>
    <div class="credits-bar-wrap">
      <div class="credits-label">
        <span><i class="fa-solid fa-bolt"></i> ${remaining} / ${currentUser.credits_limit} credits left</span>
        ${currentUser.plan === 'free'
          ? `<button class="btn btn-primary btn-sm" onclick="startCheckout('pro')">⬆️ Upgrade</button>`
          : `<button class="btn btn-ghost btn-sm" onclick="openBillingPortal()">Manage Plan</button>`
        }
      </div>
      <div class="credits-track">
        <div class="credits-fill" style="width:${pct}%;background:${pct < 20 ? 'var(--red)' : 'var(--grad)'}"></div>
      </div>
    </div>
  `;
}

// ── Auth modal ────────────────────────────────────────────────────────────────
function showAuth(tab = 'login') {
  const overlay = document.getElementById('auth-overlay');
  overlay.classList.add('open');
  switchAuthTab(tab);
}
function hideAuth() {
  document.getElementById('auth-overlay').classList.remove('open');
}
function switchAuthTab(tab) {
  document.getElementById('tab-login').classList.toggle('active', tab === 'login');
  document.getElementById('tab-register').classList.toggle('active', tab === 'register');
  document.getElementById('form-login').style.display    = tab === 'login'    ? 'flex' : 'none';
  document.getElementById('form-register').style.display = tab === 'register' ? 'flex' : 'none';
}

async function doLogin(e) {
  e.preventDefault();
  const email = document.getElementById('login-email').value.trim();
  const pass  = document.getElementById('login-pass').value;
  const btn   = document.getElementById('btn-login');
  btn.disabled = true; btn.textContent = 'Logging in…';

  const res = await fetch(API + '/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password: pass }),
  });
  btn.disabled = false; btn.textContent = 'Log In';

  const data = await res.json();
  if (!res.ok) { toast(data.detail || 'Login failed', 'error'); return; }
  setToken(data.token);
  await loadUser();
  toast('Welcome back! 👋', 'success');
}

async function doRegister(e) {
  e.preventDefault();
  const email = document.getElementById('reg-email').value.trim();
  const pass  = document.getElementById('reg-pass').value;
  const btn   = document.getElementById('btn-register');
  btn.disabled = true; btn.textContent = 'Creating account…';

  const res = await fetch(API + '/api/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password: pass }),
  });
  btn.disabled = false; btn.textContent = 'Create Account';

  const data = await res.json();
  if (!res.ok) { toast(data.detail || 'Registration failed', 'error'); return; }
  setToken(data.token);
  await loadUser();
  toast('Account created! 🎉 You have 5 free credits.', 'success');
}

function logout() {
  clearToken();
  currentUser = null;
  showAuth();
  document.getElementById('output-section').style.display = 'none';
  document.getElementById('history-section').style.display = 'none';
}

// ── Upload & Generate ─────────────────────────────────────────────────────────
let selectedFile = null;

function setupDropzone() {
  const zone   = document.getElementById('dropzone');
  const fileIn = document.getElementById('file-input');

  zone.addEventListener('click', () => fileIn.click());
  zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('dragging'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('dragging'));
  zone.addEventListener('drop', e => {
    e.preventDefault();
    zone.classList.remove('dragging');
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  });
  fileIn.addEventListener('change', () => {
    if (fileIn.files[0]) handleFile(fileIn.files[0]);
  });
}

function handleFile(file) {
  if (!file.type.startsWith('image/')) {
    toast('Please upload an image file (PNG, JPG, etc.)', 'error');
    return;
  }
  if (file.size > 10 * 1024 * 1024) {
    toast('File is too large. Max 10 MB.', 'error');
    return;
  }
  selectedFile = file;

  // Show preview
  const reader = new FileReader();
  reader.onload = ev => {
    document.getElementById('preview-img').src = ev.target.result;
    document.getElementById('preview-wrap').style.display = 'block';
    document.getElementById('dropzone-hint').style.display = 'none';
    document.getElementById('fname-label').textContent = file.name;
  };
  reader.readAsDataURL(file);

  // Enable generate button
  document.getElementById('btn-generate').disabled = false;
}

async function generateCode() {
  if (!selectedFile || !currentUser) return;
  if (currentUser.credits_remaining <= 0) {
    toast('No credits left! Upgrade to continue.', 'error');
    startCheckout('pro');
    return;
  }

  const btn = document.getElementById('btn-generate');
  btn.disabled = true;
  btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generating…';

  const form = new FormData();
  form.append('file', selectedFile);

  const res = await api('/api/generate', { method: 'POST', body: form });
  btn.disabled = false;
  btn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Generate Code';

  if (!res) return;
  const data = await res.json();

  if (!res.ok) {
    if (res.status === 402) {
      toast(data.detail, 'error');
      startCheckout('pro');
    } else {
      toast(data.detail || 'Generation failed', 'error');
    }
    return;
  }

  showCode(data.code);
  currentUser.credits_remaining = data.credits_remaining;
  renderUserBar();
  loadHistory();
  toast('Code generated! ✨', 'success');
}

// ── Code output ───────────────────────────────────────────────────────────────
function showCode(code) {
  const out = document.getElementById('output-section');
  const pre = document.getElementById('code-output');
  out.style.display = 'block';
  pre.textContent = code;
  if (window.Prism) Prism.highlightElement(pre);
  pre.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function copyCode() {
  const code = document.getElementById('code-output').textContent;
  navigator.clipboard.writeText(code).then(() => toast('Copied to clipboard! 📋', 'success'));
}

function downloadCode() {
  const code = document.getElementById('code-output').textContent;
  const blob = new Blob([code], { type: 'text/plain' });
  const a    = document.createElement('a');
  a.href     = URL.createObjectURL(blob);
  a.download = 'chart_code.py';
  a.click();
  toast('Downloaded chart_code.py', 'success');
}

// ── History ───────────────────────────────────────────────────────────────────
async function loadHistory() {
  const sec = document.getElementById('history-section');
  const res = await api('/api/history');
  if (!res || !res.ok) return;
  const items = await res.json();
  if (!items.length) { sec.style.display = 'none'; return; }

  sec.style.display = 'block';
  const list = document.getElementById('history-list');
  list.innerHTML = items.map(item => `
    <div class="history-item" onclick="showCode(${JSON.stringify(item.generated_code)})">
      <div class="history-icon"><i class="fa-solid fa-chart-bar"></i></div>
      <div class="history-info">
        <div class="history-name">${item.image_name || 'chart.png'}</div>
        <div class="history-date">${new Date(item.created_at).toLocaleDateString()}</div>
      </div>
      <i class="fa-solid fa-chevron-right" style="color:var(--text-muted);margin-left:auto;"></i>
    </div>
  `).join('');
}

// ── Billing ───────────────────────────────────────────────────────────────────
async function startCheckout(plan) {
  const res = await api('/api/billing/checkout', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ plan }),
  });
  if (!res) return;
  if (!res.ok) {
    const d = await res.json();
    toast(d.detail || 'Payment not configured yet', 'error');
    return;
  }
  const { url } = await res.json();
  window.location.href = url;
}

async function openBillingPortal() {
  const res = await api('/api/billing/portal', { method: 'POST' });
  if (!res || !res.ok) { toast('Could not open billing portal', 'error'); return; }
  const { url } = await res.json();
  window.location.href = url;
}

// ── URL param handling ────────────────────────────────────────────────────────
function checkUrlParams() {
  const sp = new URLSearchParams(window.location.search);
  if (sp.get('success'))  toast('🎉 Subscription activated! Enjoy your extra credits.', 'success');
  if (sp.get('canceled')) toast('Payment canceled. You can try again anytime.', 'info');
  if (sp.get('plan'))     startCheckout(sp.get('plan'));
  // Clean URL
  window.history.replaceState({}, '', '/app.html');
}

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  setupDropzone();
  loadUser();
});
