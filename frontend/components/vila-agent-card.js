/*
 * <vila-agent-card> — card compacto de habitante.
 * Props via atributos: nome, tier, patente, categoria, energia, avatar-url
 * Uso:
 *   <vila-agent-card nome="Sun Tzu" tier="S" patente="Coronel" categoria="estrategista" energia="80"></vila-agent-card>
 */

class VilaAgentCard extends HTMLElement {
  static get observedAttributes() {
    return ['nome', 'tier', 'patente', 'categoria', 'energia', 'avatar-url', 'status'];
  }

  constructor() {
    super();
    this._root = this.attachShadow({ mode: 'open' });
  }

  connectedCallback() { this._render(); }
  attributeChangedCallback() { this._render(); }

  _initial(nome) {
    return (nome || '?').trim().charAt(0).toUpperCase();
  }

  _tierColor(tier) {
    const map = { S: 'var(--amber)', A: 'var(--silver)', B: 'var(--bronze)', C: 'var(--text-muted)' };
    return map[tier?.toUpperCase()] || 'var(--text-muted)';
  }

  _render() {
    const nome = this.getAttribute('nome') || 'desconhecido';
    const tier = this.getAttribute('tier') || '';
    const patente = this.getAttribute('patente') || '';
    const categoria = this.getAttribute('categoria') || '';
    const energia = parseFloat(this.getAttribute('energia') || '0');
    const status = this.getAttribute('status') || '';

    this._root.innerHTML = `
      <style>
        :host {
          display: block;
          font-family: var(--font-sans, system-ui);
        }
        .card {
          display: grid;
          grid-template-columns: 40px 1fr auto;
          gap: 12px;
          align-items: center;
          padding: 10px 12px;
          background: var(--bg-surface, #121828);
          border: 1px solid var(--border-subtle, #2a3450);
          border-radius: 8px;
          transition: border-color 120ms;
        }
        .card:hover { border-color: var(--border-strong, #3a4666); }
        .avatar {
          width: 40px; height: 40px;
          border-radius: 50%;
          background: ${this._tierColor(tier)};
          color: var(--text-on-amber, #0a0e1a);
          display: flex; align-items: center; justify-content: center;
          font-weight: 700;
          font-size: 16px;
          font-family: var(--font-mono, monospace);
        }
        .info { min-width: 0; }
        .nome {
          font-size: 14px;
          font-weight: 600;
          color: var(--text-primary, #e8ecf4);
          overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
        }
        .meta {
          font-size: 11px;
          color: var(--text-muted, #6b7489);
          text-transform: uppercase;
          letter-spacing: 0.3px;
          margin-top: 2px;
        }
        .right {
          display: flex; flex-direction: column; gap: 4px; align-items: flex-end;
          font-size: 11px;
          color: var(--text-muted, #6b7489);
        }
        .energy-bar {
          width: 48px; height: 3px;
          background: var(--border-subtle, #2a3450);
          border-radius: 999px;
          overflow: hidden;
        }
        .energy-fill {
          height: 100%;
          background: ${energia > 30 ? 'var(--success, #4ade80)' : 'var(--warn, #fbbf24)'};
          width: ${Math.max(0, Math.min(100, energia))}%;
          transition: width 220ms;
        }
        .status-dot {
          display: inline-block;
          width: 6px; height: 6px;
          border-radius: 50%;
          background: ${status === 'ativo' ? 'var(--success, #4ade80)' :
                        status === 'latente' ? 'var(--text-muted, #6b7489)' : 'transparent'};
          margin-right: 4px;
        }
      </style>
      <article class="card" role="listitem" aria-label="${nome}, ${patente}">
        <div class="avatar" aria-hidden="true">${this._initial(nome)}</div>
        <div class="info">
          <div class="nome">${status ? `<span class="status-dot"></span>` : ''}${nome}</div>
          <div class="meta">${tier ? `Tier ${tier}` : ''}${categoria ? ` · ${categoria}` : ''}</div>
        </div>
        <div class="right">
          <div>${patente}</div>
          <div class="energy-bar" aria-label="energia"><div class="energy-fill"></div></div>
        </div>
      </article>
    `;
  }
}

customElements.define('vila-agent-card', VilaAgentCard);
