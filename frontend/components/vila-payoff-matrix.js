/*
 * <vila-payoff-matrix> — tabela interativa de payoffs p/ jogos 2x2+.
 * Props:
 *   payoffs-a: JSON string — matriz 2D de payoffs jogador A
 *   payoffs-b: JSON string — matriz 2D de payoffs jogador B
 *   nash: JSON string — lista de [i, j] tuples que são NE puros
 *   labels-a, labels-b: JSON string — nomes das estratégias
 */

class VilaPayoffMatrix extends HTMLElement {
  static get observedAttributes() {
    return ['payoffs-a', 'payoffs-b', 'nash', 'labels-a', 'labels-b', 'titulo'];
  }

  constructor() { super(); this._root = this.attachShadow({ mode: 'open' }); }
  connectedCallback() { this._render(); }
  attributeChangedCallback() { this._render(); }

  _parse(attr, fallback) {
    try { return JSON.parse(this.getAttribute(attr) || '[]'); } catch { return fallback; }
  }

  _render() {
    const A = this._parse('payoffs-a', []);
    const B = this._parse('payoffs-b', []);
    const nash = this._parse('nash', []);
    const labelsA = this._parse('labels-a', []);
    const labelsB = this._parse('labels-b', []);
    const titulo = this.getAttribute('titulo') || '';

    if (A.length === 0 || B.length === 0) {
      this._root.innerHTML = `<p style="color: var(--text-muted); font-size: 13px;">sem dados</p>`;
      return;
    }

    const m = A.length;
    const n = A[0].length;
    const isNash = (i, j) => nash.some(([a, b]) => a === i && b === j);

    let rows = '';
    for (let i = 0; i < m; i++) {
      let cells = `<th>${labelsA[i] ?? `A${i}`}</th>`;
      for (let j = 0; j < n; j++) {
        const ne = isNash(i, j);
        cells += `
          <td class="${ne ? 'nash' : ''}" aria-label="${ne ? 'Equilíbrio de Nash' : ''}">
            <div class="payoff">
              <span class="a">${A[i][j]}</span>
              <span class="sep">,</span>
              <span class="b">${B[i][j]}</span>
            </div>
          </td>
        `;
      }
      rows += `<tr>${cells}</tr>`;
    }

    let header = '<th></th>';
    for (let j = 0; j < n; j++) header += `<th>${labelsB[j] ?? `B${j}`}</th>`;

    this._root.innerHTML = `
      <style>
        :host { display: block; font-family: var(--font-sans, system-ui); }
        .wrap {
          background: var(--bg-surface, #121828);
          border: 1px solid var(--border-subtle, #2a3450);
          border-radius: 8px;
          padding: 16px;
        }
        h3 { margin: 0 0 12px 0; font-size: 14px; color: var(--text-primary, #e8ecf4); }
        table { border-collapse: collapse; font-family: var(--font-mono, monospace); font-size: 14px; }
        th { padding: 6px 10px; color: var(--text-muted, #6b7489); font-weight: 500; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; }
        td { padding: 10px 14px; border: 1px solid var(--border-subtle, #2a3450); text-align: center; background: var(--bg-surface-2, #1a2236); transition: background 120ms; }
        td:hover { background: var(--bg-surface-3, #242e45); }
        td.nash { border-color: var(--amber, #d69e2e); background: rgba(214, 158, 46, 0.12); }
        td.nash::after { content: '★'; position: absolute; color: var(--amber, #d69e2e); font-size: 10px; margin-left: 4px; vertical-align: top; }
        .payoff { display: flex; gap: 2px; justify-content: center; align-items: baseline; font-variant-numeric: tabular-nums; }
        .a { color: var(--info, #60a5fa); }
        .b { color: var(--amber, #d69e2e); }
        .sep { color: var(--text-muted); }
        .legend { margin-top: 8px; font-size: 11px; color: var(--text-muted, #6b7489); }
      </style>
      <div class="wrap">
        ${titulo ? `<h3>${titulo}</h3>` : ''}
        <table>
          <thead><tr>${header}</tr></thead>
          <tbody>${rows}</tbody>
        </table>
        <div class="legend">
          <span class="a" style="color: var(--info, #60a5fa);">● A</span>
          &nbsp;
          <span class="b" style="color: var(--amber, #d69e2e);">● B</span>
          ${nash.length ? ` — <span>★ Equilíbrio de Nash</span>` : ''}
        </div>
      </div>
    `;
  }
}

customElements.define('vila-payoff-matrix', VilaPayoffMatrix);
