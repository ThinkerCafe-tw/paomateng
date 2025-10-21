"""
Web scraping components for TRA announcements
"""

from .list_scraper import ListScraper
from .detail_scraper import DetailScraper

__all__ = [
    "ListScraper",
    "DetailScraper",
]
