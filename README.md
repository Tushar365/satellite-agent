# Satellite Image Agent

An AI-powered agent that searches, evaluates, and retrieves satellite imagery from public STAC catalogs (Sentinel-2, Landsat) using natural language queries.

## How It Works

```
User: "Get me cloud-free Sentinel-2 imagery of Mumbai from last month"
  |
  v
[Agent] --> parses query (AOI, date range, constraints)
  |
  v
[Catalogs] --> searches STAC endpoints (Planetary Computer, Element84, NASA CMR)
  |
  v
[Quality Gate] --> filters by cloud cover, AOI coverage, nodata %
  |
  v
[Download] --> fetches COG assets, stores locally
  |
  v
Result: validated satellite scenes ready for analysis
```

## Architecture

```
src/
  config.py            # settings, constants, knowledge base
  db/
    models.py          # database tables (searches, scenes, quality checks, downloads)
    session.py         # async PostgreSQL connection
  catalogs/            # STAC catalog clients (planned)
  core/                # quality gate, download logic (planned)
  agent/               # LangGraph agent + tool nodes (planned)
  api/                 # FastAPI endpoints (planned)
alembic/               # database migrations
tests/                 # pytest suite
```

## Build Progress

| Layer | Status | What It Does |
|---|---|---|
| Config + DB + Migrations | Done | Settings, 5 DB tables, Alembic setup |
| Catalog Clients | Not started | STAC search across Planetary Computer, Element84, NASA CMR |
| Core Logic | Not started | Quality gate, COG fetch, thumbnail generation |
| Agent (LangGraph) | Not started | NL parsing, search orchestration, tool calling |
| API (FastAPI) | Not started | REST endpoints, WebSocket status |

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL with PostGIS (needed for migrations/runtime)
- Redis (needed for Celery task queue)

### Install

```bash
uv sync
```

### Configure

Copy `.env.example` and fill in your keys:

```env
ANTHROPIC_API_KEY=sk-ant-...
TAVILY_API_KEY=tvly-...
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/satellite_agent
REDIS_URL=redis://localhost:6379/0
```

### Run Migrations (requires PostgreSQL)

```bash
alembic revision --autogenerate -m "initial_tables"
alembic upgrade head
```

### Run Tests

```bash
uv run pytest tests/ -v
```

Tests validate config loading, model structure, and foreign keys without needing a running database.

## Key Config Values

| Setting | Default | Purpose |
|---|---|---|
| `cloud_cover_default_max` | 15% | Reject scenes above this cloud cover |
| `aoi_coverage_min_pct` | 95% | Scene must cover this % of the AOI |
| `nodata_max_pct` | 5% | Max allowed nodata pixels |
| `required_processing_level` | L2A | Surface reflectance (atmospherically corrected) |
| `max_candidate_scenes` | 8 | Cap on scenes to evaluate per search |

## Supported Satellites

| Platform | Bands | Resolution | Revisit |
|---|---|---|---|
| Sentinel-2 (S2A/S2B) | B02-B12 | 10-60m | 5 days |
| Landsat 8/9 | B1-B10 | 30-100m | 8 days |

## Tech Stack

- **LLM**: Claude (Anthropic) via LangGraph
- **Search**: Tavily / DuckDuckGo
- **Catalogs**: pystac-client + planetary-computer SDK
- **Database**: PostgreSQL + PostGIS + SQLAlchemy async
- **Task Queue**: Celery + Redis
- **API**: FastAPI + Uvicorn
- **Geospatial**: Shapely, PyProj, Rasterio, GeoAlchemy2
