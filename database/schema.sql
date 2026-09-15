-- PriceRadar Database Schema
-- PostgreSQL 15+

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Products table
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    brand TEXT,
    category TEXT,
    platform TEXT NOT NULL CHECK (platform IN ('amazon', 'flipkart')),
    url TEXT UNIQUE NOT NULL,
    image_url TEXT,
    product_id_on_platform TEXT,
    rating DECIMAL(3,2),
    review_count INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Price history table
CREATE TABLE IF NOT EXISTS price_history (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    price INTEGER NOT NULL,
    original_price INTEGER,
    discount_pct DECIMAL(5,2),
    in_stock BOOLEAN DEFAULT true,
    scraped_at TIMESTAMPTZ DEFAULT NOW()
);

-- Deal alerts table
CREATE TABLE IF NOT EXISTS deal_alerts (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    target_price INTEGER NOT NULL,
    email TEXT NOT NULL,
    triggered BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_products_platform ON products(platform);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_price_history_product ON price_history(product_id);
CREATE INDEX IF NOT EXISTS idx_price_history_scraped ON price_history(scraped_at);
CREATE INDEX IF NOT EXISTS idx_deal_alerts_product ON deal_alerts(product_id);

-- Materialized view for price summary statistics
CREATE MATERIALIZED VIEW IF NOT EXISTS price_summary AS
SELECT
    ph.product_id,
    MAX(ph.price) FILTER (WHERE ph.scraped_at >= NOW() - INTERVAL '1 day') as current_price,
    ROUND(AVG(ph.price) FILTER (WHERE ph.scraped_at >= NOW() - INTERVAL '7 days'))::INTEGER as avg_7d,
    ROUND(AVG(ph.price) FILTER (WHERE ph.scraped_at >= NOW() - INTERVAL '30 days'))::INTEGER as avg_30d,
    MIN(ph.price) FILTER (WHERE ph.scraped_at >= NOW() - INTERVAL '30 days') as min_30d,
    MAX(ph.price) FILTER (WHERE ph.scraped_at >= NOW() - INTERVAL '30 days') as max_30d,
    CASE
        WHEN MAX(ph.price) FILTER (WHERE ph.scraped_at >= NOW() - INTERVAL '30 days') > 0
        THEN ROUND(
            ((MAX(ph.price) FILTER (WHERE ph.scraped_at >= NOW() - INTERVAL '30 days') - 
              MAX(ph.price) FILTER (WHERE ph.scraped_at >= NOW() - INTERVAL '1 day')) * 100.0 /
             MAX(ph.price) FILTER (WHERE ph.scraped_at >= NOW() - INTERVAL '30 days')), 2)
        ELSE 0
    END as drop_from_max_pct,
    CASE
        WHEN MAX(ph.price) FILTER (WHERE ph.scraped_at >= NOW() - INTERVAL '30 days') > 
             ROUND(AVG(ph.price) FILTER (WHERE ph.scraped_at >= NOW() - INTERVAL '30 days')) * 1.2
        AND MAX(ph.price) FILTER (WHERE ph.scraped_at >= NOW() - INTERVAL '1 day') < 
            ROUND(AVG(ph.price) FILTER (WHERE ph.scraped_at >= NOW() - INTERVAL '30 days'))
        THEN true
        ELSE false
    END as is_deal
FROM price_history ph
GROUP BY ph.product_id;

-- Index on materialized view
CREATE INDEX IF NOT EXISTS idx_price_summary_product ON price_summary(product_id);
CREATE INDEX IF NOT EXISTS idx_price_summary_is_deal ON price_summary(is_deal);

-- Trigger to update updated_at on product changes
CREATE OR REPLACE FUNCTION update_product_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_product_updated_at ON products;
CREATE TRIGGER trigger_update_product_updated_at
BEFORE UPDATE ON products
FOR EACH ROW
EXECUTE FUNCTION update_product_updated_at();

-- Initial data verification (no inserts, just structure check)
-- These comments verify the schema is ready for data loading
-- Products will be scraped and inserted via the API
-- Price history will be populated during scraping cycles
-- Deal alerts will be created by users via the API
