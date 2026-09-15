"""Analytics and reporting queries."""
from src.analytics.queries import (
    get_top_deals,
    get_price_history,
    get_platform_comparison,
    get_category_trends,
    get_kpi_summary,
)

__all__ = [
    "get_top_deals",
    "get_price_history",
    "get_platform_comparison",
    "get_category_trends",
    "get_kpi_summary",
]
