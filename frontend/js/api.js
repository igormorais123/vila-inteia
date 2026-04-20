/*
 * Vila INTEIA — wrappers tipados para /api/v1/*.
 * import { vila, colmeia, harness, rede, vivos } from '/frontend/js/api.js';
 */

import { api } from './core.js';

const V1 = '/api/v1';

export const vila = {
  iniciar: (opts) => api.post(`${V1}/vila/iniciar`, opts),
  step: (n) => api.post(`${V1}/vila/step`, { n: n ?? 1 }),
  pausar: () => api.post(`${V1}/vila/pausar`, {}),
  retomar: () => api.post(`${V1}/vila/retomar`, {}),
  parar: () => api.post(`${V1}/vila/parar`, {}),
  estado: () => api.get(`${V1}/vila/estado`),
  mapa: () => api.get(`${V1}/vila/mapa`),
  agentes: (filtros = {}) => {
    const q = new URLSearchParams(filtros).toString();
    return api.get(`${V1}/vila/agentes${q ? '?' + q : ''}`);
  },
  injetarTopico: (topico, importancia) =>
    api.post(`${V1}/vila/injetar-topico`, { topico, importancia }),
  iniciarDesafio: (tema, descricao, documento) =>
    api.post(`${V1}/vila/iniciar-desafio`, { tema, descricao, documento }),
};

export const colmeia = {
  ranking: (top = 20) => api.get(`${V1}/colmeia/ranking?top=${top}`),
  estado: () => api.get(`${V1}/colmeia/estado`),
  agente: (id) => api.get(`${V1}/colmeia/agente/${encodeURIComponent(id)}`),
  testeGenoma: (genoma) => api.post(`${V1}/colmeia/teste-genoma`, genoma),
};

export const harness = {
  saude: () => api.get(`${V1}/harness/saude`),
  traces: (filtros = {}) => {
    const q = new URLSearchParams(filtros).toString();
    return api.get(`${V1}/harness/traces${q ? '?' + q : ''}`);
  },
  trace: (id) => api.get(`${V1}/harness/traces/${encodeURIComponent(id)}`),
  tracesAgente: (id) => api.get(`${V1}/harness/traces/agente/${encodeURIComponent(id)}`),
  metricas: () => api.get(`${V1}/harness/metricas`),
  flush: () => api.post(`${V1}/harness/flush`, {}),
};

export const rede = {
  feed: (limite = 50) => api.get(`${V1}/rede/feed?limite=${limite}`),
  postar: (agenteId, conteudo) =>
    api.post(`${V1}/rede/agente/${encodeURIComponent(agenteId)}/postar`, { conteudo }),
  conversas: () => api.get(`${V1}/rede/conversas`),
};

export const vivos = {
  profile: (id) => api.get(`${V1}/vivos/habitante/${encodeURIComponent(id)}/profile`),
  traceLiveUrl: (id) => `${V1}/vivos/habitante/${encodeURIComponent(id)}/trace-live`,
};
