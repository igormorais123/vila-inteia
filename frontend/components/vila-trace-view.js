/*
 * <vila-trace-view> — árvore de causal chain.
 * Atributo: trace (JSON string) — objeto com id, fase, filhos[], duracao_ms, tokens, custo_usd
 */

class VilaTraceView extends HTMLElement {
  static get observedAttributes() { return ['trace']; }

  constructor() { super(); this._root = this.attachShadow({ mode: 'open' }); }
  connectedCallback() { this._render(); }
  attributeChangedCallback() { this._render(); }

  _renderNode(n, depth = 0) {
    if (!n) return '';
    const filhos = Array.isArray(n.filhos) ? n.filhos : [];
    const icone = filhos.length ? '▾' : '•';
    return `
      <li style="padding-left: ${depth * 16}px;" role="treeitem" aria-expanded="${filhos.length > 0}">
        <div class="node">
          <span class="caret">${icone}</span>
          <span class="fase">${n.fase || '?'}</span>
          <span class="meta">${n.duracao_ms ?? '?'}ms · ${n.tokens ?? 0}tok · $${(n.custo_usd ?? 0).toFixed(4)}</span>
          <span class="status ${n.resultado || 'sucesso'}">${n.resultado || 'sucesso'}</span>
        </div>
        ${filhos.length ? `<ul role="group">${filhos.map(f => this._renderNode(f, depth + 1)).join('')}</ul>` : ''}
      </li>
    `;
  }

  _render() {
    let trace = null;
    try { trace = JSON.parse(this.getAttribute('trace') || 'null'); } catch {}

    if (!trace) {
      this._root.innerHTML = `<p style="color: var(--text-muted); font-size: 13px;">sem trace</p>`;
      return;
    }

    this._root.innerHTML = `
      <style>
        :host { display: block; font-family: var(--font-mono, monospace); font-size: 13px; }
        ul { list-style: none; padding: 0; margin: 0; }
        li { margin: 0; }
        .node {
          display: flex; align-items: center; gap: 8px;
          padding: 6px 8px;
          border-radius: 4px;
          transition: background 120ms;
        }
        .node:hover { background: var(--bg-surface-2, #1a2236); }
        .caret { color: var(--text-muted, #6b7489); width: 12px; }
        .fase { color: var(--amber, #d69e2e); font-weight: 500; }
        .meta { color: var(--text-muted, #6b7489); font-size: 11px; margin-left: auto; }
        .status { font-size: 10px; padding: 1px 6px; border-radius: 999px; text-transform: uppercase; letter-spacing: 0.5px; }
        .status.sucesso { color: var(--success, #4ade80); border: 1px solid var(--success, #4ade80); }
        .status.falha { color: var(--danger, #f87171); border: 1px solid var(--danger, #f87171); }
        .status.aprovacao_humana { color: var(--warn, #fbbf24); border: 1px solid var(--warn, #fbbf24); }
      </style>
      <ul role="tree" aria-label="Causal chain">${this._renderNode(trace)}</ul>
    `;
  }
}

customElements.define('vila-trace-view', VilaTraceView);
