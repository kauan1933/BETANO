# ShotSaaS - Sports Betting Analysis Platform

## Stack
- **Frontend**: Next.js 14 (App Router) + Tailwind CSS + Recharts
- **Backend**: FastAPI + SQLAlchemy Async + APScheduler
- **Database**: PostgreSQL (SQLAlchemy async models)
- **Cache**: Redis
- **Data Source**: API-Football (api-football.com)

## Project Structure
```
betano/
├── frontend/          # Next.js application
│   └── src/
│       ├── app/       # App Router pages
│       ├── components/ # Shared UI components
│       └── lib/       # API client, utilities
├── backend/
│   └── app/
│       ├── api/       # FastAPI route handlers
│       ├── core/      # Config, DB, Redis
│       ├── models/    # SQLAlchemy models
│       ├── schemas/   # Pydantic schemas
│       ├── services/  # Business logic
│       └── tasks/     # Background scheduler tasks
├── vercel.json
└── .gitignore
```

## Key Endpoints
- `GET /api/v1/players/today` - Players playing today
- `GET /api/v1/players/top-shooters` - Top shooters ranking
- `GET /api/v1/players/{id}` - Player detail
- `GET /api/v1/matches/today` - Today's matches
- `GET /api/v1/value-bets/shots` - EV+ shot market bets
- `POST /api/v1/admin/refresh` - Force data refresh
- `WS /ws/live` - Real-time updates

## Probability Model
- Poisson distribution based on per-90 min historical rates
- Recency weighting: Last 5 games (50%), games 6-10 (30%), baseline (20%)
- Consistency measured via coefficient of variation (lower = better)
- Value bet: EV = (model_prob * odds - 1) - (1 - model_prob), threshold ≥ 5%

## Data Flow
1. Scheduler fetches fixtures daily for 10 major leagues
2. Player stats from last 10 games are collected
3. Probability engine computes shot/SOT probabilities
4. Odds fetcher scrapes bookmaker markets
5. Value bet detector compares model vs market, flags EV+ opportunities
