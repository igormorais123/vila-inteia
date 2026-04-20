/*
 * Vila INTEIA — JS core (Onda 10).
 * fetch wrapper, SSE client, event bus, toast. Zero deps.
 * import { api, bus, sse, toast } from '/js/core.js';
 */

/* ------------------------------------------------------------------ */
/* Event bus — pub/sub minimalista                                   */
/* ------------------------------------------------------------------ */
class EventBus {
  constructor() { this._lst = new Map(); }
  on(evt, fn) {
    if (!this._lst.has(evt)) this._lst.set(evt, new Set());
    this._lst.get(evt).add(fn);
    return () => this.off(evt, fn);
  }
  off(evt, fn) {
    if (this._lst.has(evt)) this._lst.get(evt).delete(fn);
  }
  emit(evt, data) {
    if (!this._lst.has(evt)) return;
    for (const fn of this._lst.get(evt)) {
      try { fn(data); } catch (e) { console.error(`[bus:${evt}]`, e); }
    }
  }
}
export const bus = new EventBus();

/* ------------------------------------------------------------------ */
/* fetch wrapper                                                      */
/* ------------------------------------------------------------------ */
async function request(path, { method = 'GET', body, headers = {} } = {}) {
  const opts = {
    method,
    headers: { 'Accept': 'application/json', ...headers },
  };
  if (body !== undefined) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(path, opts);
  const text = await res.text();
  let data = null;
  try { data = text ? JSON.parse(text) : null; } catch { data = text; }
  if (!res.ok) {
    const err = new Error(`HTTP ${res.status}: ${res.statusText}`);
    err.status = res.status;
    err.body = data;
    throw err;
  }
  return data;
}

export const api = {
  get: (p) => request(p),
  post: (p, body) => request(p, { method: 'POST', body }),
  put: (p, body) => request(p, { method: 'PUT', body }),
  del: (p) => request(p, { method: 'DELETE' }),
};

/* ------------------------------------------------------------------ */
/* SSE client                                                         */
/* ------------------------------------------------------------------ */
export function sse(path, handlers = {}) {
  const es = new EventSource(path);
  if (handlers.onMessage) es.onmessage = (e) => {
    let data = e.data;
    try { data = JSON.parse(e.data); } catch {}
    handlers.onMessage(data, e);
  };
  if (handlers.onError) es.onerror = handlers.onError;
  if (handlers.onOpen) es.onopen = handlers.onOpen;
  return es;  // caller deve chamar es.close() para parar
}

/* ------------------------------------------------------------------ */
/* Toast                                                              */
/* ------------------------------------------------------------------ */
let _toastRoot = null;
function ensureToastRoot() {
  if (_toastRoot) return _toastRoot;
  const el = document.createElement('div');
  el.id = 'vila-toast-root';
  el.style.cssText = `
    position: fixed; bottom: 24px; right: 24px;
    display: flex; flex-direction: column; gap: 8px;
    z-index: 300;
  `;
  document.body.appendChild(el);
  _toastRoot = el;
  return el;
}

export function toast(msg, { level = 'info', ttl = 4000 } = {}) {
  const root = ensureToastRoot();
  const colors = {
    info: 'var(--info)',
    success: 'var(--success)',
    warn: 'var(--warn)',
    danger: 'var(--danger)',
  };
  const el = document.createElement('div');
  el.setAttribute('role', 'status');
  el.setAttribute('aria-live', 'polite');
  el.style.cssText = `
    background: var(--bg-surface-2);
    border: 1px solid ${colors[level] || colors.info};
    color: var(--text-primary);
    padding: 8px 16px;
    border-radius: 6px;
    font-size: 13px;
    max-width: 320px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.45);
    opacity: 0;
    transform: translateY(8px);
    transition: opacity 200ms, transform 200ms;
  `;
  el.textContent = msg;
  root.appendChild(el);
  requestAnimationFrame(() => { el.style.opacity = '1'; el.style.transform = 'translateY(0)'; });
  setTimeout(() => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(8px)';
    setTimeout(() => el.remove(), 220);
  }, ttl);
}

/* ------------------------------------------------------------------ */
/* Helpers utilitários                                                */
/* ------------------------------------------------------------------ */
export const fmt = {
  money: (n) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(n),
  num: (n, digits = 2) => new Intl.NumberFormat('pt-BR', { maximumFractionDigits: digits }).format(n),
  pct: (n, digits = 1) => new Intl.NumberFormat('pt-BR', { style: 'percent', maximumFractionDigits: digits }).format(n),
  rel: (iso) => {
    const s = Math.round((Date.now() - new Date(iso)) / 1000);
    if (s < 60) return `${s}s atrás`;
    if (s < 3600) return `${Math.round(s / 60)}min atrás`;
    if (s < 86400) return `${Math.round(s / 3600)}h atrás`;
    return `${Math.round(s / 86400)}d atrás`;
  },
};
