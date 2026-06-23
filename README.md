# ShotSaaS - Plataforma de Análise de Apostas em Finalizações

SaaS de análise de apostas esportivas focado em jogadores que mais finalizam ao gol.
Calcula probabilidades de chutes no gol usando distribuição Poisson e identifica Value Bets com EV+.

## Funcionalidades

- **Jogadores do Dia**: Lista todos os prováveis titulares com estatísticas de finalização
- **Top Finalizadores**: Ranking dos jogadores com maior volume de chutes
- **Probabilidades**: Chance de 1+ e 2+ chutes no gol via modelo Poisson
- **Value Bets**: Compara odds do mercado com probabilidades calculadas para encontrar EV+
- **Consistência**: Score de regularidade baseado em coeficiente de variação
- **10 Ligas**: Premier League, La Liga, Serie A, Bundesliga, Ligue 1, Brasileirão, Argentina, MLS, Eredivisie, Primeira Liga
- **Atualização Automática**: Scheduler busca dados a cada 15min (jogos), 5min (odds), 30min (stats)

## Stack

| Componente | Tecnologia | Deploy |
|------------|-----------|--------|
| Frontend | Next.js 14 + Tailwind + Recharts | Vercel (Hobby) |
| Backend | FastAPI + SQLAlchemy Async | Render (Free) |
| Database | PostgreSQL | Supabase / Render |
| Cache | Redis | Upstash / Render |
| Tasks | APScheduler (in-process) | Mesmo do backend |

## APIs Externas Necessárias

### 1. API-Football (OBRIGATÓRIA para dados reais)

- **Site**: https://www.api-football.com/
- **Plano Grátis**: 100 requisições/dia
- **O que fornece**: Fixtures (jogos), estatísticas de jogadores, odds, lineups, lesões
- **Como obter**: Cadastre-se → Dashboard → "API Key"
- **Config**: Colocar em `backend/.env` como `API_FOOTBALL_KEY=seu_token`

> **Sem essa chave**, o sistema funciona mas retorna dados vazios. Use o seed de dados mockados para testar.

### 2. PostgreSQL (Produção)

- **Opção 1 — Render**: Cria automaticamente via `render.yaml` (free tier, 1GB)
- **Opção 2 — Supabase**: https://supabase.com — Plano grátis: 500MB, conexão SSL
  - Criar projeto → Copiar "Connection string" (modo URI)
  - Colocar em `DATABASE_URL` e `DATABASE_URL_SYNC`

### 3. Redis (Produção)

- **Opção 1 — Render**: Cria automaticamente via `render.yaml` (free tier, 30MB)
- **Opção 2 — Upstash**: https://upstash.com — Plano grátis: 10MB, conexão SSL
  - Criar database → Copiar "UPSTASH_REDIS_REST_URL"
  - Colocar em `REDIS_URL`

## Começar (Desenvolvimento Local)

### 1. Backend

```bash
cd backend
cp .env.example .env
# Edite .env com suas chaves (API-Football é opcional para testar)
pip install -r requirements.txt

# Opção A: Com PostgreSQL local rodando
uvicorn app.main:app --reload --port 8000

# Opção B: Só testar o modelo (sem banco)
python -m pytest tests/ -v
```

### 2. Popular dados mockados (recomendado para testar)

```bash
cd backend
python -m app.seed
# Isso cria: 5 ligas, 30 times, ~200 jogadores, partidas de hoje, stats de 10 jogos, odds
```

### 3. Frontend

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Acesse: http://localhost:3000

## Deploy Passo a Passo

### Render (Backend + Banco + Redis)

1. Crie conta em https://render.com
2. Conecte seu repositório GitHub
3. Use o blueprint (`render.yaml`) — Render detecta automaticamente:
   - Web Service: `shotsaas-api`
   - PostgreSQL: `shotsaas-db`
   - Redis: `shotsaas-redis`
4. Configure a env var `API_FOOTBALL_KEY` no painel do Render (Dashboard > Environment)
5. O deploy é automático

**Alternativa manual:**
1. Dashboard > Blueprint > Connect repo → seleciona `render.yaml`
2. Adiciona `API_FOOTBALL_KEY` como secret env var
3. Deploy

### Vercel (Frontend)

```bash
# Instalar CLI da Vercel
npm i -g vercel

# Deploy
cd frontend
vercel --prod

# Configurar env var:
vercel env add NEXT_PUBLIC_API_URL
# Cole: https://shotsaas-api.onrender.com
```

Ou conecte o repositório no https://vercel.com/new — o `vercel.json` já está configurado.

## Estrutura do Projeto

```
betano/
├── frontend/src/
│   ├── app/                  # Páginas (Dashboard, Players, Value Bets, Admin)
│   ├── components/           # UI (Navbar, PlayerCard, ValueBetCard)
│   └── lib/                  # API client, utils
├── backend/
│   └── app/
│       ├── api/              # Endpoints REST + WebSocket
│       ├── core/             # Config, banco, redis
│       ├── models/           # SQLAlchemy (9 tabelas)
│       ├── schemas/          # Pydantic validation
│       ├── services/         # Probability engine, value bet detector
│       └── tasks/            # Scheduler (APScheduler)
├── alembic/                  # Migrations
├── tests/                    # 40 testes unitários
├── vercel.json
└── render.yaml
```

## API Endpoints

| Endpoint | Descrição |
|----------|-----------|
| `GET /api/v1/players/today` | Jogadores em campo hoje com probabilidades |
| `GET /api/v1/players/top-shooters?limit=20` | Ranking de finalizadores |
| `GET /api/v1/players/{id}` | Detalhes do jogador + últimas partidas |
| `GET /api/v1/matches/today` | Jogos de hoje |
| `GET /api/v1/matches/{id}` | Detalhes da partida + escalações |
| `GET /api/v1/value-bets/shots?min_ev=0.05` | Value Bets em chutes |
| `GET /api/v1/value-bets/stats` | Estatísticas agregadas de value bets |
| `GET /api/v1/admin/dashboard` | Métricas do admin |
| `POST /api/v1/admin/refresh` | Forçar atualização de dados |
| `WS /ws/live` | Atualizações em tempo real |

## Modelo de Probabilidade

- **Distribuição Poisson** baseada na média histórica por 90 min
- Pesos: últimos 5 jogos (50%), jogos 6-10 (30%), baseline (20%)
- Consistência medida por coeficiente de variação (0-1, maior = mais regular)
- EV = (prob_modelo * odd) - 1, threshold mínimo de 5%
- Classificação: high (EV >= 20% E consistência >= 70%), medium, low

## Testes

```bash
cd backend
python -m pytest tests/ -v
# 40 testes — probability engine + value bet detection + data fetcher
```

## Seed Data

```bash
cd backend
python -m app.seed
# Popula: 5 ligas, 30 times, ~200 jogadores, partidas de hoje, histórico de 10 jogos por jogador, odds simuladas
```
