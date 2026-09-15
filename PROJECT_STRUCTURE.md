# PriceRadar Project Structure
This directory contains the complete PriceRadar production application.

## Quick Navigation

### Backend (Python/FastAPI)
- `src/scrapers/` - Web scraping modules for Amazon & Flipkart
- `src/pipeline/` - Data cleaning and database loading
- `src/models/` - Machine learning deal detection
- `src/analytics/` - Business intelligence queries
- `src/api/` - FastAPI REST endpoints
- `requirements.txt` - All Python dependencies

### Frontend (React)
- `frontend/` - Complete React 18 application
- `frontend/src/pages/` - Home, Product Detail, Search
- `frontend/src/components/` - Reusable widgets
- `frontend/src/api/` - Axios HTTP client

### Database
- `database/schema.sql` - PostgreSQL schema with tables & views
- All price history, products, and alerts stored here

### Testing & Deployment
- `tests/` - Pytest unit tests
- `Dockerfile` - Container image for API
- `docker-compose.yml` - Complete stack orchestration
- `.env.example` - Configuration template

### Documentation
- `README.md` - Full project documentation
- This file

## Key Features

✅ Scrapes 500+ products every 6 hours
✅ Machine learning deal detection
✅ Real-time REST API with caching
✅ Dark-themed React dashboard
✅ Production-ready with Docker
✅ Type hints & full test coverage
✅ Zero hardcoded values
✅ Complete error handling

## Dependencies

- **Backend**: FastAPI, SQLAlchemy, Playwright, scikit-learn, psycopg2
- **Frontend**: React 18, Vite, Recharts, Axios
- **Database**: PostgreSQL 15+
- **ML**: scikit-learn RandomForest, MLflow
- **Scheduling**: APScheduler
