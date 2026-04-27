
/* ============================================================
   CONFIGURACAO
   ============================================================ */
// Auto-detectar backend: se no Render, usar proxy local (resolve CORS)
const _IS_RENDER = location.hostname.includes('onrender.com');
const BACKEND_URL = _IS_RENDER ? location.origin : 'https://api.inteia.com.br';
const OMNI_URL = _IS_RENDER
  ? location.origin + '/api/v1/vila/chat'
  : 'https://api.inteia.com.br/api/v1/vila-inteia/chat';
const OMNI_MODEL = 'BestFREE';
const DATA_URL = '../data/banco-consultores-lendarios.json';
const BACKEND_API = _IS_RENDER
  ? location.origin + '/api/v1/vila'
  : 'https://api.inteia.com.br/api/v1/vila-inteia';
const CONSULTORS_API_URL = _IS_RENDER
  ? ''
  : `${BACKEND_URL}/api/v1/consultores-lendarios?por_pagina=200`;

/* ============================================================
   ESTADO GLOBAL
   ============================================================ */
let consultores = [];
let mensagens = [];
let artigos = [];
let propostas = [];
let wallets = {};
let transacoes = [];
let helenaInsights = [];
let artigosSalvosBackend = new Set();
let running = false;
let speed = 1;
let roundNum = 0;
let speakersSet = new Set();
let sessionId = '';
let timerHandle = null;
let isGenerating = false;
let lastSpeakerId = null;
let lastSpeakers = [];
const TRIBUNA_GAP = 8;
let artigoCounter = 0;

function showFatalInitError(err) {
  const msg = (err && err.message) ? String(err.message) : String(err || 'Erro desconhecido');
  console.error('[JOGO] Falha fatal na inicializacao:', err);
  const feed = document.getElementById('feed');
  if (!feed) return;
  const diagnostico = /502|Bad Gateway|Failed to fetch|NetworkError/i.test(msg)
    ? 'Falha de conexao com a API da Vila INTEIA. O backend publico esta instavel ou indisponivel.'
    : 'Falha ao inicializar o Jogo Constituinte da Vila INTEIA.';
  feed.innerHTML =
    '<div class="msg tipo-sistema"><div class="msg-text">' + diagnostico +
    '<br><small style="display:block;margin-top:8px;color:#94a3b8">Detalhe tecnico: ' +
    msg.replace(/</g, '&lt;') + '</small></div></div>';
}

async function carregarConsultores() {
  for (const path of ['./banco-consultores-lendarios.json', DATA_URL]) {
    try {
      const r = await fetch(path);
      if (!r.ok) continue;
      const data = await r.json();
      if (Array.isArray(data) && data.length > 50) {
        return data;
      }
    } catch (e) {}
  }

  try {
    const r = await fetch(CONSULTORS_API_URL);
    if (r.ok) {
      const data = await r.json();
      if (Array.isArray(data?.consultores) && data.consultores.length > 50) {
        return data.consultores;
      }
    }
  } catch (e) {
    console.warn('[INIT] API de consultores indisponivel, tentando fallback estatico');
  }

  throw new Error('Nao foi possivel carregar os consultores da Vila INTEIA');
}

/* ============================================================
   PROCESSO LEGISLATIVO — Baseado no modelo brasileiro
   ============================================================ */

// Fases do processo legislativo
const FASE = {
  PAUTA: 'pauta',           // Escolha do tema para debate
  APRESENTACAO: 'apresentacao', // Proponente apresenta
  DISCUSSAO: 'discussao',   // Oradores discutem (a favor e contra)
  VOTACAO: 'votacao',        // Votação formal
  RESULTADO: 'resultado'     // Anúncio do resultado
};

let faseAtual = FASE.PAUTA;
let propostaEmPauta = null;     // Proposta sendo deliberada (uma por vez)
let ordemDosDias = [];          // Fila de temas/propostas pendentes
let votosRodada = { sim: new Set(), nao: new Set(), abstencao: new Set() };
let numOradoresDiscussao = 0;   // Quantos já falaram na fase de discussão
let rodadaUltimaFase = 0;       // Rodada em que a fase mudou pela última vez
const MAX_ORADORES_DISCUSSAO = 5; // Máximo de oradores por fase de discussão (was 8)
const MIN_ORADORES_DISCUSSAO = 2; // Mínimo antes de poder ir para votação (was 3)
const QUORUM_SIMPLES = 0.5;     // Maioria simples (>50% dos votantes)
const QUORUM_QUALIFICADO = 0.66; // 2/3 para matérias constitucionais importantes

// Presidente da Assembleia (jurista que conduz os trabalhos)
const PRESIDENTE_ASSEMBLEIA = 'CL097'; // Rui Barbosa (jurista lendário, orador)

// Regimento Interno pré-escrito (essas regras já existem desde o início)
const REGIMENTO_INTERNO = [
  {
    numero: 'RI-1',
    texto: 'A Assembleia Constituinte da Vila INTEIA é presidida por Rui Barbosa, que conduz os trabalhos, concede a palavra, mantém a ordem e proclama os resultados das votações.',
    tipo: 'Processo Legislativo'
  },
  {
    numero: 'RI-2',
    texto: 'O processo legislativo segue as fases: (1) Apresentação da proposta pelo proponente; (2) Discussão com no mínimo 3 e no máximo 8 oradores; (3) Votação nominal — maioria simples para artigos ordinários, dois terços para matérias de governança e punição.',
    tipo: 'Processo Legislativo'
  },
  {
    numero: 'RI-3',
    texto: 'Cada deliberação trata de UMA proposta por vez. Emendas são aceitas durante a fase de discussão e votadas como substitutivos antes da proposta original.',
    tipo: 'Processo Legislativo'
  },
  {
    numero: 'RI-4',
    texto: 'Qualquer constituinte pode requerer destaque, questão de ordem ou pedir vista. O Presidente decide questões de ordem. Obstrução deliberada é punida com perda da palavra por 5 rodadas.',
    tipo: 'Processo Legislativo'
  },
  {
    numero: 'RI-5',
    texto: 'O Regimento Interno pode ser alterado pela Assembleia por maioria de dois terços, mediante proposta fundamentada.',
    tipo: 'Processo Legislativo'
  }
];

// Pauta de temas obrigatórios (ordem prioritária)
const PAUTA_OBRIGATORIA = [
  { tema: 'Princípios Fundamentais', desc: 'Definir valores, objetivos e fundamentos da Vila INTEIA' },
  { tema: 'Forma de Governo', desc: 'Sistema de governo, eleições, mandatos, poderes' },
  { tema: 'Economia e Moeda', desc: 'Regulamentação da moeda Ξ, impostos, comércio, propriedade' },
  { tema: 'Direitos e Deveres', desc: 'Direitos fundamentais dos habitantes, deveres cívicos' },
  { tema: 'Punições e Justiça', desc: 'Sistema de punições, tribunal, expulsão, recursos' },
  { tema: 'Emendas à Constituição', desc: 'Como alterar a constituição no futuro' }
];
let pautaIndex = 0; // Qual tema da pauta obrigatória estamos

/* Tipos de artigo constitucionais */
const TIPOS_ARTIGO = [
  'Princípios Fundamentais',
  'Organização e Governança',
  'Economia e Moeda',
  'Direitos e Deveres',
  'Punições e Expulsão',
  'Processo Legislativo',
  'Emendas e Revisão'
];

/* ============================================================
   CORES POR CATEGORIA
   ============================================================ */
const CAT_COLORS = {
  visionario: '#8b5cf6',
  estrategia: '#3b82f6',
  investidor: '#10b981',
  negociacao: '#f59e0b',
  tech: '#06b6d4',
  marca: '#ec4899',
  politica_internacional: '#ef4444',
  politica_brasileira: '#22c55e',
  resiliencia: '#f97316',
  ia_futuro: '#a78bfa',
  mindset: '#14b8a6',
  br_business: '#84cc16',
  mkt_digital: '#f472b6',
  lado_negro: '#991b1b',
  qi_extremo: '#7c3aed',
  omega: '#d69e2e',
  ficticio: '#6366f1',
  influencia_oratoria: '#e879f9',
  jurista_lendario: '#78716c',
  provocador: '#dc2626',
  espiritual: '#fbbf24'
};

const CAT_LABELS = {
  visionario:'Visionário', estrategia:'Estratégia', investidor:'Investidor',
  negociacao:'Negociação', tech:'Tech', marca:'Marca',
  politica_internacional:'Política Intl', politica_brasileira:'Política BR',
  resiliencia:'Resiliência', ia_futuro:'IA & Futuro', mindset:'Mindset',
  br_business:'Business BR', mkt_digital:'Marketing Digital',
  lado_negro:'Lado Negro', qi_extremo:'QI Extremo', omega:'Omega',
  ficticio:'Fictício', influencia_oratoria:'Oratória',
  jurista_lendario:'Jurista', provocador:'Provocador', espiritual:'Espiritual'
};

/* ============================================================
   SISTEMA ECONOMICO
   ============================================================ */
function initWallets(lista) {
  wallets = {};
  lista.forEach(c => {
    const id = c.id || ('CL' + String(c.numero_lista).padStart(3, '0'));
    wallets[id] = 1000;
  });
}

function getConsultorId(c) {
  return c.id || ('CL' + String(c.numero_lista).padStart(3, '0'));
}

/* transferir removida - transacoes sao exclusivas da cidade 3D */

function calcGini(values) {
  if (!values || values.length === 0) return 0;
  const sorted = [...values].sort((a, b) => a - b);
  const n = sorted.length;
  const mean = sorted.reduce((s, v) => s + v, 0) / n;
  if (mean === 0) return 0;
  let sumDiff = 0;
  for (let i = 0; i < n; i++) {
    for (let j = 0; j < n; j++) {
      sumDiff += Math.abs(sorted[i] - sorted[j]);
    }
  }
  return sumDiff / (2 * n * n * mean);
}

function getWalletBalance(consultorId) {
  return wallets[consultorId] || 0;
}

function getNomeById(id) {
  const c = consultores.find(x => getConsultorId(x) === id);
  return c ? (c.nome_exibicao || c.nome) : id;
}

/* findConsultorByName removida - buscas de nome eram para transacoes (cidade 3D) */

/* detectarTransacao removido - transacoes sao exclusivas da cidade 3D, nao da assembleia */

/* ============================================================
   CLASSIFICACAO DE MENSAGENS
   ============================================================ */
function classificarMensagem(texto) {
  const t = texto.toLowerCase();

  // Negociacao (prioridade alta — detectar antes de apoio/oposicao)
  if (/\b(ofer[eç][ao]\s*[Ξ$]?\s*\d|cobr[oa]\s*[Ξ$]?\s*\d|pag[oa]\s*[Ξ$]?\s*\d|troc[ao].*por|negoci[ao]|proponho.*troca|alianca\s+economica)\b/i.test(t)) return 'negociacao';

  // PRIORIDADE 1: Apoio/oposicao explícita no inicio
  if (/^(apoio\b|sou a favor|concordo com|endosso|subscrevo|voto sim)/.test(t)) return 'apoio';
  if (/^(oponho|me oponho|discordo|rejeito|sou contra|voto n[aã]o)/.test(t)) return 'oposicao';

  // PRIORIDADE 2: Apoio/oposição em qualquer posicao
  if (/\b(apoio a proposta de|sou a favor d[ao]|voto sim|endosso a proposta)\b/.test(t)) return 'apoio';
  if (/\b(oponho-me a|sou contra [ao]|voto não|rejeito a proposta)\b/.test(t)) return 'oposicao';

  // PRIORIDADE 3: Proposta nova
  if (/\b(proponho artigo|proponho que|proposta:|sugiro que|artigo\s*\d+\s*:)\b/.test(t) && !/emenda/.test(t)) return 'proposta';

  // PRIORIDADE 4: Emenda
  if (/\b(emenda|proponho em substituição|proponho modificação|com a ressalva|adendo)\b/.test(t)) return 'emenda';

  // PRIORIDADE 5: Proposta generica
  if (/\b(proponho|proponhamos|regra\s*:|lei\s*:|devemos estabelecer)\b/.test(t)) return 'proposta';

  // Provocacao
  if (/\b(pat[eé]tico|piada|rid[ií]culo|covardes|fracos|ingenuidade|bobagem|besteira|hip[oó]critas|absurdo)\b/.test(t)) return 'provocacao';
  // Conciliacao
  if (/\b(acalm|diálogo|equil[ií]brio|ouçamos|ponderemos|meio[ -]?termo|concilia|modera[çc])\b/.test(t)) return 'conciliacao';
  return 'fala';
}

