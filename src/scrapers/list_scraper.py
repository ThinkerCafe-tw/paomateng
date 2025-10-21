"""
List scraper for TRA announcement list pages
"""

from typing import List
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup
from loguru import logger

from src.utils.http_client import HTTPClient
from src.models.announcement import AnnouncementListItem


class ListScraper:
    """
    Scraper for TRA announcement list pages
    """

    def __init__(self, http_client: HTTPClient, base_url: str):
        """
        Initialize list scraper

        Args:
            http_client: HTTP client for making requests
            base_url: Base URL for TRA announcement list
        """
        self.http_client = http_client
        self.base_url = base_url

    def scrape_page(self, page_num: int) -> List[AnnouncementListItem]:
        """
        Scrape a single list page

        Args:
            page_num: Page number (starting from 0)

        Returns:
            List of announcement items found on the page
        """
        url = f"{self.base_url}/newsList?page={page_num}"
        logger.info(f"Scraping list page {page_num}: {url}")

        html = self.http_client.get_with_retry(url)
        if not html:
            logger.error(f"Failed to fetch list page {page_num}")
            return []

        try:
            soup = BeautifulSoup(html, "lxml")
            items = []

            # Find all announcement links
            # TRA list page typically has links to detail pages
            # Look for links that contain newsNo parameter
            links = soup.find_all("a", href=True)

            for link in links:
                href = link.get("href", "")

                # Check if this is a news detail link (contains newsNo parameter)
                if "newsNo=" in href:
                    try:
                        # Extract newsNo from URL
                        parsed_url = urlparse(href)
                        query_params = parse_qs(parsed_url.query)
                        news_no = query_params.get("newsNo", [None])[0]

                        if not news_no:
                            continue

                        # Get title from link text or nearby elements
                        title = link.get_text(strip=True)

                        # Find publish date (usually in same row or nearby element)
                        # This will depend on actual TRA HTML structure
                        publish_date = ""
                        parent = link.find_parent("tr") or link.find_parent("div")
                        if parent:
                            # Try to find date in various common formats
                            date_cells = parent.find_all(["td", "span", "div"])
                            for cell in date_cells:
                                text = cell.get_text(strip=True)
                                # Look for YYYY/MM/DD pattern
                                if "/" in text and len(text) >= 8:
                                    # Basic validation: should have 2 slashes
                                    if text.count("/") == 2:
                                        publish_date = text
                                        break

                        # Construct full detail URL
                        detail_url = urljoin(self.base_url, href)

                        # Create and validate AnnouncementListItem
                        item = AnnouncementListItem(
                            news_no=news_no,
                            title=title,
                            publish_date=publish_date,
                            detail_url=detail_url,
                        )
                        items.append(item)
                        logger.debug(f"Extracted: {news_no} - {title}")

                    except Exception as e:
                        logger.warning(f"Failed to parse announcement link: {e}")
                        continue

            logger.info(f"Found {len(items)} announcements on page {page_num}")
            return items

        except Exception as e:
            logger.error(f"Error parsing list page {page_num}: {e}")
            return []

    def scrape_all_pages(self) -> List[AnnouncementListItem]:
        """
        Scrape all list pages until no more data is found

        Returns:
            List of all announcement items from all pages
        """
        all_items = []
        page_num = 0

        logger.info("Starting historical scrape of all list pages")

        while True:
            items = self.scrape_page(page_num)

            if not items:
                logger.info(f"No items found on page {page_num}. Stopping pagination.")
                break

            all_items.extend(items)
            page_num += 1

            logger.info(f"Total announcements collected so far: {len(all_items)}")

        logger.info(f"Historical scrape complete. Total announcements: {len(all_items)}")
        return all_items
