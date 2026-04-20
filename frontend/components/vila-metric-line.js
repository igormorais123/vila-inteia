/*
 * <vila-metric-line> — métrica 1 linha 1 número com sparkline opcional.
 * Atributos:
 *   label, valor, unit, trend (subindo|descendo|estavel), points (JSON)
 */

class VilaMetricLine extends HTMLElement {
  static get observedAttributes() { return ['label', 'valor', 'unit', 'trend', 'points']; }

  constructor() { super(); this._root = this.attachShadow({ mode: 'open' }); }
  connectedCallback() { this._render(); }
  attributeChangedCallback() { this._render(); }

  _sparkline(points) {
    if (!Array.isArray(points) || points.length < 2) return '';
    const w = 80, h = 18;
    const min = Math.min(...points), max = Math.max(...points);
    const range = max - min || 1;
    const step = w / (points.length - 1);
    const path = points.map((p, i) => {
      const x = i * step;
      const y = h - ((p - min) / range) * h;
      return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`;
    }).join(' ');
    return `<svg width="${w}" height="${h}" aria-hidden="true">
      <path d="${path}" fill="none" stroke="var(--amber, #d69e2e)" stroke-width="1.5" />
    </svg>`;
  }

  _render() {
    const label = this.getAttribute('label') || '';
    const valor = this.getAttribute('valor') || '-';
    const unit = this.getAttribute('unit') || '';
    const trend = this.getAttribute('trend') || '';
    const trendIcon = trend === 'subindo' ? '↑' : trend === 'descendo' ? '↓' : trend === 'estavel' ? '=' : '';
    const trendColor = trend === 'subindo' ? 'var(--success)' : trend === 'descendo' ? 'var(--danger)' : 'var(--text-muted)';
    let points = [];
    try { points = JSON.parse(this.getAttribute('points') || '[]'); } catch {}

    this._root.innerHTML = `
      <style>
        :host { display: inline-block; font-family: var(--font-sans, system-ui); }
        .row { display: flex; align-items: baseline; gap: 12px; padding: 8px 0; }
        .label { font-size: 11px; color: var(--text-muted, #6b7489); text-transform: uppercase; letter-spacing: 0.5px; min-width: 80px; }
        .valor { font-size: 22px; font-weight: 600; color: var(--text-primary, #e8ecf4); font-variant-numeric: tabular-nums; }
        .unit { font-size: 13px; color: var(--text-muted, #6b7489); }
        .trend { font-size: 13px; color: ${trendColor}; }
        .spark { margin-left: auto; }
      </style>
      <div class="row" role="figure" aria-label="${label}: ${valor} ${unit}">
        <div class="label">${label}</div>
        <div class="valor">${valor}</div>
        <div class="unit">${unit}</div>
        <div class="trend">${trendIcon}</div>
        <div class="spark">${this._sparkline(points)}</div>
      </div>
    `;
  }
}

customElements.define('vila-metric-line', VilaMetricLine);
