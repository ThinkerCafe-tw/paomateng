"""
Detail scraper for TRA announcement detail pages
"""

from typing import Tuple, Optional
from bs4 import BeautifulSoup
from loguru import logger

from src.utils.http_client import HTTPClient
from src.utils.hash_utils import compute_hash


class DetailScraper:
    """
    Scraper for TRA announcement detail pages
    """

    def __init__(self, http_client: HTTPClient):
        """
        Initialize detail scraper

        Args:
            http_client: HTTP client for making requests
        """
        self.http_client = http_client

    def scrape_detail(self, detail_url: str) -> Optional[Tuple[str, str]]:
        """
        Scrape announcement detail page and compute content hash

        Args:
            detail_url: URL of the detail page

        Returns:
            Tuple of (content_html, content_hash) if successful, None if failed

        Examples:
            >>> scraper.scrape_detail("https://...")
            ("<div>...</div>", "md5:a1b2c3...")
        """
        logger.debug(f"Fetching detail page: {detail_url}")

        html = self.http_client.get_with_retry(detail_url)
        if not html:
            logger.error(f"Failed to fetch detail page: {detail_url}")
            return None

        try:
            soup = BeautifulSoup(html, "lxml")

            # Extract main content
            # TRA typically uses specific div classes for content
            # Common patterns: class="content", class="newsContent", id="content"
            content = None

            # Try multiple selectors to find the main content
            selectors = [
                {"class": "newsContent"},
                {"class": "content"},
                {"id": "content"},
                {"class": "main-content"},
                {"class": "news-detail"},
            ]

            for selector in selectors:
                content_div = soup.find("div", selector)
                if content_div:
                    content = str(content_div)
                    logger.debug(f"Found content using selector: {selector}")
                    break

            # If no specific content div found, try to find the main article/content area
            if not content:
                # Look for article tag
                article = soup.find("article")
                if article:
                    content = str(article)
                else:
                    # Fall back to finding the largest div with text content
                    all_divs = soup.find_all("div")
                    if all_divs:
                        # Find div with most text content
                        largest_div = max(all_divs, key=lambda d: len(d.get_text(strip=True)))
                        content = str(largest_div)
                        logger.warning(f"Using largest div as content for {detail_url}")

            if not content:
                logger.warning(f"Could not extract specific content div, using full HTML for {detail_url}")
                content = html

            # Compute hash of the content
            content_hash = compute_hash(content)

            logger.debug(f"Successfully extracted content from {detail_url} (hash: {content_hash})")
            return (content, content_hash)

        except Exception as e:
            logger.error(f"Error parsing detail page {detail_url}: {e}")
            # If parsing fails, return the raw HTML with hash
            # This ensures we don't lose data even if structure changes
            try:
                content_hash = compute_hash(html)
                logger.warning(f"Falling back to raw HTML for {detail_url}")
                return (html, content_hash)
            except Exception as hash_error:
                logger.error(f"Failed to compute hash for {detail_url}: {hash_error}")
                return None
