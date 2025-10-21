"""
Historical scrape orchestrator for initial data collection
"""

from datetime import datetime
from zoneinfo import ZoneInfo
from loguru import logger

from src.utils.http_client import HTTPClient
from src.utils.text_utils import html_to_text
from src.scrapers.list_scraper import ListScraper
from src.scrapers.detail_scraper import DetailScraper
from src.parsers.content_parser import ContentParser
from src.classifiers.announcement_classifier import AnnouncementClassifier
from src.storage.json_storage import JSONStorage
from src.models.announcement import Announcement, VersionEntry


def run_historical_scrape(config: dict) -> None:
    """
    Run historical scrape of all TRA announcements

    Args:
        config: Configuration dictionary from settings.yaml
    """
    logger.info("=" * 80)
    logger.info("Starting Historical Scrape")
    logger.info("=" * 80)

    # Initialize components
    http_client = HTTPClient(
        user_agent=config["scraper"]["user_agent"],
        timeout=config["scraper"]["request_timeout"],
        retry_attempts=config["scraper"]["retry_attempts"],
        rate_limit_delay=config["scraper"]["rate_limit_delay"],
    )

    list_scraper = ListScraper(http_client, config["scraper"]["base_url"])
    detail_scraper = DetailScraper(http_client)
    content_parser = ContentParser()
    classifier = AnnouncementClassifier()
    storage = JSONStorage(
        output_file=config["storage"]["output_file"],
        backup_dir=config["storage"]["backup_dir"],
        pretty_print=config["storage"]["pretty_print"],
    )

    try:
        # Step 1: Scrape all list pages
        logger.info("Step 1: Scraping all list pages...")
        list_items = list_scraper.scrape_all_pages()
        logger.info(f"Found {len(list_items)} total announcements")

        if not list_items:
            logger.warning("No announcements found. Exiting.")
            return

        # Step 2: Process each announcement
        logger.info("Step 2: Processing announcements...")
        announcements = []
        processed_count = 0

        for idx, item in enumerate(list_items, 1):
            try:
                # Log progress every 10 announcements
                if idx % 10 == 0:
                    logger.info(f"Progress: {idx}/{len(list_items)} ({idx/len(list_items)*100:.1f}%)")

                # Scrape detail page
                detail_result = detail_scraper.scrape_detail(item.detail_url)
                if not detail_result:
                    logger.warning(f"Failed to scrape detail for {item.news_no}, skipping")
                    continue

                content_html, content_hash = detail_result

                # Parse content for structured data (pass publish_date and title for accurate time parsing)
                extracted_data = content_parser.parse(content_html, item.publish_date, item.title)

                # Classify announcement
                classification = classifier.classify(item.title, content_html)

                # Update classification with publish_date for event_group_id
                classification.event_group_id = classifier.extract_event_group_id(
                    item.title, item.publish_date
                )

                # Create version entry
                version_entry = VersionEntry(
                    scraped_at=datetime.now(ZoneInfo("Asia/Taipei")),
                    content_html=content_html,
                    content_text=html_to_text(content_html),
                    content_hash=content_hash,
                    extracted_data=extracted_data,
                )

                # Create announcement
                announcement = Announcement(
                    id=item.news_no,
                    title=item.title,
                    publish_date=item.publish_date,
                    detail_url=item.detail_url,
                    classification=classification,
                    version_history=[version_entry],
                )

                announcements.append(announcement)
                processed_count += 1

            except Exception as e:
                logger.error(f"Error processing announcement {item.news_no}: {e}")
                continue

        # Step 3: Save all data
        logger.info(f"Step 3: Saving {len(announcements)} announcements to storage...")
        storage.save(announcements)

        logger.info("=" * 80)
        logger.info(f"Historical Scrape Complete!")
        logger.info(f"Total announcements found: {len(list_items)}")
        logger.info(f"Successfully processed: {processed_count}")
        logger.info(f"Saved to: {config['storage']['output_file']}")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"Historical scrape failed: {e}")
        raise
    finally:
        http_client.close()