/* ============================================================
   FILTRO ANTI-CLICHE
   ============================================================ */
function isMensagemVazia(texto) {
  const t = texto.toLowerCase();
  const len = texto.length;

  const clichesExatos = [
    'concordo plenamente', 'excelente ponto', 'brilhante colocação',
    'muito bem colocado', 'palavras sábias', 'tenho que concordar',
    'não poderia concordar mais', 'é exatamente isso',
    'juntos somos mais fortes', 'o futuro nos aguarda',
    'devemos refletir sobre isso', 'é preciso sabedoria',
    'a união faz a força', 'precisamos trabalhar juntos',
    'estou impressionado', 'que momento histórico'
  ];
  for (const c of clichesExatos) {
    if (t.includes(c) && len < 120) return true;
  }

  const padroesCliche = [
    /^(caros|prezados|nobres|estimados)\s+(colegas|companheiros|amigos)/,
    /como\s+(bem\s+)?disse\s+\w+.*concordo/,
    /devemos\s+(todos\s+)?refletir/,
    /é\s+fundamental\s+que\s+trabalhemos\s+juntos/,
    /a\s+sabedoria\s+(nos\s+)?ensina/,
    /neste\s+momento\s+histórico/,
    /com\s+todo\s+respeito.*concordo/,
  ];
  for (const p of padroesCliche) {
    if (p.test(t) && len < 150) return true;
  }

  const temSubstancia = /\b(proponho|artigo|voto|apoio|oponho|emenda|regra|proposta|estabelecer|determinar|proibir|garantir|punir|expuls|direito|dever|obrigaç|ofer[eç]|cobr|pag[oa]|Ξ|\d+\s*coins?|transfer|negocia)/i.test(t);
  const temPosicionamento = /\b(concordo com|discordo de|apoio a|rejeito|sou contra|sou a favor|defendo que|oponho-me)/i.test(t);

  if (len < 80 && !temSubstancia && !temPosicionamento) return true;

  return false;
}

/* ============================================================
   INICIALIZACAO
   ============================================================ */
async function init() {
  sessionId = localStorage.getItem('vila_jogo_session') || crypto.randomUUID();
  localStorage.setItem('vila_jogo_session', sessionId);
  document.getElementById('sessionBadge').textContent = 'Sessão: ' + sessionId.slice(0, 8);

  // Carregar consultores
  document.getElementById('feed').innerHTML = '<div class="msg tipo-sistema"><div class="msg-text">Carregando 142 consultores lendários...</div></div>';
  try {
    consultores = await carregarConsultores();
    console.log(`[INIT] ${consultores.length} consultores carregados`);
    document.getElementById('feed').innerHTML = '';
  } catch (e) {
    console.error('[INIT] Erro ao carregar consultores:', e);
    document.getElementById('feed').innerHTML = '<div class="msg tipo-sistema"><div class="msg-text">Erro ao carregar consultores. Verifique o console.</div></div>';
    return;
  }

  // Inicializar wallets (economia e na cidade 3D, aqui so debate regras)
  initWallets(consultores);

  // Tentar restaurar estado completo do backend primeiro
  let backendLoaded = false;
  try {
    const [estadoRes, msgsRes, artigosRes] = await Promise.allSettled([
      fetch(BACKEND_API + '/estado/carregar/jogo?sessao_id=' + sessionId),
      fetch(BACKEND_API + '/mensagens/carregar/constituicao?sessao_id=' + sessionId + '&limit=200'),
      fetch(BACKEND_API + '/constituicao/artigos')
    ]);

    // Restaurar estado global (roundNum, propostas, helenaInsights)
    if (estadoRes.status === 'fulfilled' && estadoRes.value.ok) {
      const estadoData = await estadoRes.value.json();
      if (estadoData.dados) {
        const d = estadoData.dados;
        if (d.roundNum) roundNum = d.roundNum;
        if (d.helenaInsights && d.helenaInsights.length > 0) helenaInsights = d.helenaInsights;
        if (d.propostas && d.propostas.length > 0) {
          propostas = d.propostas.map(p => ({
            ...p,
            apoios: new Set(p.apoios || []),
            oposicoes: new Set(p.oposicoes || [])
          }));
        }
        // Restaurar estado do processo legislativo
        if (d.faseAtual) faseAtual = d.faseAtual;
        if (d.pautaIndex !== undefined) pautaIndex = d.pautaIndex;
        if (d.numOradoresDiscussao !== undefined) numOradoresDiscussao = d.numOradoresDiscussao;
        if (d.rodadaUltimaFase !== undefined) rodadaUltimaFase = d.rodadaUltimaFase;
        if (d.propostaEmPauta) propostaEmPauta = {
          ...d.propostaEmPauta,
          apoios: new Set(d.propostaEmPauta.apoios || []),
          oposicoes: new Set(d.propostaEmPauta.oposicoes || [])
        };
        console.log('[INIT] Estado restaurado do backend (rodada ' + roundNum + ', fase ' + faseAtual + ')');
      }
    }

    // Restaurar mensagens do backend
    if (msgsRes.status === 'fulfilled' && msgsRes.value.ok) {
      const msgsData = await msgsRes.value.json();
      if (msgsData.mensagens && msgsData.mensagens.length > 0) {
        mensagens = msgsData.mensagens;
        backendLoaded = true;
        console.log('[INIT] Mensagens restauradas do backend:', mensagens.length);
      }
    }

    // Restaurar artigos do backend
    if (artigosRes.status === 'fulfilled' && artigosRes.value.ok) {
      const artigosData = await artigosRes.value.json();
      if (artigosData.artigos && artigosData.artigos.length > 0) {
        artigos = artigosData.artigos;
        artigoCounter = artigos.length;
        artigos.forEach(a => { if (a.status === 'consenso') artigosSalvosBackend.add(a.numero); });
        console.log('[INIT] Artigos restaurados do backend:', artigos.length);
      }
    }
  } catch(e) {
    console.warn('[INIT] Backend indisponivel, usando localStorage como fallback');
  }

  // Fallback: localStorage se backend nao retornou dados
  if (!backendLoaded) {
    try {
      const local = JSON.parse(localStorage.getItem('vila_jogo_msgs_' + sessionId) || '[]');
      if (local.length > 0) {
        mensagens = local;
        console.log('[INIT] ' + local.length + ' mensagens restauradas do localStorage');
      }
    } catch (e) {}
  }
  if (artigos.length === 0) {
    try {
      const localArt = JSON.parse(localStorage.getItem('vila_jogo_artigos_' + sessionId) || '[]');
      if (localArt.length > 0) {
        artigos = localArt;
        artigoCounter = artigos.length;
      }
    } catch (e) {}
  }
  if (helenaInsights.length === 0) {
    try {
      const localH = JSON.parse(localStorage.getItem('vila_jogo_helena_' + sessionId) || '[]');
      if (localH.length > 0) helenaInsights = localH;
    } catch (e) {}
  }
  if (propostas.length === 0) {
    try {
      const localP = JSON.parse(localStorage.getItem('vila_jogo_propostas_' + sessionId) || '[]');
      if (localP.length > 0) {
        propostas = localP.map(p => ({
          ...p,
          apoios: new Set(p.apoios || []),
          oposicoes: new Set(p.oposicoes || [])
        }));
      }
    } catch (e) {}
  }

  // Detectar sessão antiga sem processo legislativo e forçar reset
  const temRegimento = artigos.some(a => String(a.numero).startsWith('RI-'));
  if (mensagens.length > 0 && !temRegimento) {
    console.warn('[INIT] Sessão antiga detectada (sem Regimento Interno). Forçando nova sessão.');
    mensagens = [];
    artigos = [];
    propostas = [];
    helenaInsights = [];
    roundNum = 0;
    speakersSet = new Set();
    lastSpeakers = [];
    artigoCounter = 0;
    faseAtual = FASE.PAUTA;
    propostaEmPauta = null;
    pautaIndex = 0;
    numOradoresDiscussao = 0;
    rodadaUltimaFase = 0;
    votosRodada = { sim: new Set(), nao: new Set(), abstencao: new Set() };
    // Limpar localStorage da sessão antiga
    localStorage.removeItem('vila_jogo_msgs_' + sessionId);
    localStorage.removeItem('vila_jogo_artigos_' + sessionId);
    localStorage.removeItem('vila_jogo_helena_' + sessionId);
    localStorage.removeItem('vila_jogo_propostas_' + sessionId);
  }

  // Renderizar mensagens existentes
  if (mensagens.length > 0) {
    mensagens.forEach(m => renderMessage(m, false));
    // Usar roundNum do backend se ja foi carregado; senao, calcular das mensagens
    if (roundNum === 0) roundNum = mensagens.filter(m => m.tipo !== 'sistema' && m.tipo !== 'usuario').length;
    mensagens.forEach(m => { if (m.consultorId) speakersSet.add(m.consultorId); });
    artigos.forEach(a => renderArticle(a, false));
    helenaInsights.forEach(h => renderHelenaInsight(h, false));
  }

  updateStats();
  updateEconomyTab();
  updateCurrencyBadge();
  scrollToBottom();

  // Auto-save a cada 60 segundos
  const _autoSaveInterval = setInterval(() => {
    fetch(BACKEND_API + '/estado/salvar', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({
        modulo: 'jogo', sessao_id: sessionId,
        dados: {
          roundNum, artigos,
          propostas: propostas.map(p => ({...p, apoios: Array.from(p.apoios || []), oposicoes: Array.from(p.oposicoes || [])})),
          helenaInsights, mensagensCount: mensagens.length,
          faseAtual, pautaIndex, numOradoresDiscussao, rodadaUltimaFase,
          propostaEmPauta: propostaEmPauta ? {...propostaEmPauta, apoios: Array.from(propostaEmPauta.apoios || []), oposicoes: Array.from(propostaEmPauta.oposicoes || [])} : null
        },
        timestamp: Date.now()
      })
    }).catch(() => {});
  }, 60000);
}

/* ============================================================
   PERSISTENCIA
   ============================================================ */
function salvarMensagem(msg) {
  try {
    const local = JSON.parse(localStorage.getItem('vila_jogo_msgs_' + sessionId) || '[]');
    local.push(msg);
    if (local.length > 500) local.splice(0, local.length - 500);
    localStorage.setItem('vila_jogo_msgs_' + sessionId, JSON.stringify(local));
  } catch (e) {}

  // Backend (fire and forget)
  fetch(BACKEND_API + '/mensagens/salvar', {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ modulo: 'constituicao', sessao_id: sessionId, mensagens: [msg] })
  }).catch(() => {});
}

function salvarArtigos() {
  try {
    localStorage.setItem('vila_jogo_artigos_' + sessionId, JSON.stringify(artigos));
  } catch (e) {}
  // Salvar no backend apenas artigos novos (evita duplicatas)
  artigos.filter(a =>
    a.status === 'consenso' &&
    Number.isInteger(a.numero) &&
    !artigosSalvosBackend.has(a.numero)
  ).forEach(a => {
    fetch(BACKEND_API + '/constituicao/artigo', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({
        numero: a.numero,
        texto: a.texto,
        proponente: a.proponente,
        apoios: Array.isArray(a.apoios) ? a.apoios : Array.from(a.apoios || []),
        oposicoes: Array.isArray(a.oposicoes) ? a.oposicoes : Array.from(a.oposicoes || []),
        status: 'consenso',
        tipo: a.tipo || 'Principios Fundamentais',
        rodada: a.rodada || 0
      })
    }).then((response) => {
      if (!response.ok) {
        throw new Error(`Falha ao salvar artigo ${a.numero}: ${response.status}`);
      }
      artigosSalvosBackend.add(a.numero);
    }).catch((error) => {
      console.error('[ARTIGO] Erro ao salvar no backend:', error);
    });
  });
}

/* salvarWallets e salvarTransacoes removidos - economia e exclusiva da cidade 3D */

function salvarHelena() {
  try {
    localStorage.setItem('vila_jogo_helena_' + sessionId, JSON.stringify(helenaInsights));
  } catch (e) {}
  // Salvar no backend
  if (helenaInsights.length > 0) {
    const latest = helenaInsights[helenaInsights.length - 1];
    fetch(BACKEND_API + '/helena/insight', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ texto: latest.texto, modulo: 'constituicao', rodada: latest.rodada, metricas: { numArtigos: latest.numArtigos } })
    }).catch(() => {});
  }
}

