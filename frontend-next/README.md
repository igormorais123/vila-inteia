# Vila Politica — Next.js dashboard (Onda 7)

Cliente-facing prod dashboard para Predição Política BR 2026.
Substitui `frontend/politica.html` em deploys clientes (multi-tenant SaaS).

## Setup

```bash
cd frontend-next
npm install
VILA_API_BASE=http://localhost:8123 npm run dev
# abre http://localhost:3001
```

## Deploy Vercel

```bash
vercel link
vercel env add VILA_API_BASE production
# cole: https://vila-inteia.onrender.com
vercel --prod
```

## Estrutura

```
app/
  layout.tsx       root layout
  page.tsx         home: presidência ranked
  globals.css      tailwind + dark theme
components/
  ProbBar.tsx      barra de probabilidade
lib/
  api.ts           wrapper para /api/v1/politica
next.config.ts     rewrite /api -> VILA_API_BASE
```

## TODO (próximas iterações)

- /governadores : grid 27 UFs com p_winner
- /senado       : ranking 4 candidatos
- /custom       : form para POST /predict
- /backtest     : selective sweep visualization
- shadcn/ui     : install card/tabs/dialog para UX completa
- auth          : NextAuth + magic link via vila_clients
- analytics     : track which clientes consomem mais
