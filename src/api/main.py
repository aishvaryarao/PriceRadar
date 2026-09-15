"""FastAPI application with full endpoints."""
import logging
import time
from datetime import datetime
from functools import lru_cache
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from src.api.schemas import (
    ProductOutSchema,
    ProductDetailOutSchema,
    DealOutSchema,
    AlertInSchema,
    AlertOutSchema,
    KPISummarySchema,
    HealthSchema,
)
from src.analytics.queries import (
    get_top_deals,
    get_price_history,
    get_category_trends,
    get_kpi_summary,
)
from src.pipeline.scheduler import PipelineScheduler
from src.models.deal_detector import DealDetector
from src.pipeline.loader import get_db_context

logger = logging.getLogger(__name__)

# Initialize app
app = FastAPI(
    title="PriceRadar API",
    description="Real-time price intelligence platform",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log incoming requests with timing."""

    async def dispatch(self, request: Request, call_next) -> Any:
        """Log request details."""
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time

        logger.info(
            f"{request.method} {request.url.path} - "
            f"{response.status_code} ({duration*1000:.0f}ms)"
        )

        return response


app.add_middleware(RequestLoggingMiddleware)

# Global state
pipeline_scheduler: Optional[PipelineScheduler] = None
deal_detector: Optional[DealDetector] = None
cache_expiry: dict[str, float] = {}
cached_responses: dict[str, Any] = {}
CACHE_TTL_SECONDS: int = 60


def invalidate_cache(keys: list[str]) -> None:
    """Invalidate specific cache keys."""
    for key in keys:
        cache_expiry.pop(key, None)
        cached_responses.pop(key, None)


def get_cached(key: str) -> Any:
    """Get cached response if fresh."""
    now = time.time()
    if key in cache_expiry and cache_expiry[key] > now:
        return cached_responses.get(key)
    return None


def set_cache(key: str, value: Any) -> None:
    """Set cache with TTL."""
    cached_responses[key] = value
    cache_expiry[key] = time.time() + CACHE_TTL_SECONDS


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize on startup."""
    global pipeline_scheduler, deal_detector

    logger.info("Starting PriceRadar API")

    # Initialize deal detector
    deal_detector = DealDetector()
    try:
        deal_detector.load()
    except Exception:
        logger.info("Model not found, training new model")
        deal_detector.train()

    # Start pipeline scheduler (don't run immediately to avoid asyncio conflicts)
    pipeline_scheduler = PipelineScheduler()
    pipeline_scheduler.start(run_immediately=False)

    logger.info("API startup complete")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Cleanup on shutdown."""
    global pipeline_scheduler

    if pipeline_scheduler:
        pipeline_scheduler.stop()

    logger.info("API shutdown complete")


@app.get("/health", response_model=HealthSchema)
async def health_check() -> HealthSchema:
    """Health check endpoint.

    Returns:
        Health status
    """
    return HealthSchema(status="ok", timestamp=datetime.utcnow())


@app.get("/products", response_model=list[ProductOutSchema])
async def list_products(
    category: Optional[str] = Query(None, description="Filter by category"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    limit: int = Query(50, ge=1, le=500, description="Limit results"),
) -> list[ProductOutSchema]:
    """List products with optional filters.

    Args:
        category: Optional category filter
        platform: Optional platform filter (amazon/flipkart)
        limit: Max results to return

    Returns:
        List of products
    """
    try:
        with get_db_context() as conn:
            query = "SELECT id, name, platform, category, current_price, rating, scraped_at FROM products WHERE 1=1"
            params = []

            if category:
                query += " AND category = ?"
                params.append(category)

            if platform:
                query += " AND platform = ?"
                params.append(platform)

            query += " LIMIT ?"
            params.append(int(limit))

            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            cursor.close()

            # Placeholder images by category
            placeholder_images = {
                'smartphones': 'https://via.placeholder.com/300x300?text=Smartphone',
                'laptops': 'https://via.placeholder.com/300x300?text=Laptop',
                'headphones': 'https://via.placeholder.com/300x300?text=Headphones',
                'skincare': 'https://via.placeholder.com/300x300?text=Skincare',
                'protein': 'https://via.placeholder.com/300x300?text=Protein',
            }
            default_image = 'https://via.placeholder.com/300x300?text=Product'

            # Convert to response objects
            result = []
            for row in rows:
                category_val = row[3] if row[3] else 'unknown'
                platform_val = row[2] if row[2] else 'amazon'
                image_url = placeholder_images.get(category_val, default_image)
                
                # Generate product URL
                base_url = f"https://{platform_val.lower()}.com/s?k="
                product_url = f"{base_url}{row[1].replace(' ', '+')}"
                
                result.append(
                    ProductOutSchema(
                        id=row[0],
                        name=row[1],
                        brand=None,
                        category=category_val,
                        platform=platform_val,
                        url=product_url,
                        image_url=image_url,
                        rating=row[5],
                        current_price=int(row[4]),
                        original_price=None,
                        discount_pct=None,
                        deal_label=None,
                        deal_confidence=None,
                    )
                )

            return result

    except Exception as e:
        logger.error(f"Error listing products: {e}")
        raise HTTPException(status_code=500, detail="Database error")


@app.get("/products/{product_id}", response_model=ProductOutSchema)
async def get_product(product_id: int) -> ProductOutSchema:
    """Get single product by ID.

    Args:
        product_id: Product ID

    Returns:
        Product details
    """
    try:
        with get_db_context() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, platform, category, current_price, rating, scraped_at FROM products WHERE id = ?", (product_id,))
            row = cursor.fetchone()
            cursor.close()

            if not row:
                raise HTTPException(status_code=404, detail="Product not found")

            # Placeholder images by category
            placeholder_images = {
                'smartphones': 'https://via.placeholder.com/300x300?text=Smartphone',
                'laptops': 'https://via.placeholder.com/300x300?text=Laptop',
                'headphones': 'https://via.placeholder.com/300x300?text=Headphones',
                'skincare': 'https://via.placeholder.com/300x300?text=Skincare',
                'protein': 'https://via.placeholder.com/300x300?text=Protein',
            }
            default_image = 'https://via.placeholder.com/300x300?text=Product'
            
            category_val = row[3] if row[3] else 'unknown'
            platform_val = row[2] if row[2] else 'amazon'
            image_url = placeholder_images.get(category_val, default_image)
            
            # Generate product URL
            base_url = f"https://{platform_val.lower()}.com/s?k="
            product_url = f"{base_url}{row[1].replace(' ', '+')}"

            return ProductOutSchema(
                id=row[0],
                name=row[1],
                brand=None,
                category=category_val,
                platform=platform_val,
                url=product_url,
                image_url=image_url,
                rating=row[5],
                current_price=int(row[4]),
                original_price=None,
                discount_pct=None,
                deal_label=None,
                deal_confidence=None,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting product: {e}")
        raise HTTPException(status_code=500, detail="Database error")


@app.get("/products/{product_id}/history", response_model=list[dict[str, Any]])
async def get_product_history(
    product_id: int,
    days: int = Query(30, ge=1, le=365, description="Number of days to retrieve"),
) -> list[dict[str, Any]]:
    """Get price history for product.

    Args:
        product_id: Product ID
        days: Number of days to retrieve

    Returns:
        List of price history points
    """
    try:
        df = get_price_history(product_id, days)

        if df.empty:
            return []

        return df.to_dict(orient="records")

    except Exception as e:
        logger.error(f"Error getting history: {e}")
        raise HTTPException(status_code=500, detail="Database error")


@app.get("/deals", response_model=list[DealOutSchema])
async def list_deals(
    category: Optional[str] = Query(None, description="Filter by category"),
    min_drop: float = Query(10, ge=0, le=100, description="Minimum discount %"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
) -> list[DealOutSchema]:
    """List current deals.

    Args:
        category: Optional category filter
        min_drop: Minimum drop percentage
        limit: Max results

    Returns:
        List of deals
    """
    cache_key = f"deals:{category}:{min_drop}:{limit}"
    cached = get_cached(cache_key)
    if cached:
        return cached

    try:
        df = get_top_deals(limit, category)

        if df.empty:
            return []

        # Filter by min_drop
        df = df[df["drop_from_max_pct"] >= min_drop]

        # Convert to response
        deals = []
        for _, row in df.iterrows():
            deal = DealOutSchema(
                id=row["id"],
                name=row["name"],
                platform=row["platform"],
                current_price=row["current_price"],
                max_30d=row["max_30d"],
                drop_pct=row["drop_from_max_pct"],
                url=row["url"],
                image_url=row["image_url"],
                reason=f"Price dropped {row['drop_from_max_pct']:.1f}%",
            )
            deals.append(deal)

        set_cache(cache_key, deals)
        return deals

    except Exception as e:
        logger.error(f"Error listing deals: {e}")
        raise HTTPException(status_code=500, detail="Database error")


@app.get("/search", response_model=list[ProductOutSchema])
async def search_products(
    q: str = Query(..., min_length=1, description="Search query"),
    platform: Optional[str] = Query(None, description="Platform filter"),
) -> list[ProductOutSchema]:
    """Search products by name.

    Args:
        q: Search query
        platform: Optional platform filter

    Returns:
        Matching products
    """
    try:
        with get_db_context() as conn:
            # SQLite doesn't support ILIKE, use LIKE with case-insensitive matching
            query = "SELECT id, name, platform, category, current_price, rating, scraped_at FROM products WHERE LOWER(name) LIKE LOWER(?)"
            params = [f"%{q}%"]

            if platform:
                query += " AND platform = ?"
                params.append(platform)

            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            cursor.close()

            # Placeholder images by category
            placeholder_images = {
                'smartphones': 'https://via.placeholder.com/300x300?text=Smartphone',
                'laptops': 'https://via.placeholder.com/300x300?text=Laptop',
                'headphones': 'https://via.placeholder.com/300x300?text=Headphones',
                'skincare': 'https://via.placeholder.com/300x300?text=Skincare',
                'protein': 'https://via.placeholder.com/300x300?text=Protein',
            }
            default_image = 'https://via.placeholder.com/300x300?text=Product'

            result = []
            for row in rows:
                category_val = row[3] if row[3] else 'unknown'
                platform_val = row[2] if row[2] else 'amazon'
                image_url = placeholder_images.get(category_val, default_image)
                
                # Generate product URL
                base_url = f"https://{platform_val.lower()}.com/s?k="
                product_url = f"{base_url}{row[1].replace(' ', '+')}"
                
                result.append(
                    ProductOutSchema(
                        id=row[0],
                        name=row[1],
                        brand=None,
                        category=category_val,
                        platform=platform_val,
                        url=product_url,
                        image_url=image_url,
                        rating=row[5],
                        current_price=int(row[4]),
                        original_price=None,
                        discount_pct=None,
                        deal_label=None,
                        deal_confidence=None,
                    )
                )

            return result

    except Exception as e:
        logger.error(f"Error searching products: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Database error")


@app.get("/analytics/kpis", response_model=KPISummarySchema)
async def get_kpis() -> KPISummarySchema:
    """Get KPI summary.

    Returns:
        KPI metrics
    """
    cache_key = "kpis"
    cached = get_cached(cache_key)
    if cached:
        return cached

    try:
        summary = get_kpi_summary()
        result = KPISummarySchema(**summary)
        set_cache(cache_key, result)
        return result

    except Exception as e:
        logger.error(f"Error getting KPIs: {e}")
        raise HTTPException(status_code=500, detail="Database error")


@app.get("/analytics/categories")
async def get_category_stats() -> list[dict[str, Any]]:
    """Get category trends.

    Returns:
        Category statistics
    """
    try:
        df = get_category_trends()

        if df.empty:
            return []

        return df.to_dict(orient="records")

    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise HTTPException(status_code=500, detail="Database error")


@app.post("/alerts", response_model=AlertOutSchema)
async def create_alert(alert: AlertInSchema) -> AlertOutSchema:
    """Create price alert.

    Args:
        alert: Alert details

    Returns:
        Created alert
    """
    try:
        with get_db_context() as conn:
            cursor = conn.cursor()

            # Check product exists
            cursor.execute("SELECT id FROM products WHERE id = %s", (alert.product_id,))
            if not cursor.fetchone():
                cursor.close()
                raise HTTPException(status_code=404, detail="Product not found")

            # Insert alert
            cursor.execute(
                """
                INSERT INTO deal_alerts (product_id, target_price, email)
                VALUES (%s, %s, %s)
                RETURNING id, created_at
                """,
                (alert.product_id, alert.target_price, alert.email),
            )

            result = cursor.fetchone()
            alert_id, created_at = result[0], result[1]
            cursor.close()

            return AlertOutSchema(
                id=alert_id,
                product_id=alert.product_id,
                target_price=alert.target_price,
                email=alert.email,
                triggered=False,
                created_at=created_at,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        raise HTTPException(status_code=500, detail="Database error")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