function salvarPropostas() {
  try {
    const toSave = propostas.map(p => ({
      ...p,
      apoios: Array.from(p.apoios || []),
      oposicoes: Array.from(p.oposicoes || [])
    }));
    localStorage.setItem('vila_jogo_propostas_' + sessionId, JSON.stringify(toSave));
  } catch (e) {}
}

/* ============================================================
   SELECAO DO PROXIMO ORADOR — SISTEMA DE TRIBUNA
   ============================================================ */
function selecionarOrador(depth = 0) {
  if (consultores.length === 0) return null;

  const bloqueados = new Set(lastSpeakers.slice(-TRIBUNA_GAP));

  let bilateralBlock = null;
  if (mensagens.length >= 2) {
    const penult = mensagens[mensagens.length - 2];
    const ult = mensagens[mensagens.length - 1];
    if (penult.consultorId && ult.consultorId && penult.consultorId !== ult.consultorId) {
      bilateralBlock = penult.consultorId;
    }
  }

  const scores = consultores.map(c => {
    const cId = getConsultorId(c);
    let score = 0;

    if (bloqueados.has(cId)) return { c, score: -999 };
    if (cId === bilateralBlock) return { c, score: -999 };

    if (!speakersSet.has(cId)) score += 20;

    const extro = c.nivel_extroversao || 5;
    score += extro * 0.6;

    // Priorizar por fase processual
    const temaAtual = pautaIndex < PAUTA_OBRIGATORIA.length ? PAUTA_OBRIGATORIA[pautaIndex] : null;
    if (temaAtual && faseAtual === FASE.APRESENTACAO) {
      // Na apresentação, priorizar quem tem expertise no tema
      const temaLower = temaAtual.tema.toLowerCase();
      const expertise = (c.areas_expertise || []).join(' ').toLowerCase();
      if (temaLower.includes('economia') && /econ|finan|invest|capital|negoc/i.test(expertise)) score += 15;
      if (temaLower.includes('governo') && /politi|govern|estrat|lider/i.test(expertise)) score += 15;
      if (temaLower.includes('direito') && /jurid|direi|lei|justic/i.test(expertise)) score += 15;
      if (temaLower.includes('punic') && /jurid|direi|lei|penal|justic/i.test(expertise)) score += 15;
      if (temaLower.includes('princip') && /filos|etic|valor|moral|espirit/i.test(expertise)) score += 15;
    }

    if (faseAtual === FASE.VOTACAO) {
      // Na votação, todos votam — priorizar quem ainda não votou
      const jaVotou = votosRodada.sim.has(c.nome_exibicao) || votosRodada.nao.has(c.nome_exibicao) || votosRodada.abstencao.has(c.nome_exibicao);
      if (jaVotou) return { c, score: -999 }; // Já votou, não fala de novo
      score += 20; // Priorizar votantes
    }

    if (faseAtual === FASE.DISCUSSAO) {
      // Na discussão, alternar a favor e contra para pluralidade
      const ultimoTipo = mensagens.length > 0 ? mensagens[mensagens.length - 1].tipo : '';
      const orientacao = (c.orientacao_politica || '').toLowerCase();
      // Se último foi apoio, priorizar quem tem visão diferente
      if (ultimoTipo === 'apoio' && /conservador|direita|liberal/i.test(orientacao)) score += 5;
      if (ultimoTipo === 'oposicao' && /progressist|esquerda|social/i.test(orientacao)) score += 5;
    }

    if (mensagens.length > 0) {
      const recentText = mensagens.slice(-8).map(m => m.texto).join(' ').toLowerCase();
      const expertise = (c.areas_expertise || []).map(e => e.toLowerCase());
      let relevancia = 0;
      expertise.forEach(exp => {
        const words = exp.split(/\s+/);
        words.forEach(w => { if (w.length > 4 && recentText.includes(w)) relevancia++; });
      });
      if (/\b(moeda|dinheiro|econ|coin|Ξ|transaç|mercado|capital|imposto|taxa)\b/.test(recentText)) {
        if ((c.areas_expertise || []).some(e => /econ|finan|invest|capital/i.test(e))) score += 10;
      }
      score += Math.min(relevancia * 3, 12);
    }

    score += (c.nivel_carisma || 5) * 0.3;
    score += (c.presenca_publica || 5) * 0.3;

    const catCount = lastSpeakers.filter(id => {
      const sp = consultores.find(cc => getConsultorId(cc) === id);
      return sp && sp.categoria === c.categoria;
    }).length;
    if (catCount === 0) score += 8;

    score += Math.random() * 15;

    return { c, score };
  });

  const validos = scores.filter(s => s.score > -900);
  if (validos.length === 0) {
    if (depth >= 3) return consultores[Math.floor(Math.random() * consultores.length)];
    lastSpeakers.splice(0, Math.floor(lastSpeakers.length / 2));
    return selecionarOrador(depth + 1);
  }

  validos.sort((a, b) => b.score - a.score);
  return validos[0].c;
}

/* ============================================================
   GERACAO DE FALA VIA IA
   ============================================================ */
async function gerarFala(consultor) {
  const consultorId = getConsultorId(consultor);

  // Contexto das ultimas 18 mensagens
  const contexto = mensagens.slice(-18).map(m => {
    if (m.tipo === 'sistema') return `[SISTEMA]: ${m.texto}`;
    if (m.tipo === 'usuario') return `[IGOR MORAIS]: ${m.texto}`;
    return `[${m.nome}]: ${m.texto}`;
  }).join('\n');

  // Situacao
  const totalFalas = mensagens.filter(m => m.tipo !== 'sistema' && m.tipo !== 'usuario').length;
  const numArtigos = artigos.filter(a => a.status === 'consenso').length;
  const numPropostas = propostas.length;

  let artigosAprovados = '';
  if (artigos.length > 0) {
    artigosAprovados = '\n\nARTIGOS JA APROVADOS:\n' + artigos
      .filter(a => a.status === 'consenso')
      .map(a => `Art. ${a.numero}: ${a.texto.substring(0, 120)}`)
      .join('\n');
  }

  let propostasAtivas = '';
  const propostasDebate = propostas.filter(p => p.status === 'debate' || p.status === 'formacao');
  if (propostasDebate.length > 0) {
    propostasAtivas = '\n\nPROPOSTAS EM DEBATE (vote apoio ou oposicao):\n' + propostasDebate
      .slice(-5)
      .map(p => `- ${p.proponente}: "${p.texto.substring(0, 100)}..." (${p.apoios.size} apoios, ${p.oposicoes.size} oposicoes)`)
      .join('\n');
  }

  // Economia: apenas debate de regras na assembleia

  // Situação baseada na fase processual atual
  const temaAtual = pautaIndex < PAUTA_OBRIGATORIA.length ? PAUTA_OBRIGATORIA[pautaIndex] : null;
  let situacao = '';
  let instrucaoFase = '';

  if (faseAtual === FASE.APRESENTACAO) {
    situacao = `FASE: APRESENTAÇÃO DE PROPOSTAS. Tema da Ordem do Dia: "${temaAtual ? temaAtual.tema : 'Livre'}". ${temaAtual ? temaAtual.desc : ''}.`;
    instrucaoFase = `Voce deve APRESENTAR UMA PROPOSTA DE ARTIGO sobre o tema "${temaAtual ? temaAtual.tema : 'livre'}". Use o formato: "Proponho Artigo: [texto completo do artigo]". A proposta deve ser concreta, clara e implementável. Se outra proposta já foi apresentada e você concorda, diga "Apoio a proposta de [nome]" e explique brevemente por quê. Se discorda, apresente uma proposta ALTERNATIVA melhor.`;
  } else if (faseAtual === FASE.DISCUSSAO) {
    const proponenteNome = propostaEmPauta ? propostaEmPauta.proponente : '';
    const textoResumo = propostaEmPauta ? propostaEmPauta.texto.substring(0, 200) : '';
    situacao = `FASE: DISCUSSÃO. Proposta em pauta (de ${proponenteNome}): "${textoResumo}". Oradores: ${numOradoresDiscussao}/${MAX_ORADORES_DISCUSSAO}. ${numOradoresDiscussao >= MIN_ORADORES_DISCUSSAO ? 'DISCUSSÃO PODE SER ENCERRADA para votação.' : `Faltam ${MIN_ORADORES_DISCUSSAO - numOradoresDiscussao} oradores para quórum mínimo.`}`;
    instrucaoFase = `Voce esta na fase de DISCUSSÃO. Analise a proposta em pauta e posicione-se:
- Se CONCORDA: "Declaro voto favorável. [razão breve baseada na sua visão de mundo]"
- Se DISCORDA: "Declaro voto contrário. [razão breve baseada na sua visão de mundo]"
- Se quer EMENDAR: "Proponho emenda: [alteração específica ao texto]"
- Se quer encerrar discussão: "Requeiro encerramento da discussão e votação"
NÃO repita os argumentos de quem já falou. Traga perspectiva NOVA da sua área de expertise.`;
  } else if (faseAtual === FASE.VOTACAO) {
    const textoResumo = propostaEmPauta ? propostaEmPauta.texto.substring(0, 150) : '';
    situacao = `FASE: VOTAÇÃO NOMINAL. Proposta: "${textoResumo}". Votos até agora: ${votosRodada.sim.size} SIM, ${votosRodada.nao.size} NÃO, ${votosRodada.abstencao.size} abstenções.`;
    instrucaoFase = `VOTAÇÃO EM CURSO. Você DEVE votar usando EXATAMENTE um destes formatos:
- "Voto SIM." seguido de justificativa breve (1 frase)
- "Voto NÃO." seguido de justificativa breve (1 frase)
- "Abstenção." seguido de motivo breve
Apenas seu VOTO. Sem discursos.`;
  } else {
    situacao = `Aguardando próximo tema da Ordem do Dia.`;
    instrucaoFase = `O Presidente vai anunciar o próximo tema. Aguarde.`;
  }

  // Mapear orientação política para instrução de coerência
  const orientacao = (consultor.orientacao_politica || '').toLowerCase();
  let instrucaoIdeologica = '';
  if (/conservador|direita|liberal.?economico|libertario/i.test(orientacao)) {
    instrucaoIdeologica = 'Voce defende: propriedade privada, livre mercado, estado minimo, merito individual, tradicao, ordem. Desconfia de intervencionismo estatal e coletivismo.';
  } else if (/progressist|esquerda|social.?democrat|socialista/i.test(orientacao)) {
    instrucaoIdeologica = 'Voce defende: justica social, intervencao estatal, direitos coletivos, redistribuicao, servicos publicos. Desconfia do livre mercado irrestrito.';
  } else if (/centrist|moderad|pragmat/i.test(orientacao)) {
    instrucaoIdeologica = 'Voce busca equilibrio pragmatico. Aceita tanto iniciativa privada quanto intervencao estatal conforme o caso. Foca em resultados praticos.';
  } else if (/anarqui|libert/i.test(orientacao)) {
    instrucaoIdeologica = 'Voce desconfia de qualquer autoridade centralizada. Defende auto-organizacao, consenso voluntario, minimo de regras possiveis.';
  } else if (/autoritari|autoc/i.test(orientacao)) {
    instrucaoIdeologica = 'Voce acredita em lideranca forte e ordem. Regras claras, punicoes severas, hierarquia definida. Eficiencia sobre processo.';
  }

  const systemPrompt = `Voce e ${consultor.nome_exibicao}, clone digital perfeito de ${consultor.nome}. Vila INTEIA, Assembleia Constituinte.

PERSONALIDADE: ${consultor.personalidade_resumo || ''}
TOM: ${consultor.tom_voz || 'direto'} | ESTILO: ${consultor.estilo_argumentacao || 'direto'}
${consultor.instrucao_comportamental || ''}
EXPERTISE: ${(consultor.areas_expertise || []).join(', ')}
EXPRESSOES TIPICAS: ${(consultor.expressoes_tipicas || []).slice(0, 3).join('; ')}

POSICAO IDEOLOGICA (OBRIGATORIA — suas falas DEVEM refletir isso):
Orientacao: ${consultor.orientacao_politica || 'pragmatico'}
${instrucaoIdeologica}
Visao de poder: ${consultor.visao_poder || ''}
Visao etica: ${consultor.visao_etica || ''}
Visao economica: ${consultor.visao_dinheiro || ''}

SUAS POSICOES DEVEM SER COERENTES com quem voce e. Se ${consultor.nome_exibicao} na vida real defenderia X, voce DEVE defender X. Nao concorde por educacao. Discorde se seu personagem discordaria.

${situacao}

${instrucaoFase}

CONSTITUICAO VIGENTE:
${artigosAprovados || 'Regimento Interno aprovado (5 artigos processuais). Nenhum artigo substantivo ainda.'}

${propostasAtivas}

REGRAS PROCESSUAIS (Regimento Interno vigente):
- Uma proposta por vez. Nao proponha artigo novo se ha proposta em discussao
- Fases: Apresentacao → Discussao (min 3, max 8 oradores) → Votacao nominal
- Na votacao: "Voto SIM", "Voto NAO" ou "Abstencao" — apenas isso
- Emendas sao apresentadas na fase de discussao
- NAO trave discussao bilateral. Dirija-se a ASSEMBLEIA, nao a um orador
- O Presidente (Rui Barbosa) conduz os trabalhos

FORMATO: 2-4 frases. Direto ao ponto. Fale como ${consultor.nome_exibicao} falaria. Portugues brasileiro.

PROIBIDO: frases vazias, cliches motivacionais, elogios genericos, concordar por educacao, repetir argumentos ja feitos.`;

  const userPrompt = `ASSEMBLEIA CONSTITUINTE — ${faseAtual.toUpperCase()}

${contexto || '[O Presidente abriu a sessao. Ninguem falou ainda.]'}

FASE ATUAL: ${faseAtual.toUpperCase()}
SUA VEZ. ${instrucaoFase}
Escreva 2-4 frases. Apenas sua fala, sem aspas, sem prefixos, sem nome.`;

  const _ctrl = new AbortController(); const _tid = setTimeout(() => _ctrl.abort(), 12000);
  try {
    const response = await fetch(OMNI_URL, {
      method: 'POST', signal: _ctrl.signal,
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: OMNI_MODEL,
        messages: [
          { role: 'user', content: '[INSTRUCAO]\n' + systemPrompt + '\n\n[TAREFA]\n' + userPrompt }
        ],
        max_tokens: 200,
        temperature: 0.75
      })
    });
    clearTimeout(_tid);

    if (!response.ok) throw new Error(`API retornou ${response.status}`);

    const data = await response.json();
    let text = (data.choices?.[0]?.message?.content || '').trim();

    // Limpar
    text = text.replace(/^["']|["']$/g, '').trim();
    const prefixRegex = new RegExp(`^${consultor.nome_exibicao}\\s*:\\s*`, 'i');
    text = text.replace(prefixRegex, '').trim();

    if (text && isMensagemVazia(text)) {
      console.warn(`[FILTRO] Fala de ${consultor.nome_exibicao} rejeitada por cliche`);
      return null;
    }

    return text || null;
  } catch (e) {
    console.error(`[IA] Erro gerando fala de ${consultor.nome_exibicao}:`, e);
    return null;
  }
}

