# PriceRadar — Real-Time E-Commerce Price Intelligence Platform

PriceRadar is a full-stack price intelligence platform that collects product and pricing data from Amazon India and Flipkart, stores price history in PostgreSQL, analyzes pricing trends, and uses machine learning to identify potential deals.

The project combines web scraping, data engineering, analytics, machine learning, REST APIs, and a React dashboard into a single end-to-end application.

## Features

- Multi-platform price tracking — Collects product data from Amazon India and Flipkart
- Price history — Stores historical prices for tracking price movements
- Price analytics — Calculates minimum, maximum, average, volatility, and price-drop metrics
- ML-based deal detection — Uses a Random Forest classifier to identify potential deals
- Scheduled scraping — Automatically runs the scraping pipeline at configured intervals
- FastAPI backend — Provides REST APIs for products, deals, analytics, and price history
- React dashboard — Interactive interface for browsing products and pricing information
- Docker support — Runs the backend, frontend, and PostgreSQL database as a containerized stack

## Tech Stack

### Backend

- Python
- FastAPI
- Playwright
- PostgreSQL
- SQLAlchemy
- APScheduler

### Data and Machine Learning

- Pandas
- NumPy
- Scikit-learn
- Joblib

### Frontend

- React
- Vite
- Axios
- Recharts

### DevOps

- Docker
- Docker Compose
- Git / GitHub