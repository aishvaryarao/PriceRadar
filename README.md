PriceRadar — Real-Time E-Commerce Price Intelligence Platform

PriceRadar is a full-stack price intelligence platform that collects product and pricing data from Amazon India and Flipkart, stores price history in PostgreSQL, analyzes pricing trends, and uses machine learning to identify potential deals.


Features

1. Multi-platform price tracking using Amazon India and Flipkart

2. Historical price tracking using PostgreSQL

3. Price analytics including averages, volatility, and price drops

4. Random Forest-based deal detection

5. Automated scraping with APScheduler

6. FastAPI REST backend

7. React dashboard with price visualizations

8. Dockerized application stack
   

Architecture

                    ┌─────────────────┐
                    │  Amazon India   │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │    Flipkart     │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   Playwright    │
                    │    Scrapers     │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Data Cleaning & │
                    │  Normalization  │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   PostgreSQL    │
                    │                 │
                    │ Products        │
                    │ Price History   │
                    │ Deal Alerts     │
                    └────────┬────────┘
                             │
                  ┌──────────┴──────────┐
                  ▼                     ▼
          ┌───────────────┐     ┌────────────────┐
          │    Price      │     │   ML Deal      │
          │   Analytics   │     │   Detector     │
          └───────┬───────┘     └───────┬────────┘
                  │                      │
                  └──────────┬───────────┘
                             ▼
                    ┌─────────────────┐
                    │     FastAPI     │
                    │    REST API     │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  React + Vite   │
                    │    Dashboard    │
                    └─────────────────┘
                    

Tech Stack

Backend: Python, FastAPI, Playwright, SQLAlchemy, APScheduler

Database: PostgreSQL

Data & ML: Pandas, NumPy, Scikit-learn, Joblib

Frontend: React, Vite, Axios, Recharts

DevOps: Docker, Docker Compose, Git, GitHub

Machine Learning

PriceRadar uses a Random Forest classifier for potential deal detection.

The model uses:

Price drop from historical maximum

Current price vs. 7-day average

Current price vs. 30-day average

Price volatility

The current model is trained on synthetic data and is intended as a project-level demonstration of the deal detection pipeline.


Project Structure

```text
┌───────────────────────────────────────────────────────────┐
│                       PriceRadar                          │
├───────────────────────┬───────────────────────────────────┤
│ database/             │ frontend/                         │
│ └── schema.sql        │ ├── src/                          │
│                       │ │   ├── api/                      │
│ models/               │ │   ├── components/               │
│ └── deal_detector     │ │   └── pages/                    │ 
│     .joblib           │ ├── package.json                  │
│                       │ └── vite.config.js                │
├───────────────────────┼───────────────────────────────────┤
│ src/                  │ tests/                            │
│ ├── analytics/        │                                   │
│ ├── api/              │                                   │
│ ├── database/         │                                   │
│ ├── models/           │                                   │
│ ├── pipeline/         │                                   │
│ └── scrapers/         │                                   │
├───────────────────────┴───────────────────────────────────┤
│ Dockerfile  │  docker-compose.yml  │  requirements.txt    │
│ README.md                                                 │
└───────────────────────────────────────────────────────────┘
```


Running the Project

Prerequisites

1. Docker Desktop

2. Git

Setup

git clone https://github.com/aishvaryarao/PriceRadar.git
cd PriceRadar

Create .env using .env.example, then run:

docker compose up --build

Application

Frontend: http://localhost:3000

Backend: http://localhost:8000

API Docs: http://localhost:8000/docs

To stop the application:

docker compose down

Testing

pytest


Project Objective

PriceRadar demonstrates an end-to-end data-driven application combining:

Web scraping

Data engineering

Database management

Data analytics

Machine learning

REST APIs

Frontend development

Docker