/* ============================================================
   HELENA ANALYSIS
   ============================================================ */
async function helenaAnalise() {
  const recentMsgs = mensagens.slice(-30);
  const recentTrades = transacoes.slice(-20);

  const topWalletsList = Object.entries(wallets)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10);
  const bottomWalletsList = Object.entries(wallets)
    .sort((a, b) => a[1] - b[1])
    .slice(0, 5);
  const totalTradesCount = transacoes.length;
  const volumeTotal = transacoes.reduce((s, t) => s + t.valor, 0);
  const gini = calcGini(Object.values(wallets));

  const prompt = `Voce e Helena Strategos, cientista-chefe da INTEIA. Analise esta assembleia constituinte com sistema economico.

DEBATE (ultimas 30 msgs):
${recentMsgs.map(m => `${m.nome}: ${m.texto}`).join('\n')}

ECONOMIA:
- ${totalTradesCount} transacoes totais, volume: Ξ${volumeTotal}
- Coeficiente de Gini: ${gini.toFixed(3)} (0=igualdade, 1=concentracao)
- Top wallets: ${topWalletsList.map(([id, v]) => `${getNomeById(id)}: Ξ${v}`).join(', ')}
- Mais pobres: ${bottomWalletsList.map(([id, v]) => `${getNomeById(id)}: Ξ${v}`).join(', ')}
- Transacoes recentes: ${recentTrades.map(t => `${getNomeById(t.de)}->Ξ${t.valor}->${getNomeById(t.para)}: ${t.motivo}`).join('; ')}

CONSTITUICAO:
- ${artigos.filter(a => a.status === 'consenso').length} artigos aprovados
${artigos.map(a => `Art. ${a.numero}: ${a.texto.substring(0, 100)}`).join('\n')}

Gere 3-5 insights estrategicos CURTOS (1-2 frases cada). Foque em:
- Aliancas e coalizoes formadas
- Conflitos ideologicos emergentes
- Padroes economicos (quem acumula, quem distribui, quem negocia votos)
- Dinamicas de poder e lideranca
- Riscos e oportunidades para a estabilidade da comunidade
- Comparacoes com sistemas politicos e economicos reais

Formato: numere de 1 a 5, cada insight em 1-2 frases diretas. Sem introducoes.`;

  const _hCtrl = new AbortController(); const _hTid = setTimeout(() => _hCtrl.abort(), 12000);
  try {
    const response = await fetch(OMNI_URL, {
      method: 'POST', signal: _hCtrl.signal,
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: OMNI_MODEL,
        messages: [
          { role: 'user', content: '[INSTRUCAO]\nVoce e Helena Strategos, cientista politica e analista chefe da INTEIA. Responda em portugues brasileiro, direto ao ponto.\n\n[TAREFA]\n' + prompt }
        ],
        max_tokens: 200,
        temperature: 0.6
      })
    });
    clearTimeout(_hTid);

    if (!response.ok) throw new Error(`Helena API: ${response.status}`);

    const data = await response.json();
    const text = (data.choices?.[0]?.message?.content || '').trim();

    if (text) {
      const insight = {
        texto: text,
        rodada: roundNum,
        gini: gini,
        totalTrades: totalTradesCount,
        volumeTotal: volumeTotal,
        numArtigos: artigos.filter(a => a.status === 'consenso').length,
        timestamp: Date.now()
      };
      helenaInsights.push(insight);
      renderHelenaInsight(insight, true);
      salvarHelena();
      console.log('[HELENA] Insight gerado na rodada', roundNum);
    }
  } catch (e) {
    console.error('[HELENA] Erro:', e);
  }
}

/* ============================================================
   DETECCAO DE CONSENSO
   ============================================================ */
function analisarConsenso() {
  const msgsRecentes = mensagens.slice(-30);

  msgsRecentes.forEach((msg, idx) => {
    if (msg.tipo !== 'proposta') return;
    if (msg._consensoAnalisado) return;

    const seguintes = msgsRecentes.slice(idx + 1);
    const apoios = new Set();
    const oposicoes = new Set();

    seguintes.forEach(s => {
      const texto = (s.texto || '').toLowerCase();
      const nomeProponente = (msg.nome || '').toLowerCase();
      const refProposta = texto.includes(nomeProponente) ||
        texto.includes('proposta') || texto.includes('artigo') ||
        texto.includes('concordo') || texto.includes('discordo') ||
        texto.includes('apoio') || texto.includes('rejeito');

      if (!refProposta) return;

      if (s.tipo === 'apoio' || s.tipo === 'emenda') apoios.add(s.consultorId || s.nome);
      if (s.tipo === 'oposicao') oposicoes.add(s.consultorId || s.nome);
      if (/\b(apoio a proposta|apoio a emenda|sou a favor|concordo com)\b/.test(texto)) {
        apoios.add(s.consultorId || s.nome);
      }
    });

    const jaRastreada = propostas.find(p => p.msgIndex === mensagens.indexOf(msg));
    if (!jaRastreada) {
      propostas.push({
        msgIndex: mensagens.indexOf(msg),
        texto: msg.texto,
        proponente: msg.nome,
        apoios: apoios,
        oposicoes: oposicoes,
        status: 'debate'
      });
    } else {
      apoios.forEach(a => jaRastreada.apoios.add(a));
      oposicoes.forEach(o => jaRastreada.oposicoes.add(o));
    }
  });

  // Verificar consenso
  propostas.forEach(p => {
    if (p.status === 'aprovado') return;

    const numApoios = p.apoios.size;
    const numOposicoes = p.oposicoes.size;

    // Aprovação por consenso: 2+ apoios e mais apoios que oposições
    if (numApoios >= 2 && numApoios > numOposicoes) {
      // Controle constitucional: juristas podem vetar
      const juristasContra = Array.from(p.oposicoes).filter(id => {
        const c = consultores.find(x => getConsultorId(x) === id);
        return c && c.categoria === 'jurista_lendario';
      });
      // Se 2+ juristas vetam, nao aprova (tribunal constitucional)
      if (juristasContra.length >= 2) {
        const anuncio = {
          tipo: 'sistema', nome: 'SISTEMA',
          texto: `Artigo VETADO pelo Tribunal Constitucional (${juristasContra.length} juristas contra). Proposta de ${p.proponente} precisa ser reformulada.`,
          hora: getHora(), rodada: roundNum, timestamp: Date.now()
        };
        mensagens.push(anuncio);
        renderMessage(anuncio);
        p.status = 'vetado';
        salvarPropostas();
        return;
      }

      p.status = 'aprovado';
      artigoCounter++;

      // Classificar tipo de artigo
      let tipoArtigo = 'Princípios Fundamentais';
      const tl = p.texto.toLowerCase();
      if (/\b(moeda|coin|Ξ|econ|imposto|taxa|dinheiro|capital|mercado|comerci)\b/.test(tl)) tipoArtigo = 'Economia e Moeda';
      else if (/\b(puni|expuls|ban|sanc|multa|infra)\b/.test(tl)) tipoArtigo = 'Punições e Expulsão';
      else if (/\b(direito|dever|liber|priv|garanti|proteg)\b/.test(tl)) tipoArtigo = 'Direitos e Deveres';
      else if (/\b(govern|presid|conselho|voto|eleic|cargo|poder|autorid)\b/.test(tl)) tipoArtigo = 'Organização e Governança';
      else if (/\b(emend|revis|alter|reform|modific)\b/.test(tl)) tipoArtigo = 'Emendas e Revisão';
      else if (/\b(process|tramit|quorum|procedim|deliber)\b/.test(tl)) tipoArtigo = 'Processo Legislativo';

      const artigo = {
        numero: artigoCounter,
        texto: p.texto,
        proponente: p.proponente,
        apoios: Array.from(p.apoios),
        oposicoes: Array.from(p.oposicoes),
        status: 'consenso',
        tipo: tipoArtigo,
        rodada: roundNum
      };
      artigos.push(artigo);
      renderArticle(artigo, true);
      salvarArtigos();
      salvarPropostas();

      const anuncio = {
        tipo: 'sistema', nome: 'SISTEMA',
        texto: `ARTIGO ${artigo.numero} APROVADO por consenso (${numApoios} a favor, ${numOposicoes} contra). Tipo: ${tipoArtigo}. Proposto por ${p.proponente}.`,
        hora: getHora(), rodada: roundNum, timestamp: Date.now()
      };
      mensagens.push(anuncio);
      renderMessage(anuncio);

    } else if (numApoios >= 2 && numOposicoes < 2 && !p._formacaoRenderizada) {
      p.status = 'formacao';
      p._formacaoRenderizada = true;
      const artigo = {
        numero: '?',
        texto: p.texto,
        proponente: p.proponente,
        apoios: Array.from(p.apoios),
        oposicoes: Array.from(p.oposicoes),
        status: 'formacao',
        tipo: '',
        rodada: roundNum
      };
      renderArticle(artigo, true);
    }
  });

  salvarPropostas();
}

/* ============================================================
   RENDERIZACAO
   ============================================================ */
function renderMessage(msg, animate = true) {
  const feed = document.getElementById('feed');

  const typing = document.getElementById('typingIndicator');
  if (typing) typing.remove();

  const div = document.createElement('div');
  div.className = `msg tipo-${msg.tipo || 'fala'}`;
  if (!animate) div.style.animation = 'none';

  if (msg.tipo === 'sistema') {
    div.innerHTML = `<div class="msg-text">${escapeHtml(msg.texto)}</div>`;
  } else {
    const cor = msg.tipo === 'usuario'
      ? 'var(--amber)'
      : (CAT_COLORS[msg.categoria] || '#64748b');
    const iniciais = getInitials(msg.nome || 'SN');
    const tipoBadge = getTipoBadge(msg.tipo);
    const walletDisplay = msg.consultorId ? `<span class="msg-wallet">&#926;${wallets[msg.consultorId] || '?'}</span>` : '';

    let tradeAlert = '';
    if (msg.tradeInfo) {
      const ti = msg.tradeInfo;
      if (ti.tipo === 'cobranca_pedido') {
        tradeAlert = `<div class="msg-trade-alert" style="border-color:rgba(234,179,8,0.3);background:rgba(234,179,8,0.08)">
          <span class="trade-icon">\u039E</span>
          <span>${escapeHtml(ti.nomeTo)} solicita \u039E${ti.valor} de ${escapeHtml(ti.nomeFrom)}</span>
        </div>`;
      } else {
        tradeAlert = `<div class="msg-trade-alert">
          <span class="trade-icon">\u039E</span>
          <span>${escapeHtml(ti.nomeFrom)} transferiu \u039E${ti.valor} para ${escapeHtml(ti.nomeTo)}</span>
        </div>`;
      }
    }

    div.innerHTML = `
      <div class="msg-avatar" style="background:${cor}">${iniciais}</div>
      <div class="msg-body">
        <div class="msg-header">
          <span class="msg-name">${escapeHtml(msg.nome || '')}</span>
          <span class="msg-cat">${escapeHtml(msg.categoriaLabel || '')}</span>
          ${walletDisplay}
          ${tipoBadge}
        </div>
        <div class="msg-text">${escapeHtml(msg.texto)}</div>
        ${tradeAlert}
        <div class="msg-time">${msg.hora || ''}</div>
      </div>
    `;
  }

  feed.appendChild(div);
}

function renderArticle(artigo, animate = true) {
  const body = document.getElementById('tabConstitution');
  const empty = document.getElementById('constEmpty');
  if (empty) empty.style.display = 'none';

  // Remover versao "formacao" do mesmo texto
  if (artigo.status === 'consenso') {
    const existentes = body.querySelectorAll('.const-article.formacao');
    existentes.forEach(el => {
      if (el.dataset.proponente === artigo.proponente) el.remove();
    });
  }

  const div = document.createElement('div');
  div.className = `const-article ${artigo.status === 'formacao' ? 'formacao' : 'emergente'}`;
  div.dataset.proponente = artigo.proponente;
  if (!animate) div.style.animation = 'none';

  const statusClass = artigo.status === 'consenso' ? 'consenso'
    : artigo.status === 'formacao' ? 'formacao'
    : 'debate';
  const statusLabel = artigo.status === 'consenso' ? 'CONSENSO APROVADO'
    : artigo.status === 'formacao' ? 'EM FORMACAO'
    : 'EM DEBATE';

  const apoiosHtml = (artigo.apoios || []).map(a => `<span class="supporter-chip">+ ${escapeHtml(typeof a === 'string' ? a : getNomeById(a))}</span>`).join('');
  const oposHtml = (artigo.oposicoes || []).map(o => `<span class="opposer-chip">- ${escapeHtml(typeof o === 'string' ? o : getNomeById(o))}</span>`).join('');
  const tipoHtml = artigo.tipo ? `<span class="const-article-type">${artigo.tipo}</span>` : '';

  div.innerHTML = `
    <div class="const-article-num">Artigo ${artigo.numero} ${tipoHtml}</div>
    <span class="const-article-status ${statusClass}">${statusLabel}</span>
    <div class="const-article-text">${escapeHtml(artigo.texto)}</div>
    <div class="const-article-meta">
      <span>Proposto por: ${escapeHtml(artigo.proponente)}</span>
      <span>Rodada ${artigo.rodada}</span>
    </div>
    <div class="const-article-supporters">${apoiosHtml}${oposHtml}</div>
  `;

  body.appendChild(div);
  body.scrollTop = body.scrollHeight;
}

function renderHelenaInsight(insight, animate = true) {
  const container = document.getElementById('helenaInsights');
  const empty = container.querySelector('.helena-empty');
  if (empty) empty.remove();

  const div = document.createElement('div');
  div.className = 'helena-insight';
  if (!animate) div.style.animation = 'none';

  // Gini color
  let giniColor = 'var(--green)';
  if (insight.gini > 0.3) giniColor = 'var(--yellow)';
  if (insight.gini > 0.5) giniColor = 'var(--red)';

  div.innerHTML = `
    <div class="helena-insight-header">
      <span class="helena-insight-icon">&#128161;</span>
      <span class="helena-insight-round">Rodada ${insight.rodada}</span>
    </div>
    <div class="helena-insight-text">${escapeHtml(insight.texto)}</div>
    <div class="helena-insight-tags">
      <span class="helena-tag">&#926;Vol: ${insight.volumeTotal}</span>
      <span class="helena-tag" style="color:${giniColor}">Gini: ${(insight.gini || 0).toFixed(3)}</span>
      <span class="helena-tag">${insight.numArtigos} artigos</span>
      <span class="helena-tag">${insight.totalTrades} trades</span>
    </div>
  `;

  container.insertBefore(div, container.firstChild);
}

function showTyping(consultor) {
  const feed = document.getElementById('feed');
  const old = document.getElementById('typingIndicator');
  if (old) old.remove();

  const cor = CAT_COLORS[consultor.categoria] || '#64748b';
  const iniciais = getInitials(consultor.nome_exibicao);
  const saldo = wallets[getConsultorId(consultor)] || 1000;

  const div = document.createElement('div');
  div.className = 'typing-indicator';
  div.id = 'typingIndicator';
  div.innerHTML = `
    <div class="msg-avatar" style="background:${cor}">${iniciais}</div>
    <div class="typing-dots"><span></span><span></span><span></span></div>
    <span class="typing-name">${escapeHtml(consultor.nome_exibicao)} (&#926;${saldo}) está digitando...</span>
  `;
  feed.appendChild(div);
  scrollToBottom();
}

function removeTyping() {
  const el = document.getElementById('typingIndicator');
  if (el) el.remove();
}

/* ============================================================
   ECONOMY TAB UPDATE
   ============================================================ */
function updateEconomyTab() {
  const econArticles = artigos.filter(a => a.tipo === 'Economia e Moeda' && a.status === 'consenso');
  const container = document.getElementById('econRules');
  if (!container) return;

  if (econArticles.length > 0) {
    container.innerHTML = econArticles.map(a => `
      <div style="padding:10px;border-radius:8px;background:var(--card);border:1px solid var(--brd)">
        <div style="font-size:10px;font-weight:700;color:var(--amber);margin-bottom:4px">ARTIGO ${a.numero} — ${a.tipo}</div>
        <div style="font-size:12px;color:var(--tx2);line-height:1.5">${escapeHtml(a.texto)}</div>
        <div style="font-size:9px;color:var(--txm);margin-top:4px">Proposto por ${escapeHtml(a.proponente)} — Rodada ${a.rodada}</div>
      </div>
    `).join('');
  }

  const countEl = document.getElementById('econArticleCount');
  if (countEl) countEl.textContent = econArticles.length;

  const temas = new Set();
  econArticles.forEach(a => {
    const t = a.texto.toLowerCase();
    if (/imposto|taxa/.test(t)) temas.add('Impostos');
    if (/moeda|coin/.test(t)) temas.add('Moeda');
    if (/comér|mercado/.test(t)) temas.add('Comércio');
    if (/propried|posse/.test(t)) temas.add('Propriedade');
    if (/contrat/.test(t)) temas.add('Contratos');
    if (/limit|acumul/.test(t)) temas.add('Limites');
    if (/puni|multa/.test(t)) temas.add('Punições');
  });
  const themeEl = document.getElementById('econThemeCount');
  if (themeEl) themeEl.textContent = temas.size;
}

function updateCurrencyBadge() {
  // Supply fixo — economia real e na cidade 3D
}

/* ============================================================
   TABS
   ============================================================ */
function switchTab(tabId, btn) {
  document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));

  const tabMap = {
    'constitution': 'tabConstitution',
    'economy': 'tabEconomy',
    'helena': 'tabHelena',
    'desafio': 'tabDesafio',
    'inteligencia': 'tabInteligencia'
  };
  const el = document.getElementById(tabMap[tabId]);
  if (el) el.classList.add('active');
  btn.classList.add('active');
  if (tabId === 'inteligencia') carregarRelatorio();
  if (tabId === 'desafio') carregarDesafio();
}

const VILA_BACKEND = 'https://vila-inteia.onrender.com/api/v1/vila';
let _relatorioTimer = null;

async function carregarRelatorio() {
  const el = document.getElementById('relatorioLive');
  if (!el) return;
  el.innerHTML = '<div style="text-align:center;padding:12px;color:var(--txm)">Carregando...</div>';
  try {
    const ctrl = new AbortController();
    setTimeout(() => ctrl.abort(), 12000);
    const r = await fetch(VILA_BACKEND + '/relatorio', { signal: ctrl.signal });
    if (!r.ok) throw new Error(r.status);
    const d = await r.json();
    let h = '';

    // Stats
    h += '<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px">';
    h += '<span style="background:var(--amber);color:#000;padding:2px 8px;border-radius:var(--r-full);font-size:10px;font-weight:600">Step ' + d.step + '</span>';
    h += '<span style="background:var(--green);color:#000;padding:2px 8px;border-radius:var(--r-full);font-size:10px;font-weight:600">' + (d.stats?.conversas || 0) + ' conv</span>';
    h += '<span style="background:var(--blue);color:#fff;padding:2px 8px;border-radius:var(--r-full);font-size:10px;font-weight:600">' + (d.stats?.sinteses || 0) + ' sínteses</span>';
    h += '<span style="background:var(--purple);color:#fff;padding:2px 8px;border-radius:var(--r-full);font-size:10px;font-weight:600">' + (d.stats?.posts || 0) + ' posts</span>';
    h += '</div>';

    // Conclusões
    if (d.conclusoes && d.conclusoes.length > 0) {
      h += '<div style="margin-bottom:12px"><div style="font-size:10px;color:var(--amber);text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;font-weight:600">Conclusões</div>';
      d.conclusoes.forEach(function(c) {
        h += '<div style="background:var(--bg2);border-left:3px solid var(--green);padding:8px 10px;margin-bottom:6px;border-radius:var(--r-sm);font-size:12px;line-height:1.5">' + escapeHtml(c) + '</div>';
      });
      h += '</div>';
    }

    // Divergências
    if (d.divergencias && d.divergencias.length > 0) {
      h += '<div style="margin-bottom:12px"><div style="font-size:10px;color:var(--red);text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;font-weight:600">Divergências</div>';
      d.divergencias.forEach(function(v) {
        h += '<div style="background:var(--bg2);border-left:3px solid var(--red);padding:8px 10px;margin-bottom:6px;border-radius:var(--r-sm);font-size:12px;line-height:1.5">' + escapeHtml(v) + '</div>';
      });
      h += '</div>';
    }

    // Descobertas
    if (d.descobertas && d.descobertas.length > 0) {
      h += '<div style="margin-bottom:12px"><div style="font-size:10px;color:var(--cyan);text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;font-weight:600">Descobertas</div>';
      d.descobertas.forEach(function(v) {
        h += '<div style="background:var(--bg2);border-left:3px solid var(--cyan);padding:8px 10px;margin-bottom:6px;border-radius:var(--r-sm);font-size:12px;line-height:1.5">' + escapeHtml(v) + '</div>';
      });
      h += '</div>';
    }

    // Recomendações
    if (d.recomendacoes && d.recomendacoes.length > 0) {
      h += '<div style="margin-bottom:12px"><div style="font-size:10px;color:var(--amber);text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;font-weight:600">Recomendações</div>';
      d.recomendacoes.forEach(function(r, i) {
        h += '<div style="background:var(--bg2);border-left:3px solid var(--amber);padding:8px 10px;margin-bottom:6px;border-radius:var(--r-sm);font-size:12px;line-height:1.5"><strong>' + (i+1) + '.</strong> ' + escapeHtml(r) + '</div>';
      });
      h += '</div>';
    }

    // Tendências
    if (d.tendencias && d.tendencias.length > 0) {
      h += '<div style="margin-bottom:12px"><div style="font-size:10px;color:var(--purple);text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;font-weight:600">Tendências</div>';
      d.tendencias.forEach(function(t) {
        h += '<div style="font-size:11px;color:var(--tx2);padding:4px 0;border-bottom:1px solid var(--brd)">→ ' + escapeHtml(t) + '</div>';
      });
      h += '</div>';
    }

    // Próximos passos
    if (d.proximos_passos && d.proximos_passos.length > 0) {
      h += '<div><div style="font-size:10px;color:var(--txm);text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;font-weight:600">Próximos Passos</div>';
      d.proximos_passos.forEach(function(p) {
        h += '<div style="font-size:11px;color:var(--txm);padding:3px 0">→ ' + escapeHtml(p) + '</div>';
      });
      h += '</div>';
    }

    if (!h) h = '<div style="text-align:center;padding:20px;color:var(--txm)">Simulação iniciando — aguardando dados (step 10+)</div>';

    h += '<div style="margin-top:12px;font-size:9px;color:var(--txm);text-align:right">Atualizado: ' + (d.gerado_em || 'agora') + '</div>';
    el.innerHTML = h;
  } catch(e) {
    if (e.name !== 'AbortError') el.innerHTML = '<div style="text-align:center;padding:20px;color:var(--txm)">Backend offline — Vila rodará em modo local</div>';
  }
}

// Auto-refresh a cada 60s quando tab ativa
function startRelatorioPolling() {
  if (_relatorioTimer) clearInterval(_relatorioTimer);
  _relatorioTimer = setInterval(function() {
    var tab = document.getElementById('tabInteligencia');
    if (tab && tab.classList.contains('active')) carregarRelatorio();
  }, 60000);
}

/* ============================================================
   UTILIDADES
   ============================================================ */
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function getInitials(name) {
  return name.split(' ').filter(Boolean).map(w => w[0]).slice(0, 2).join('').toUpperCase();
}

function getTipoBadge(tipo) {
  const labels = {
    proposta: 'PROPOSTA', apoio: 'APOIO', oposicao: 'OPOSIÇÃO',
    provocacao: 'PROVOCAÇÃO', emenda: 'EMENDA', conciliacao: 'CONCILIAÇÃO',
    negociacao: 'NEGOCIAÇÃO'
  };
  if (!labels[tipo]) return '';
  return `<span class="msg-tipo-badge ${tipo}">${labels[tipo]}</span>`;
}

function getHora() {
  return new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function scrollToBottom() {
  const feed = document.getElementById('feed');
  requestAnimationFrame(() => { feed.scrollTop = feed.scrollHeight; });
}

function updateStats() {
  document.getElementById('statRound').textContent = roundNum;
  document.getElementById('statMsgs').textContent = mensagens.length;
  document.getElementById('statSpeakers').textContent = speakersSet.size;
  document.getElementById('statArticles').textContent = artigos.filter(a => a.status === 'consenso').length;
  document.getElementById('statTrades').textContent = transacoes.length;

  // Atualizar indicador de fase processual
  const faseEl = document.getElementById('statFase');
  if (faseEl) {
    const faseLabels = {
      'pauta': 'PAUTA',
      'apresentacao': 'APRESENTAÇÃO',
      'discussao': 'DISCUSSÃO',
      'votacao': 'VOTAÇÃO',
      'resultado': 'RESULTADO'
    };
    faseEl.textContent = faseLabels[faseAtual] || faseAtual;
    faseEl.className = 'stat-fase fase-' + faseAtual;
  }
  const votosEl = document.getElementById('statVotos');
  if (votosEl && faseAtual === FASE.VOTACAO) {
    votosEl.textContent = `${votosRodada.sim.size}S/${votosRodada.nao.size}N/${votosRodada.abstencao.size}A`;
    votosEl.style.display = 'inline';
  } else if (votosEl) {
    votosEl.style.display = 'none';
  }
}

/* ============================================================
   LOOP PRINCIPAL DA SIMULACAO
   ============================================================ */
async function rodada() {
  if (!running || isGenerating) return;
  isGenerating = true;

  try {
    // ==========================================
    // LÓGICA DE TRANSIÇÃO DE FASES PROCESSUAIS
    // ==========================================

    // FASE APRESENTAÇÃO: após propostas e falas suficientes, ir para DISCUSSÃO da mais apoiada
    if (faseAtual === FASE.APRESENTACAO) {
      const proposstasFase = propostas.filter(p => p.status === 'debate' || p.status === 'formacao');
      const falasDesdeUltimaFase = mensagens.filter(m => m.tipo !== 'sistema' && m.tipo !== 'usuario' && (m.rodada || 0) > rodadaUltimaFase).length;

      // Se já temos propostas e pelo menos 3 falas desde a última mudança de fase
      if (proposstasFase.length >= 1 && falasDesdeUltimaFase >= 3) {
        // Ordenar por apoio
        const melhorProposta = proposstasFase.sort((a, b) => (b.apoios.size - b.oposicoes.size) - (a.apoios.size - a.oposicoes.size))[0];
        propostaEmPauta = melhorProposta;
        faseAtual = FASE.DISCUSSAO;
        rodadaUltimaFase = roundNum;
        numOradoresDiscussao = 0;
        votosRodada = { sim: new Set(), nao: new Set(), abstencao: new Set() };

        const msgTransicao = {
          tipo: 'sistema', nome: 'PRESIDENTE',
          texto: `PRESIDENTE RUI BARBOSA: Encerrada a fase de apresentação. Passa à DISCUSSÃO a proposta de ${melhorProposta.proponente}: "${melhorProposta.texto.substring(0, 150)}..." — Concedo a palavra aos oradores. Declarem-se a favor, contra, ou proponham emendas.`,
          hora: getHora(), rodada: roundNum, timestamp: Date.now()
        };
        mensagens.push(msgTransicao);
        renderMessage(msgTransicao);
        salvarMensagem(msgTransicao);
      }
    }

    // FASE DISCUSSÃO: após MAX oradores ou pedido de encerramento, ir para VOTAÇÃO
    if (faseAtual === FASE.DISCUSSAO) {
      if (numOradoresDiscussao >= MAX_ORADORES_DISCUSSAO ||
          (numOradoresDiscussao >= MIN_ORADORES_DISCUSSAO && mensagens.length > 0 &&
           /\b(encerr|vota[çc][aã]o|votar agora|ir [aà] voto)\b/i.test(mensagens[mensagens.length - 1]?.texto || ''))) {
        faseAtual = FASE.VOTACAO;
        rodadaUltimaFase = roundNum;
        votosRodada = { sim: new Set(), nao: new Set(), abstencao: new Set() };

        const msgVotacao = {
          tipo: 'sistema', nome: 'PRESIDENTE',
          texto: `PRESIDENTE RUI BARBOSA: Encerrada a discussão com ${numOradoresDiscussao} oradores. Passa-se à VOTAÇÃO NOMINAL. Proposta de ${propostaEmPauta.proponente}: "${propostaEmPauta.texto.substring(0, 120)}..." — Os constituintes devem votar: SIM, NÃO ou ABSTENÇÃO.`,
          hora: getHora(), rodada: roundNum, timestamp: Date.now()
        };
        mensagens.push(msgVotacao);
        renderMessage(msgVotacao);
        salvarMensagem(msgVotacao);
      }
    }

    // FASE VOTAÇÃO: após votos suficientes, proclamar resultado
    if (faseAtual === FASE.VOTACAO) {
      let totalVotos = votosRodada.sim.size + votosRodada.nao.size + votosRodada.abstencao.size;

      // Auto-completar votação se está demorando muito (mais de 6 rodadas de votação sem quórum)
      const rodadasEmVotacao = roundNum - rodadaUltimaFase;
      if (totalVotos < 5 && rodadasEmVotacao >= 6) {
        // Forçar votos dos NPCs restantes baseado na sua orientação
        const jaVotaram = new Set([...votosRodada.sim, ...votosRodada.nao, ...votosRodada.abstencao]);
        const faltam = consultores.filter(c => !jaVotaram.has(c.nome_exibicao)).slice(0, 5 - totalVotos);
        faltam.forEach(c => {
          const orient = (c.orientacao_politica || '').toLowerCase();
          const textoP = (propostaEmPauta?.texto || '').toLowerCase();
          // Voto baseado na coerência ideológica
          let votoAuto = Math.random() < 0.6 ? 'sim' : 'nao';
          if (/estado|regula|impost|taxa|redistr/i.test(textoP)) {
            if (/esquerda|social|progressi/i.test(orient)) votoAuto = 'sim';
            else if (/direita|liberal|conserv/i.test(orient)) votoAuto = 'nao';
          }
          if (/liber|livre|propried|privad/i.test(textoP)) {
            if (/direita|liberal|conserv/i.test(orient)) votoAuto = 'sim';
            else if (/esquerda|social|progressi/i.test(orient)) votoAuto = 'nao';
          }
          votosRodada[votoAuto === 'sim' ? 'sim' : 'nao'].add(c.nome_exibicao);
        });
        totalVotos = votosRodada.sim.size + votosRodada.nao.size + votosRodada.abstencao.size;
        const msgAutoVoto = {
          tipo: 'sistema', nome: 'PRESIDENTE',
          texto: `PRESIDENTE RUI BARBOSA: Verificando quórum... ${totalVotos} votos registrados. Resultado será proclamado.`,
          hora: getHora(), rodada: roundNum, timestamp: Date.now()
        };
        mensagens.push(msgAutoVoto);
        renderMessage(msgAutoVoto);
      }

      if (totalVotos >= 5) { // Quórum mínimo de 5 votos (was 8)
        const votantes = votosRodada.sim.size + votosRodada.nao.size;
        const isQualificado = /\b(govern|presid|puni[çc]|expuls|poder|autorid)\b/i.test(propostaEmPauta.texto);
        const quorum = isQualificado ? QUORUM_QUALIFICADO : QUORUM_SIMPLES;
        const aprovado = votantes > 0 && (votosRodada.sim.size / votantes) > quorum;

        if (aprovado) {
          artigoCounter++;
          let tipoArtigo = 'Princípios Fundamentais';
          const tl = propostaEmPauta.texto.toLowerCase();
          if (/\b(moeda|coin|Ξ|econ|imposto|taxa|dinheiro|capital|mercado|comerci)\b/.test(tl)) tipoArtigo = 'Economia e Moeda';
          else if (/\b(puni|expuls|ban|sanc|multa|infra)\b/.test(tl)) tipoArtigo = 'Punições e Expulsão';
          else if (/\b(direito|dever|liber|priv|garanti|proteg)\b/.test(tl)) tipoArtigo = 'Direitos e Deveres';
          else if (/\b(govern|presid|conselho|voto|eleic|cargo|poder|autorid)\b/.test(tl)) tipoArtigo = 'Organização e Governança';
          else if (/\b(emend|revis|alter|reform|modific)\b/.test(tl)) tipoArtigo = 'Emendas e Revisão';
          else if (/\b(process|tramit|quorum|procedim|deliber)\b/.test(tl)) tipoArtigo = 'Processo Legislativo';

          const artigo = {
            numero: artigoCounter,
            texto: propostaEmPauta.texto,
            proponente: propostaEmPauta.proponente,
            apoios: Array.from(votosRodada.sim),
            oposicoes: Array.from(votosRodada.nao),
            status: 'consenso',
            tipo: tipoArtigo,
            rodada: roundNum
          };
          artigos.push(artigo);
          renderArticle(artigo, true);
          salvarArtigos();
          propostaEmPauta.status = 'aprovado';

          const msgResultado = {
            tipo: 'sistema', nome: 'PRESIDENTE',
            texto: `PRESIDENTE RUI BARBOSA: APROVADO! Artigo ${artigoCounter} aprovado por ${votosRodada.sim.size} votos a favor, ${votosRodada.nao.size} contra e ${votosRodada.abstencao.size} abstenções${isQualificado ? ' (quórum qualificado de 2/3)' : ' (maioria simples)'}. Tipo: ${tipoArtigo}. Proposto por ${propostaEmPauta.proponente}.`,
            hora: getHora(), rodada: roundNum, timestamp: Date.now()
          };
          mensagens.push(msgResultado);
          renderMessage(msgResultado);
          salvarMensagem(msgResultado);

        } else {
          propostaEmPauta.status = 'rejeitado';
          const msgRejeicao = {
            tipo: 'sistema', nome: 'PRESIDENTE',
            texto: `PRESIDENTE RUI BARBOSA: REJEITADO. Proposta de ${propostaEmPauta.proponente} rejeitada por ${votosRodada.nao.size} votos contra, ${votosRodada.sim.size} a favor e ${votosRodada.abstencao.size} abstenções. Matéria arquivada.`,
            hora: getHora(), rodada: roundNum, timestamp: Date.now()
          };
          mensagens.push(msgRejeicao);
          renderMessage(msgRejeicao);
          salvarMensagem(msgRejeicao);
        }

        // Avançar para próximo tema
        salvarPropostas();
        pautaIndex++;
        propostaEmPauta = null;
        faseAtual = FASE.APRESENTACAO;
        rodadaUltimaFase = roundNum;
        numOradoresDiscussao = 0;
        votosRodada = { sim: new Set(), nao: new Set(), abstencao: new Set() };

        if (pautaIndex < PAUTA_OBRIGATORIA.length) {
          const proximoTema = PAUTA_OBRIGATORIA[pautaIndex];
          const msgProximoTema = {
            tipo: 'sistema', nome: 'PRESIDENTE',
            texto: `PRESIDENTE RUI BARBOSA: Passamos ao próximo item da Ordem do Dia: "${proximoTema.tema}" — ${proximoTema.desc}. Constituintes que desejem apresentar propostas sobre este tema, peçam a palavra.`,
            hora: getHora(), rodada: roundNum, timestamp: Date.now()
          };
          mensagens.push(msgProximoTema);
          renderMessage(msgProximoTema);
          salvarMensagem(msgProximoTema);
        } else {
          const msgFim = {
            tipo: 'sistema', nome: 'PRESIDENTE',
            texto: `PRESIDENTE RUI BARBOSA: Esgotada a Ordem do Dia obrigatória. ${artigos.filter(a => a.status === 'consenso').length} artigos aprovados. Constituintes podem propor temas adicionais para deliberação.`,
            hora: getHora(), rodada: roundNum, timestamp: Date.now()
          };
          mensagens.push(msgFim);
          renderMessage(msgFim);
          salvarMensagem(msgFim);
        }

        updateEconomyTab();
        updateStats();
        scrollToBottom();

        // Helena analisa após cada votação
        if (roundNum > 5) helenaAnalise();

        isGenerating = false;
        return; // Não gerar fala nesta rodada (rodada processual)
      }
    }

    // ==========================================
    // GERAR FALA DO PRÓXIMO ORADOR
    // ==========================================
    const consultor = selecionarOrador();
    if (!consultor) { isGenerating = false; return; }

    const consultorId = getConsultorId(consultor);

    showTyping(consultor);

    const texto = await gerarFala(consultor);

    removeTyping();

    if (!texto) { isGenerating = false; return; }

    // Classificar
    const tipo = classificarMensagem(texto);

    const msg = {
      consultorId: consultorId,
      nome: consultor.nome_exibicao,
      categoria: consultor.categoria,
      categoriaLabel: CAT_LABELS[consultor.categoria] || consultor.categoria || '',
      texto: texto,
      tipo: tipo,
      hora: getHora(),
      rodada: roundNum + 1,
      timestamp: Date.now(),
      tradeInfo: null
    };

    mensagens.push(msg);
    if (mensagens.length > 1000) mensagens.splice(0, 200);
    roundNum++;
    speakersSet.add(consultorId);
    lastSpeakerId = consultorId;
    lastSpeakers.push(consultorId);
    if (lastSpeakers.length > 50) lastSpeakers.splice(0, 20);

    renderMessage(msg);
    scrollToBottom();
    updateStats();
    salvarMensagem(msg);

    // Rastrear proposta imediatamente quando classificada
    if (tipo === 'proposta') {
      const jaExiste = propostas.find(p => p.proponente === msg.nome && p.texto === msg.texto);
      if (!jaExiste) {
        propostas.push({
          msgIndex: mensagens.length - 1,
          texto: msg.texto,
          proponente: msg.nome,
          apoios: new Set(),
          oposicoes: new Set(),
          status: 'debate'
        });
        salvarPropostas();
      }
    }
    // Rastrear apoio/oposição imediatamente
    if (tipo === 'apoio' || tipo === 'emenda') {
      const propostasDebate = propostas.filter(p => p.status === 'debate' || p.status === 'formacao');
      if (propostasDebate.length > 0) {
        propostasDebate[propostasDebate.length - 1].apoios.add(consultorId);
        salvarPropostas();
      }
    }
    if (tipo === 'oposicao') {
      const propostasDebate = propostas.filter(p => p.status === 'debate' || p.status === 'formacao');
      if (propostasDebate.length > 0) {
        propostasDebate[propostasDebate.length - 1].oposicoes.add(consultorId);
        salvarPropostas();
      }
    }

    // Processar voto se estamos na fase de votação (detecção ampla)
    if (faseAtual === FASE.VOTACAO) {
      const textoLower = texto.toLowerCase();
      // Detecção de votos - do mais explícito ao mais implícito
      if (/\bvoto\s+sim\b/i.test(textoLower) || /\bvoto\s+favor[áa]vel\b/i.test(textoLower)) {
        votosRodada.sim.add(consultor.nome_exibicao);
      } else if (/\bvoto\s+n[aã]o\b/i.test(textoLower) || /\bvoto\s+contr[áa]rio\b/i.test(textoLower)) {
        votosRodada.nao.add(consultor.nome_exibicao);
      } else if (/\babsten[çc][aã]o\b/i.test(textoLower) || /\bme\s+abstenho\b/i.test(textoLower)) {
        votosRodada.abstencao.add(consultor.nome_exibicao);
      } else if (/\b(a favor|favor[áa]vel|concordo|apoio|aprovado|aprovo|declaro.*favor|sim[,.])\b/i.test(textoLower)) {
        votosRodada.sim.add(consultor.nome_exibicao);
      } else if (/\b(contra|contr[áa]rio|discordo|rejeito|reprovado|reprovo|declaro.*contr[áa]|n[aã]o[,.])\b/i.test(textoLower)) {
        votosRodada.nao.add(consultor.nome_exibicao);
      } else {
        // Fallback: qualquer fala durante VOTAÇÃO — inferir voto por sentimento
        const positive = (textoLower.match(/\b(bom|boa|positiv|benef|import|necess|essencial|correto|justo|adequado|concordo)\b/g) || []).length;
        const negative = (textoLower.match(/\b(mau|ruim|negativ|preju|desnec|errado|injusto|inadequado|discordo|perig)\b/g) || []).length;
        if (positive > negative) {
          votosRodada.sim.add(consultor.nome_exibicao);
        } else if (negative > positive) {
          votosRodada.nao.add(consultor.nome_exibicao);
        } else {
          votosRodada.abstencao.add(consultor.nome_exibicao);
        }
      }
    }

    // Contar orador na fase de discussão
    if (faseAtual === FASE.DISCUSSAO) {
      numOradoresDiscussao++;
    }

    // Atualizar aba de regras econômicas
    updateEconomyTab();

    // Analisar consenso a cada rodada na fase de apresentação
    if (faseAtual === FASE.APRESENTACAO) {
      analisarConsenso();
    }

    // Helena analisa a cada 15 rodadas
    if (roundNum % 15 === 0 && roundNum > 0) {
      helenaAnalise();
    }

  } catch (e) {
    console.error('[RODADA] Erro:', e);
    removeTyping();
  }

  isGenerating = false;
}

/* ============================================================
   MENSAGEM INICIAL
   ============================================================ */
function enviarMensagemInicial() {
  // 1. Abertura da Assembleia
  const msgAbertura = {
    tipo: 'sistema',
    nome: 'SISTEMA',
    texto: 'ASSEMBLEIA CONSTITUINTE DA VILA INTEIA — SESSÃO INAUGURAL. 142 consultores lendários reunidos para criar a Constituição da Vila INTEIA. A comunidade possui Ξ142.000 INTEIA Coins em circulação. O Regimento Interno já foi aprovado previamente pela Mesa Diretora.',
    hora: getHora(),
    rodada: 0,
    timestamp: Date.now()
  };
  mensagens.push(msgAbertura);
  renderMessage(msgAbertura);
  salvarMensagem(msgAbertura);

  // 2. Apresentar Regimento Interno como artigos já aprovados
  REGIMENTO_INTERNO.forEach(ri => {
    const artigo = {
      numero: ri.numero,
      texto: ri.texto,
      proponente: 'Mesa Diretora',
      apoios: ['Rui Barbosa', 'Clóvis Beviláqua', 'Abraham Lincoln'],
      oposicoes: [],
      status: 'consenso',
      tipo: ri.tipo,
      rodada: 0
    };
    artigos.push(artigo);
    renderArticle(artigo, false);
  });
  salvarArtigos();

  // 3. Presidente abre a sessão
  const msgPresidente = {
    tipo: 'sistema',
    nome: 'PRESIDENTE',
    texto: 'PRESIDENTE RUI BARBOSA: Declaro abertos os trabalhos da Assembleia Constituinte. O Regimento Interno está publicado no painel à direita. Passamos à Ordem do Dia. PRIMEIRO TEMA: "' + PAUTA_OBRIGATORIA[0].tema + '" — ' + PAUTA_OBRIGATORIA[0].desc + '. A Mesa convida os constituintes a apresentarem propostas sobre este tema. Quem deseja a palavra?',
    hora: getHora(),
    rodada: 0,
    timestamp: Date.now()
  };
  mensagens.push(msgPresidente);
  renderMessage(msgPresidente);
  salvarMensagem(msgPresidente);

  // 4. Iniciar na fase de PAUTA do primeiro tema
  faseAtual = FASE.APRESENTACAO;
  pautaIndex = 0;
}

/* ============================================================
   CONTROLES
   ============================================================ */
function togglePlay() {
  const btn = document.getElementById('btnPlay');

  if (running) {
    running = false;
    if (timerHandle) clearInterval(timerHandle);
    timerHandle = null;
    btn.innerHTML = '&#9654; Play';
    btn.classList.remove('paused');
    btn.classList.add('play-btn');
  } else {
    running = true;
    btn.innerHTML = '&#9646;&#9646; Pause';
    btn.classList.add('paused');

    if (mensagens.length === 0) {
      enviarMensagemInicial();
    }

    startLoop();
  }
}

function startLoop() {
  if (timerHandle) clearInterval(timerHandle);
  const interval = getInterval();
  const delay = mensagens.length <= 1 ? 1500 : 200;
  setTimeout(() => {
    if (running) rodada();
  }, delay);
  timerHandle = setInterval(() => {
    if (running && !isGenerating) rodada();
  }, interval);
}

function getInterval() {
  const base = 6000;
  return Math.max(base / speed, 1500);
}

function setSpeed(s, btn) {
  speed = s;
  document.querySelectorAll('.speed-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  if (running) startLoop();
}

/* ============================================================
   INPUT DO USUARIO
   ============================================================ */
function sendUserMessage() {
  const input = document.getElementById('userInput');
  const texto = input.value.trim();
  if (!texto) return;

  const msg = {
    tipo: 'usuario',
    nome: 'Igor Morais',
    consultorId: 'USER_IGOR',
    categoria: 'omega',
    categoriaLabel: 'Criador INTEIA',
    texto: texto,
    hora: getHora(),
    rodada: roundNum,
    timestamp: Date.now(),
    tradeInfo: null
  };

  mensagens.push(msg);
  renderMessage(msg);
  scrollToBottom();
  salvarMensagem(msg);
  updateStats();
  updateEconomyTab();

  input.value = '';
}

/* ============================================================
   EXPORTAR TRANSCRIPT
   ============================================================ */
function exportTranscript() {
  let text = '=== JOGO DA ASSEMBLEIA CONSTITUINTE - VILA INTEIA ===\n';
  text += `Sessão: ${sessionId}\n`;
  text += `Exportado: ${new Date().toLocaleString('pt-BR')}\n`;
  text += `Total de mensagens: ${mensagens.length}\n`;
  text += `Consultores que falaram: ${speakersSet.size}\n`;
  text += `Artigos aprovados: ${artigos.filter(a => a.status === 'consenso').length}\n`;
  text += `Total transacoes: ${transacoes.length}\n`;
  text += `Volume economico: ${transacoes.reduce((s, t) => s + t.valor, 0)}\n`;
  text += `Gini: ${calcGini(Object.values(wallets)).toFixed(4)}\n`;
  text += '\n' + '='.repeat(60) + '\n\n';

  // Constituicao
  text += '--- CONSTITUICAO ---\n\n';
  artigos.filter(a => a.status === 'consenso').forEach(a => {
    text += `ARTIGO ${a.numero} [${a.tipo || ''}]\n`;
    text += `${a.texto}\n`;
    text += `Proposto por: ${a.proponente} | Rodada: ${a.rodada}\n`;
    text += `Apoios: ${(a.apoios || []).join(', ')}\n`;
    text += `Oposicoes: ${(a.oposicoes || []).join(', ')}\n\n`;
  });

  text += '\n--- ECONOMIA ---\n\n';
  text += 'Top 20 Wallets:\n';
  Object.entries(wallets).sort((a, b) => b[1] - a[1]).slice(0, 20).forEach(([id, v], i) => {
    text += `${i + 1}. ${getNomeById(id)}: Ξ${v}\n`;
  });
  text += '\nTransacoes:\n';
  transacoes.forEach(t => {
    text += `R${t.rodada} | ${getNomeById(t.de)} -> Ξ${t.valor} -> ${getNomeById(t.para)} | ${t.motivo}\n`;
  });

  text += '\n--- DEBATE ---\n\n';
  mensagens.forEach(m => {
    if (m.tipo === 'sistema') {
      text += `[SISTEMA] ${m.texto}\n\n`;
    } else {
      text += `[${m.hora}] [R${m.rodada}] ${m.nome} (${m.categoriaLabel || ''}) [${m.tipo}]:\n${m.texto}\n\n`;
    }
  });

  // Helena insights
  if (helenaInsights.length > 0) {
    text += '\n--- HELENA INSIGHTS ---\n\n';
    helenaInsights.forEach(h => {
      text += `[Rodada ${h.rodada}] Gini: ${(h.gini || 0).toFixed(3)} | Vol: Ξ${h.volumeTotal}\n`;
      text += `${h.texto}\n\n`;
    });
  }

  // Download
  const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `jogo-assembleia-${sessionId.slice(0, 8)}-${new Date().toISOString().slice(0, 10)}.txt`;
  a.click();
  URL.revokeObjectURL(url);
}

/* ============================================================
   RESET SESSION
   ============================================================ */
function resetSession() {
  if (!confirm('Iniciar nova sessão? O estado atual será salvo no histórico.')) return;

  running = false;
  if (timerHandle) clearInterval(timerHandle);
  timerHandle = null;

  const btn = document.getElementById('btnPlay');
  btn.innerHTML = '&#9654; Play';
  btn.classList.remove('paused');
  btn.classList.add('play-btn');

  // Nova sessao
  sessionId = crypto.randomUUID();
  localStorage.setItem('vila_jogo_session', sessionId);
  document.getElementById('sessionBadge').textContent = 'Sessão: ' + sessionId.slice(0, 8);

  // Limpar estado
  mensagens = [];
  artigos = [];
  propostas = [];
  transacoes = [];
  helenaInsights = [];
  roundNum = 0;
  speakersSet = new Set();
  lastSpeakers = [];
  lastSpeakerId = null;
  artigoCounter = 0;
  isGenerating = false;

  // Resetar processo legislativo
  faseAtual = FASE.PAUTA;
  propostaEmPauta = null;
  ordemDosDias = [];
  votosRodada = { sim: new Set(), nao: new Set(), abstencao: new Set() };
  numOradoresDiscussao = 0;
  pautaIndex = 0;

  // Re-init wallets
  initWallets(consultores);

  // Limpar UI
  document.getElementById('feed').innerHTML = '';
  document.getElementById('tabConstitution').innerHTML = `
    <div class="const-empty" id="constEmpty">
      <div class="const-empty-icon">&#128220;</div>
      <p>Nenhum artigo aprovado ainda. A Assembleia precisa debater e chegar a consensos para que artigos apareçam aqui.</p>
    </div>`;
  document.getElementById('helenaInsights').innerHTML = '<p class="helena-empty">Helena está observando a assembleia. Insights aparecerão aqui após 10 rodadas.</p>';

  updateStats();
  updateEconomyTab();
  updateCurrencyBadge();
}

/* ============================================================
   INIT
   ============================================================ */
/* ============================================================
   DESAFIO COLETIVO
   ============================================================ */
const VILA_API = _IS_RENDER ? location.origin + '/api/v1/vila' : 'https://vila-inteia.onrender.com/api/v1/vila';

let _desafioCache = null;

async function carregarDesafio() {
  try {
    const resp = await fetch(VILA_API + '/desafio');
    const data = await resp.json();
    _desafioCache = data;
    renderDesafio(data);
  } catch(e) {
    console.warn('Desafio indisponível:', e);
  }
}

function renderDesafio(data) {
  const header = document.getElementById('desafioHeader');
  const prog = document.getElementById('desafioProgresso');
  const fases = document.getElementById('desafioFases');
  const contribs = document.getElementById('desafioContribsList');
  const metricas = document.getElementById('desafioMetricas');

  if (!data || data.status === 'inativo') {
    header.innerHTML = `
      <div style="text-align:center;padding:20px;color:var(--txm);font-size:12px;line-height:1.6">
        Nenhum desafio ativo.<br>
        <button onclick="listarDesafios()" style="margin-top:8px;background:linear-gradient(135deg,#22c55e,#16a34a);border:none;color:#fff;padding:8px 16px;border-radius:var(--r-sm);cursor:pointer;font-size:12px;font-weight:600">Escolher Desafio</button>
      </div>`;
    prog.style.display = 'none';
    fases.innerHTML = '';
    contribs.innerHTML = '';
    metricas.style.display = 'none';
    return;
  }

  // Header ativo
  const pct = Math.round((data.progresso_total || 0) * 100);
  header.innerHTML = `
    <div style="display:flex;align-items:center;gap:10px">
      <span style="font-size:28px">${escapeHtml(data.icone || '🎯')}</span>
      <div>
        <div style="font-weight:700;font-size:14px;color:var(--tx1)">${escapeHtml(data.nome)}</div>
        <div style="font-size:11px;color:var(--txm)">${escapeHtml(data.descricao || '').slice(0,120)}...</div>
      </div>
    </div>`;

  // Progresso
  prog.style.display = 'block';
  document.getElementById('desafioProgressoPct').textContent = pct + '%';
  document.getElementById('desafioProgressoBar').style.width = pct + '%';

  // Fases
  if (data.fases && data.fases.length) {
    fases.innerHTML = data.fases.map((f, i) => {
      const isCurrent = i === data.fase_atual_idx;
      const isDone = f.status === 'concluida';
      const fpct = Math.round((f.progresso || 0) * 100);
      const bg = isDone ? 'rgba(34,197,94,0.15)' : isCurrent ? 'rgba(201,149,42,0.15)' : 'var(--bg3)';
      const border = isDone ? '1px solid rgba(34,197,94,0.3)' : isCurrent ? '1px solid rgba(201,149,42,0.3)' : '1px solid var(--brd)';
      const icon = isDone ? '✅' : isCurrent ? '▶' : '○';
      return `<div style="background:${bg};border:${border};padding:8px 10px;border-radius:var(--r-sm);display:flex;align-items:center;gap:8px">
        <span style="font-size:12px">${icon}</span>
        <div style="flex:1;min-width:0">
          <div style="font-size:12px;font-weight:600;color:var(--tx1)">${escapeHtml(f.nome)}</div>
          <div style="font-size:10px;color:var(--txm)">${escapeHtml(f.descricao)}</div>
        </div>
        <span style="font-size:11px;font-weight:700;color:${isDone?'#22c55e':isCurrent?'var(--amber)':'var(--txm)'}">${fpct}%</span>
      </div>`;
    }).join('');
  }

  // Contribuições recentes
  const recentes = data.contribuicoes_recentes || [];
  if (recentes.length) {
    contribs.innerHTML = recentes.slice(-8).reverse().map(c => `
      <div style="background:var(--bg3);padding:6px 8px;border-radius:var(--r-sm);font-size:11px;border-left:3px solid ${c.tipo==='proposta'?'#22c55e':c.tipo==='emenda'?'#3b82f6':'var(--amber)'}">
        <strong style="color:var(--tx1)">${escapeHtml(c.agente_nome)}</strong>
        <span style="color:var(--txm);margin-left:4px">${escapeHtml(c.conteudo).slice(0,120)}</span>
      </div>
    `).join('');
  } else {
    contribs.innerHTML = '<div style="text-align:center;padding:8px;color:var(--txm);font-size:11px">Aguardando contribuições...</div>';
  }

  // Métricas
  const m = data.metricas || {};
  metricas.style.display = 'grid';
  document.getElementById('desafioTotalContribs').textContent = m.total_contribuicoes || 0;
  document.getElementById('desafioParticipantes').textContent = m.agentes_participantes || 0;
  document.getElementById('desafioVotos').textContent = m.total_votos || 0;
  document.getElementById('desafioDebates').textContent = m.total_debates || 0;
}

function listarDesafios() {
  const catalogo = document.getElementById('desafioCatalogo');
  catalogo.style.display = 'block';
  catalogo.innerHTML = `
    <h4 style="font-size:13px;font-weight:700;color:var(--tx1);margin-bottom:10px">Definir Tema do Desafio</h4>
    <textarea id="desafioTemaInput" placeholder="Digite o tema... Ex: Analisar cenário eleitoral DF 2026, Criar plano de negócios para fintech, Investigar impacto da IA no direito brasileiro..." style="width:100%;height:80px;background:var(--bg3);border:1px solid var(--brd);color:var(--tx1);padding:8px;border-radius:var(--r-sm);font-size:12px;resize:vertical;font-family:inherit"></textarea>
    <div style="margin-top:8px">
      <label style="font-size:11px;color:var(--txm);cursor:pointer;display:flex;align-items:center;gap:6px">
        <span>📎 Anexar documento (txt, md, json):</span>
        <input type="file" id="desafioDocInput" aria-label="Upload documento desafio" accept=".txt,.md,.json,.csv,.html" style="font-size:11px" onchange="carregarDocDesafio(this)">
      </label>
      <div id="desafioDocPreview" style="display:none;margin-top:6px;padding:6px;background:var(--bg3);border-radius:var(--r-sm);font-size:10px;color:var(--txm);max-height:60px;overflow:hidden"></div>
    </div>
    <button onclick="iniciarDesafioLivre()" aria-label="Iniciar desafio livre" style="margin-top:10px;width:100%;background:linear-gradient(135deg,#22c55e,#16a34a);border:none;color:#fff;padding:10px;border-radius:var(--r-sm);cursor:pointer;font-size:13px;font-weight:700">Iniciar Desafio</button>
  `;
}

let _docAnexado = '';

function carregarDocDesafio(input) {
  const file = input.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = function(e) {
    _docAnexado = e.target.result;
    const preview = document.getElementById('desafioDocPreview');
    preview.style.display = 'block';
    preview.textContent = file.name + ' (' + (file.size/1024).toFixed(1) + 'KB) — ' + _docAnexado.slice(0, 200) + '...';
  };
  reader.readAsText(file);
}

async function iniciarDesafioLivre() {
  const tema = document.getElementById('desafioTemaInput')?.value?.trim();
  if (!tema) { alert('Digite o tema do desafio'); return; }

  const catalogo = document.getElementById('desafioCatalogo');
  catalogo.innerHTML = '<div style="text-align:center;padding:12px;color:var(--amber)">Criando desafio...</div>';

  try {
    const resp = await fetch(VILA_API + '/desafio/iniciar', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        tema: tema,
        documento: _docAnexado || '',
      }),
    });
    const data = await resp.json();
    catalogo.style.display = 'none';
    _docAnexado = '';

    if (data.desafio) {
      renderDesafio(data.desafio);
      addSystemMessage('🎯 DESAFIO INICIADO: ' + data.desafio.nome);
    } else if (data.erro) {
      catalogo.style.display = 'block';
      catalogo.innerHTML = '<div style="color:#ef4444;padding:12px;font-size:12px">' + escapeHtml(data.erro) + '</div>';
    }
  } catch(e) {
    catalogo.style.display = 'block';
    catalogo.innerHTML = '<div style="color:#ef4444;padding:12px;font-size:12px">Erro ao criar desafio. Backend indisponível.</div>';
  }
}

function addSystemMessage(texto) {
  const el = document.getElementById('feed');
  if (!el) return;
  const div = document.createElement('div');
  div.className = 'msg tipo-sistema';
  div.innerHTML = `<div class="msg-body"><p style="font-style:italic;color:var(--amber);font-size:12px">${escapeHtml(texto)}</p></div>`;
  el.appendChild(div);
  el.scrollTop = el.scrollHeight;
}

// Polling do desafio a cada 30s quando aba ativa
let _desafioPolling = null;
function startDesafioPolling() {
  if (_desafioPolling) return;
  _desafioPolling = setInterval(() => {
    const tab = document.getElementById('tabDesafio');
    if (tab && tab.classList.contains('active')) carregarDesafio();
  }, 30000);
}

init().then(function() { startRelatorioPolling(); carregarRelatorio(); startDesafioPolling(); }).catch(showFatalInitError);
